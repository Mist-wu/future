#!/usr/bin/env python3
"""成绩单：事件题的 Brier 分数和校准情况，市场预测的分位数损失。

用法：
  score.py            全部
  score.py events     只看事件题
  score.py market     只看市场预测
  score.py --public   只算公开账本，写公开简报时用

读法：
  Brier 分数越低越好。永远答 50% 得 0.25，全对得 0。
  分位数损失越低越好，单位是对数收益率的百分点，只在同一资产、同一周期内比较。
"""
from __future__ import annotations

import math
import statistics
import sys
from collections import defaultdict

import common
import ledger
from common import parse_iso, read_jsonl
from market import LEVELS, SOURCE_ZH as MARKET_ZH, quantile

MIN_N = 30  # 少于这个数，分数只能当参考


def note_n(n: int) -> str:
    return "" if n >= MIN_N else f"（样本 {n}，不足 {MIN_N}，仅供参考）"


# ---------- 事件题 ----------

def time_weighted(rows: list[dict], end, y: int) -> float:
    """把每个概率持有的时长当权重。rows 已按时间排序。"""
    total = weight = 0.0
    for i, r in enumerate(rows):
        start = parse_iso(r["ts"])
        stop = parse_iso(rows[i + 1]["ts"]) if i + 1 < len(rows) else end
        w = max(0.0, (min(stop, end) - start).total_seconds())
        total += w * (r["p"] - y) ** 2
        weight += w
    return total / weight if weight > 0 else (rows[0]["p"] - y) ** 2


def events():
    qs, res = ledger.questions(), ledger.resolutions()
    by: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in ledger.forecasts():
        if r.get("p") is not None:
            by[(r["qid"], r["source"])].append(r)

    scored = {qid: r for qid, r in res.items() if r["outcome"] in ("yes", "no")}
    print("== 事件题 ==")
    print(f"题库 {len(qs)} 道：已结算 {len(scored)}，作废 {len(res) - len(scored)}，未结算 {len(qs) - len(res)}")
    if not scored:
        print("还没有已结算的题，暂无成绩。\n")
        return

    first: dict[str, dict[str, float]] = defaultdict(dict)  # source -> qid -> 首次预测的 Brier
    print(f"\n{'来源':<8}{'题数':>4}  {'首次 Brier':>10}  {'时间加权 Brier':>12}")
    for source in ledger.SOURCES:
        tw = []
        for qid, r in scored.items():
            rows = by.get((qid, source))
            if not rows:
                continue
            y = 1 if r["outcome"] == "yes" else 0
            first[source][qid] = (rows[0]["p"] - y) ** 2
            tw.append(time_weighted(rows, parse_iso(r["resolved_at"]), y))
        if tw:
            n = len(tw)
            print(f"{ledger.SOURCE_ZH[source]:<8}{n:>4}  {statistics.fmean(first[source].values()):>10.3f}  {statistics.fmean(tw):>12.3f}  {note_n(n)}")

    print("\n两两比较（只算双方都有预测的题，用首次 Brier；差值为负表示前者更准）：")
    for a, b in (("ai_blind", "market"), ("ai_informed", "market"), ("human_blind", "ai_blind"),
                 ("human_final", "human_blind"), ("human_final", "mech_avg"), ("mech_avg", "ai_blind")):
        common = sorted(set(first[a]) & set(first[b]))
        if not common:
            continue
        diff = statistics.fmean(first[a][q] - first[b][q] for q in common)
        wins = sum(first[a][q] < first[b][q] for q in common)
        print(f"  {ledger.SOURCE_ZH[a]} 对 {ledger.SOURCE_ZH[b]}：差值 {diff:+.3f}，{len(common)} 题里前者更准 {wins} 题 {note_n(len(common))}")

    print("\n校准（首次预测；“预测”和“实际”越接近越好）：")
    for source in ("ai_blind", "ai_informed", "human_blind", "human_final", "market"):
        bins: dict[int, list[tuple[float, int]]] = defaultdict(list)
        for qid, r in scored.items():
            rows = by.get((qid, source))
            if rows:
                p = rows[0]["p"]
                bins[min(9, int(p * 10))].append((p, 1 if r["outcome"] == "yes" else 0))
        if not bins:
            continue
        print(f"  {ledger.SOURCE_ZH[source]}")
        for b in sorted(bins):
            items = bins[b]
            mean_p = statistics.fmean(p for p, _ in items)
            freq = statistics.fmean(y for _, y in items)
            bar = "█" * round(freq * 20) + "░" * (20 - round(freq * 20))
            print(f"    {b * 10:>3}–{b * 10 + 10:<3}%  题数 {len(items):>3}  预测 {mean_p * 100:>3.0f}%  实际 {freq * 100:>3.0f}%  {bar}")
    print()


