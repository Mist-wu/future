#!/usr/bin/env python3
"""市场预测：统计基线、AI 调整、到期结算。只读行情，没有任何下单功能。

用法：
  market.py forecast BTCUSDT ETHUSDT       出统计预测和朴素基线，并记账
  market.py adjust FID --drift -1.5 --vol 1.2 --note "理由" [--mode single|ensemble]
                                           记下 AI 调整后的分布
  market.py open                           未到期的预测
  market.py settle                         到期的预测按目标时刻的价格结算

模型：
  统计预测（stat）  日对数收益率先过一个固定参数的 GARCH(1,1) 滤波，得到标准化残差；
                    再从残差里重新抽样，按当前波动率模拟未来路径。
  朴素基线（baseline） 波动取历史平均的对数正态分布。
  AI 调整（ai）     对统计分布做两个动作：中枢平移 drift（百分比），离散程度乘 vol。

  统计预测和朴素基线都让期望价格等于现价，不带方向观点。
  对数收益率的中枢因此略低于零，波动越大低得越多。

模型版本（记录里的 model 字段，没有这个字段的是 v1）：
  v1  对数收益率的中枢为零。波动大时期望价格会高于现价，SOXL 的 30 天预测偏高约 20%。
  v2  期望价格等于现价。自 2026-11-13 起使用。

每条记录都存一个 199 档的对数收益率分位数网格（0.5% 到 99.5%），
五档价格和阈值概率都从网格算出，打分也用网格。
"""
from __future__ import annotations

import argparse
import math
import random
import statistics
import sys
from datetime import timedelta

from common import append_jsonl, config, http_json, iso, local, now, parse_iso, read_jsonl

LEVELS = [round(0.005 * i, 3) for i in range(1, 200)]  # 0.005 … 0.995
SHOW = [0.05, 0.25, 0.5, 0.75, 0.95]
ALPHA, BETA = 0.06, 0.92  # GARCH(1,1) 的固定参数，不做拟合
MODEL = "v2"
SOURCE_ZH = {"stat": "统计预测", "baseline": "朴素基线", "ai": "AI 调整"}

SPOT = "https://api.binance.com/api/v3"
FUT = "https://fapi.binance.com/fapi/v1"


# ---------- 行情 ----------

def base(venue: str) -> str:
    return SPOT if venue == "spot" else FUT


def spot_price(symbol: str, venue: str) -> float:
    return float(http_json(f"{base(venue)}/ticker/price", {"symbol": symbol})["price"])


def daily_closes(symbol: str, sym_cfg: dict) -> list[float]:
    """已收盘的日线收盘价，从旧到新。"""
    hist = sym_cfg.get("history", "")
    if hist.startswith("yahoo:"):
        ticker = hist.split(":", 1)[1]
        data = http_json(f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}",
                         {"range": "5y", "interval": "1d"})
        res = data["chart"]["result"][0]
        closes = res["indicators"]["adjclose"][0]["adjclose"]
        stamps = res["timestamp"]
        # 每根日线的时间戳是开盘时刻，开盘后 7 小时内这根还没走完，去掉
        if stamps and now().timestamp() < stamps[-1] + 7 * 3600:
            closes = closes[:-1]
        return [c for c in closes if c]
    rows = http_json(f"{base(sym_cfg['venue'])}/klines", {"symbol": symbol, "interval": "1d", "limit": 1000})
    now_ms = now().timestamp() * 1000
    return [float(r[4]) for r in rows if r[6] < now_ms]  # r[6] 是收盘时间，去掉没走完的今天


def price_at(symbol: str, venue: str, ts_ms: int) -> float | None:
    rows = http_json(f"{base(venue)}/klines", {"symbol": symbol, "interval": "1m", "startTime": ts_ms, "limit": 1})
    if not rows or rows[0][0] - ts_ms > 3600_000:  # 一小时内没有成交就当取不到
        return None
    return float(rows[0][1])


# ---------- 模型 ----------

def simulate(returns: list[float], checkpoints: list[int], paths: int, seed: str) -> dict[int, list[float]]:
    """返回 {步数: 排好序的累计对数收益率}。"""
    var_long = statistics.pvariance(returns)
    omega = (1 - ALPHA - BETA) * var_long
    var = var_long
    z = []
    for r in returns:
        z.append(r / math.sqrt(var))
        var = omega + ALPHA * r * r + BETA * var
    mean_z = statistics.fmean(z)
    sd_z = statistics.pstdev(z)
    z = [(x - mean_z) / sd_z for x in z]  # 零漂移、单位方差

    rng = random.Random(seed)
    n, steps = len(z), max(checkpoints)
    marks = set(checkpoints)
    out: dict[int, list[float]] = {c: [] for c in checkpoints}
    for _ in range(paths):
        v, total = var, 0.0
        for step in range(1, steps + 1):
            r = math.sqrt(v) * z[int(rng.random() * n)]
            total += r
            v = omega + ALPHA * r * r + BETA * v
            if step in marks:
                out[step].append(total)
    for c in checkpoints:
        # 整体平移，使期望价格等于现价：E[exp(R)] = 1
        shift = math.log(statistics.fmean(math.exp(x) for x in out[c]))
        out[c] = sorted(x - shift for x in out[c])
    return out


def grid_from_samples(sorted_samples: list[float]) -> list[float]:
    n = len(sorted_samples)
    return [round(sorted_samples[min(n - 1, int(q * n))], 5) for q in LEVELS]


def grid_normal(sigma: float) -> list[float]:
    nd = statistics.NormalDist(-sigma * sigma / 2, sigma)  # 均值取 -σ²/2，期望价格等于现价
    return [round(nd.inv_cdf(q), 5) for q in LEVELS]


def quantile(grid: list[float], q: float) -> float:
    return grid[LEVELS.index(round(q, 3))]


def cdf(grid: list[float], x: float) -> float:
    """P(对数收益率 ≤ x)，在网格上线性插值。网格之外只能说小于 0.5% 或大于 99.5%。"""
    if x <= grid[0]:
        return 0.0025
    if x >= grid[-1]:
        return 0.9975
    for i in range(1, len(grid)):
        if x <= grid[i]:
            lo, hi = grid[i - 1], grid[i]
            w = 0.5 if hi == lo else (x - lo) / (hi - lo)
            return LEVELS[i - 1] + w * (LEVELS[i] - LEVELS[i - 1])
    return 0.9975


def threshold_probs(grid: list[float], thresholds: list[float]) -> dict[str, float]:
    """阈值按期末涨跌幅算：负数是“跌幅达到或超过”，正数是“涨幅达到或超过”。"""
    out = {}
    for t in thresholds:
        x = math.log(1 + t / 100)
        p = cdf(grid, x) if t < 0 else 1 - cdf(grid, x)
        out[f"{t:+g}%"] = round(p, 4)
    return out


def summary(grid: list[float], p0: float, thresholds: list[float]) -> tuple[dict, dict]:
    quantiles = {f"{int(q * 100)}": round(p0 * math.exp(quantile(grid, q)), 6) for q in SHOW}
    return quantiles, threshold_probs(grid, thresholds)


def fmt_price(x: float) -> str:
    return f"{x:,.0f}" if x >= 1000 else f"{x:,.2f}"


def print_record(rec: dict):
    q, pr = rec["quantiles"], rec["probs"]
    qs = "  ".join(f"{k}%:{fmt_price(v):>9}" for k, v in q.items())
    ps = "  ".join(f"{k} {v * 100:.0f}%" for k, v in pr.items())
    print(f"  {SOURCE_ZH[rec['source']]:<5} {qs}")
    print(f"        期末涨跌幅概率  {ps}")


# ---------- 命令 ----------

def thresholds_for(cfg: dict, symbol: str, horizon: int) -> list[float]:
    own = cfg["symbols"][symbol].get("thresholds", {})
    return own.get(str(horizon)) or cfg["thresholds"].get(str(horizon), [])