# ---------- 市场 ----------

def pinball(grid: list[float], y: float) -> float:
    """全网格的平均分位数损失，约等于 CRPS 的一半。"""
    return statistics.fmean((q - (1 if y < g else 0)) * (y - g) for q, g in zip(LEVELS, grid))


def market():
    settles = {s["fid"]: s["price"] for s in read_jsonl("market_settlements.jsonl")}
    recs = read_jsonl("market_forecasts.jsonl")
    fids = {r["fid"] for r in recs}
    print("== 市场预测 ==")
    print(f"预测 {len(fids)} 条：已结算 {len(fids & set(settles))}，未到期 {len(fids - set(settles))}")
    if not settles:
        print("还没有到期的预测，暂无成绩。\n")
        return

    loss: dict[tuple, dict[str, float]] = defaultdict(dict)   # (symbol, h, source) -> fid -> loss
    cover: dict[tuple, list[tuple[bool, bool]]] = defaultdict(list)
    brier: dict[tuple, list[float]] = defaultdict(list)
    for r in recs:
        if r["fid"] not in settles:
            continue
        y = math.log(settles[r["fid"]] / r["p0"])
        key = (r["symbol"], r["horizon_days"], r["source"])
        loss[key][r["fid"]] = pinball(r["grid"], y) * 100  # 同一编号有多条 AI 调整时，取最后一条
        g = r["grid"]
        cover[key].append((quantile(g, 0.05) <= y <= quantile(g, 0.95), quantile(g, 0.25) <= y <= quantile(g, 0.75)))
        for name, p in r["probs"].items():
            t = float(name.rstrip("%"))
            hit = y <= math.log(1 + t / 100) if t < 0 else y >= math.log(1 + t / 100)
            brier[key].append((p - (1 if hit else 0)) ** 2)

    print(f"\n{'资产':<10}{'周期':>4}  {'来源':<6}{'条数':>4}  {'分位数损失':>8}  {'90% 区间命中':>10}  {'50% 区间命中':>10}  {'阈值 Brier':>9}")
    for key in sorted(loss):
        symbol, h, source = key
        n = len(loss[key])
        c90 = statistics.fmean(a for a, _ in cover[key]) * 100
        c50 = statistics.fmean(b for _, b in cover[key]) * 100
        br = statistics.fmean(brier[key]) if brier[key] else float("nan")
        print(f"{symbol:<10}{h:>3}天  {MARKET_ZH[source]:<6}{n:>4}  {statistics.fmean(loss[key].values()):>9.3f}  {c90:>10.0f}%  {c50:>10.0f}%  {br:>9.3f}  {note_n(n)}")

    print("\n两两比较（只算双方都有的预测；差值为负表示前者更准）：")
    for symbol, h in sorted({(k[0], k[1]) for k in loss}):
        for a, b in (("ai", "stat"), ("stat", "baseline")):
            la, lb = loss.get((symbol, h, a), {}), loss.get((symbol, h, b), {})
            common = sorted(set(la) & set(lb))
            if common:
                diff = statistics.fmean(la[f] - lb[f] for f in common)
                print(f"  {symbol} {h} 天  {MARKET_ZH[a]} 对 {MARKET_ZH[b]}：{diff:+.3f} {note_n(len(common))}")
    print("注意：起始时间相近的预测，结算窗口大量重叠，不能当独立样本看。\n")


def main():
    args = sys.argv[1:]
    if "-h" in args or "--help" in args:
        print(__doc__)
        return
    if "--public" in args:
        args.remove("--public")
        common.INCLUDE_PRIVATE = False
        print("（只算公开账本）\n")
    what = args[0] if args else "all"
    if what in ("all", "events"):
        events()
    if what in ("all", "market"):
        market()


if __name__ == "__main__":
    main()