def cmd_forecast(a):
    cfg = config()["market"]
    for symbol in a.symbols:
        sym_cfg = cfg["symbols"].get(symbol) or sys.exit(f"config.toml 里没有 {symbol}")
        closes = daily_closes(symbol, sym_cfg)
        returns = [math.log(b / c) for c, b in zip(closes, closes[1:])]
        t0 = now()
        p0 = spot_price(symbol, sym_cfg["venue"])
        spw = sym_cfg["steps_per_week"]
        steps = {h: max(1, round(h * spw / 7)) for h in cfg["horizons"]}
        sims = simulate(returns, sorted(set(steps.values())), cfg["paths"], f"{symbol}-{iso(t0)}")
        sigma_day = statistics.pstdev(returns)

        print(f"\n{symbol}  现价 {fmt_price(p0)}  （{local(t0)}，历史 {len(returns)} 个交易日）")
        for h in cfg["horizons"]:
            fid = f"m{t0.astimezone().strftime('%Y%m%dT%H%M')}-{symbol}-{h}d"  # 编号里的时间是本机时间
            target = t0 + timedelta(days=h)
            th = thresholds_for(cfg, symbol, h)
            common_fields = {"fid": fid, "symbol": symbol, "venue": sym_cfg["venue"], "horizon_days": h,
                             "t0": iso(t0), "p0": p0, "target": iso(target), "model": MODEL}
            print(f" {h} 天后（{local(target)} 结算）  编号 {fid}")
            for source, grid in (("stat", grid_from_samples(sims[steps[h]])),
                                 ("baseline", grid_normal(sigma_day * math.sqrt(steps[h])))):
                quantiles, probs = summary(grid, p0, th)
                rec = {**common_fields, "source": source, "quantiles": quantiles, "probs": probs, "grid": grid}
                append_jsonl("market_forecasts.jsonl", rec)
                print_record(rec)


def find_stat(fid: str) -> dict:
    for r in read_jsonl("market_forecasts.jsonl"):
        if r["fid"] == fid and r["source"] == "stat":
            return r
    sys.exit(f"没有这个预测编号：{fid}")


def cmd_adjust(a):
    stat = find_stat(a.fid)
    shift = math.log(1 + a.drift / 100)
    grid = [round(shift + a.vol * g, 5) for g in stat["grid"]]
    th = [float(k.rstrip("%")) for k in stat["probs"]]
    quantiles, probs = summary(grid, stat["p0"], th)
    rec = {k: stat[k] for k in ("fid", "symbol", "venue", "horizon_days", "t0", "p0", "target")}
    rec["model"] = stat.get("model", "v1")  # AI 调整建立在哪个版本的统计预测上
    rec.update({"source": "ai", "mode": a.mode, "drift_pct": a.drift, "vol_scale": a.vol, "note": a.note,
                "quantiles": quantiles, "probs": probs, "grid": grid})
    append_jsonl("market_forecasts.jsonl", rec)
    print(f"{a.fid}  中枢 {a.drift:+g}%，离散程度 ×{a.vol:g}")
    print_record(stat)
    print_record(rec)


def unsettled() -> list[dict]:
    done = {s["fid"] for s in read_jsonl("market_settlements.jsonl")}
    seen, out = set(), []
    for r in read_jsonl("market_forecasts.jsonl"):
        if r["fid"] not in done and r["fid"] not in seen and r["source"] == "stat":
            seen.add(r["fid"])
            out.append(r)
    return out


def cmd_open(_):
    rows = unsettled()
    if not rows:
        print("没有未到期的市场预测。")
        return
    print(f"未结算的市场预测 {len(rows)} 条：")
    for r in sorted(rows, key=lambda r: r["target"]):
        target = parse_iso(r["target"])
        left = (target - now()).total_seconds() / 86400
        when = f"还有 {left:.1f} 天" if left > 0 else "已到期，待结算"
        print(f"  {r['fid']}  起始价 {fmt_price(r['p0'])}  {local(target)} 结算（{when}）")


def cmd_settle(_):
    due = [r for r in unsettled() if parse_iso(r["target"]) <= now()]
    if not due:
        print("没有到期的市场预测。")
        return
    for r in due:
        price = price_at(r["symbol"], r["venue"], int(parse_iso(r["target"]).timestamp() * 1000))
        if price is None:
            print(f"取不到结算价：{r['fid']}")
            continue
        append_jsonl("market_settlements.jsonl", {"fid": r["fid"], "price": price, "target": r["target"]})
        change = (price / r["p0"] - 1) * 100
        print(f"已结算 {r['fid']}：{fmt_price(r['p0'])} → {fmt_price(price)}（{change:+.1f}%）")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("forecast")
    p.add_argument("symbols", nargs="+")
    p.set_defaults(fn=cmd_forecast)

    p = sub.add_parser("adjust")
    p.add_argument("fid")
    p.add_argument("--drift", type=float, default=0.0, help="中枢平移，百分比")
    p.add_argument("--vol", type=float, default=1.0, help="离散程度的倍数")
    p.add_argument("--note", required=True)
    p.add_argument("--mode", default="single", choices=["single", "ensemble"])
    p.set_defaults(fn=cmd_adjust)

    sub.add_parser("open").set_defaults(fn=cmd_open)
    sub.add_parser("settle").set_defaults(fn=cmd_settle)

    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
