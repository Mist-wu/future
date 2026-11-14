#!/usr/bin/env python3
"""Polymarket：给候选题、入库、揭晓市场价、查结算。全部是公开的只读接口。

用法：
  polymarket.py candidates [--n 10] [--tags crypto,fed]   列候选题，不显示价格
  polymarket.py add MARKET_ID [--title-zh ...] [--decision ...]   入库，不显示价格
  polymarket.py price q0001      揭晓市场价：显示封存的那一次，再记下并显示当前的
  polymarket.py seal q0001 ...   补存一次市场价，不显示（记 ai_blind 时会自动存，一般用不到）
  polymarket.py check            查所有未结算的 Polymarket 题：已出结果的自动结算，其余更新市场价

揭晓的顺序：
  price 要求这道题已经有 AI 盲测值，并且用户给过盲测值或者跳过了。
  揭晓之前，check 更新的市场价同样封存，不显示。
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import timedelta

import ledger
from common import config, http_json, iso, local, now, parse_iso, pct

GAMMA = "https://gamma-api.polymarket.com"


def yes_price(m: dict) -> float | None:
    """Yes 的价格：有买卖盘就取中间价，否则取 outcomePrices。"""
    try:
        outcomes = json.loads(m["outcomes"])
        prices = [float(x) for x in json.loads(m["outcomePrices"])]
        i = [o.lower() for o in outcomes].index("yes")
    except (KeyError, ValueError, TypeError):
        return None
    bid, ask = m.get("bestBid"), m.get("bestAsk")
    if i == 0 and bid is not None and ask is not None and 0 < bid <= ask < 1 and not m.get("closed"):
        return round((float(bid) + float(ask)) / 2, 4)
    return prices[i]


def is_binary(m: dict) -> bool:
    try:
        return sorted(o.lower() for o in json.loads(m["outcomes"])) == ["no", "yes"]
    except (KeyError, ValueError, TypeError):
        return False


def closed_time(m: dict) -> str:
    """关闭时间。Polymarket 的写法是 2025-01-20 17:35:42+00，先补成标准格式。"""
    text = (m.get("closedTime") or m.get("endDate") or "").strip().replace(" ", "T")
    if text.endswith("+00"):
        text += ":00"
    try:
        return iso(parse_iso(text))
    except ValueError:
        return iso(now())


def fetch_market(market_id: str) -> dict:
    return http_json(f"{GAMMA}/markets/{market_id}")


def current_price(q: dict) -> float | None:
    return yes_price(fetch_market(q["pm"]["market_id"]))


def cmd_candidates(a):
    cfg = config()["polymarket"]
    tags = a.tags.split(",") if a.tags else cfg["tags"]
    n = a.n or cfg["candidates"]
    lo, hi = cfg["price_band"]
    t_min = now() + timedelta(days=cfg["min_days"])
    t_max = now() + timedelta(days=cfg["max_days"])
    have = {q.get("pm", {}).get("market_id") for q in ledger.questions().values()}

    events: dict[str, dict] = {}
    for tag in tags:
        rows = http_json(f"{GAMMA}/events", {"tag_slug": tag, "closed": "false", "active": "true",
                                             "limit": 60, "order": "volume24hr", "ascending": "false"})
        for e in rows:
            e.setdefault("_tags", set()).add(tag)
            if e["id"] in events:
                events[e["id"]]["_tags"].add(tag)
            else:
                events[e["id"]] = e

    picked = []
    for e in events.values():
        ok = []
        for m in e.get("markets", []):
            if m.get("closed") or not m.get("active") or not m.get("acceptingOrders"):
                continue
            if not is_binary(m) or m["id"] in have or not m.get("endDate"):
                continue
            end = parse_iso(m["endDate"])
            price = yes_price(m)
            if not (t_min <= end <= t_max) or price is None or not (lo <= price <= hi):
                continue
            if float(m.get("volumeNum") or 0) < cfg["min_volume"]:
                continue
            ok.append(m)
        # 同一事件常有十几个档位，只留近 24 小时成交最多的几道
        ok.sort(key=lambda m: float(m.get("volume24hr") or 0), reverse=True)
        for m in ok[:cfg["per_event"]]:
            picked.append((e, m))

    picked.sort(key=lambda x: float(x[1].get("volume24hr") or 0), reverse=True)
    if not picked:
        print("没有符合条件的候选题。可以放宽 config.toml 里 [polymarket] 的过滤条件。")
        return
    print(f"候选题（{'、'.join(tags)}；{cfg['min_days']} 到 {cfg['max_days']} 天内截止；不显示价格）：")
    for i, (e, m) in enumerate(picked[:n], 1):
        end = parse_iso(m["endDate"])
        days = (end - now()).days
        vol = float(m.get("volume24hr") or 0)
        print(f"{i:>2}. [{m['id']}] {m['question']}")
        print(f"     事件：{e['title']}｜截止 {local(end, '%m-%d')}（{days} 天后）｜24 小时成交 ${vol:,.0f}｜{'、'.join(sorted(e['_tags']))}")


def cmd_add(a):
    m = fetch_market(a.market_id)
    if not is_binary(m):
        sys.exit("这道题不是 Yes/No 二元题，暂不支持。")
    if any(q.get("pm", {}).get("market_id") == m["id"] for q in ledger.questions().values()):
        sys.exit("这道题已经在题库里。")
    event = (m.get("events") or [{}])[0]
    url = f"https://polymarket.com/event/{event['slug']}" if event.get("slug") else f"https://polymarket.com/market/{m['slug']}"
    rec = ledger.create_question(
        title=m["question"], criteria=m.get("description") or "", close=m["endDate"],
        source="polymarket", title_zh=a.title_zh, decision=a.decision,
        tags=[t for t in a.tags.split(",") if t], url=url,
        pm={"market_id": m["id"], "slug": m["slug"], "condition_id": m.get("conditionId", "")},
    )
    print(f"已入库 {rec['qid']}：{rec['file']}")
    print(f"题目：{m['question']}")
    print(f"截止：{local(parse_iso(m['endDate']))}")
    print("价格没有显示。先写 AI 盲测值，再用 polymarket.py price 揭晓。")


def cmd_price(a):
    q = ledger.questions().get(a.qid) or sys.exit(f"没有这道题：{a.qid}")
    if q["source"] != "polymarket":
        sys.exit("这道题不是 Polymarket 的题，没有市场价。")
    rows = ledger.forecasts(a.qid)
    if ledger.latest(a.qid, "ai_blind") is None and not a.force:
        sys.exit("这道题还没有 AI 盲测值。先记 ai_blind，再揭晓市场价。确实要先看，加 --force。")
    if not any(r["source"] == "human_blind" for r in rows) and not a.force:
        sys.exit("用户还没有给盲测值，也没有跳过。先记 human_blind 或 skip，再揭晓。确实要先看，加 --force。")
    sealed = [r for r in rows if r["source"] == "market" and r.get("sealed")]
    if sealed:  # 只显示最早的一条，它和 AI 盲测值是同一时刻的
        r = sealed[0]
        print(f"{a.qid} 封存的市场价（{local(parse_iso(r['ts']))}）：{pct(r['p']).strip()}  {r.get('note', '')}")
    p = current_price(q)
    if p is None:
        sys.exit("取不到当前价格。")
    ledger.add_forecast(a.qid, "market", p)
    print(f"{a.qid} 当前市场价（Yes）：{pct(p).strip()}，已记账。")


def cmd_seal(a):
    qs = ledger.questions()
    for qid in a.qids:
        q = qs.get(qid) or sys.exit(f"没有这道题：{qid}")
        if q["source"] != "polymarket":
            print(f"{qid} 不是 Polymarket 的题，没有市场价。")
        elif ledger.market_revealed(qid):
            print(f"{qid} 的市场价已经揭晓过，不需要封存。")
        else:
            p = current_price(q)
            if p is None:
                print(f"{qid} 取不到价格。")
                continue
            ledger.add_forecast(qid, "market", p, note=a.note, sealed=True)
            print(f"{qid} 市场价已存下，没有显示。")


def cmd_check(_):
    res = ledger.resolutions()
    todo = [q for q in ledger.questions().values() if q["source"] == "polymarket" and q["qid"] not in res]
    if not todo:
        print("没有未结算的 Polymarket 题。")
        return
    for q in todo:
        m = fetch_market(q["pm"]["market_id"])
        p = yes_price(m)
        name = q["title_zh"] or q["title"]
        if m.get("closed") and p is not None and (p >= 0.99 or p <= 0.01):
            outcome = "yes" if p >= 0.99 else "no"
            resolved_at = closed_time(m)
            ledger.add_resolution(q["qid"], outcome, note="Polymarket 结果", evidence=q["url"], resolved_at=resolved_at)
            print(f"已结算  {q['qid']} → {outcome}  {name}")
        elif m.get("closed"):
            print(f"待人工  {q['qid']} 已关闭，但结果不是明确的 Yes/No（Yes 价 {p}），请看 {q['url']}")
        elif p is None:
            print(f"未出结果 {q['qid']}（取不到市场价）  {name}")
        elif ledger.market_revealed(q["qid"]):
            # 已揭晓的题：更新一条并显示，供时间加权打分用
            ledger.add_forecast(q["qid"], "market", p)
            print(f"未出结果 {q['qid']} 市场价 {pct(p).strip()}  {name}")
        elif ledger.latest(q["qid"], "ai_blind") is not None:
            # 未揭晓的题：照样更新，但封存不显示
            ledger.add_forecast(q["qid"], "market", p, sealed=True)
            print(f"未出结果 {q['qid']}（市场价已更新并封存，未揭晓）  {name}")
        else:
            print(f"未出结果 {q['qid']}（还没有 AI 盲测值，市场价未存）  {name}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("candidates")
    p.add_argument("--n", type=int, default=0)
    p.add_argument("--tags", default="")
    p.set_defaults(fn=cmd_candidates)

    p = sub.add_parser("add")
    p.add_argument("market_id")
    p.add_argument("--title-zh", default="")
    p.add_argument("--decision", default="")
    p.add_argument("--tags", default="")
    p.set_defaults(fn=cmd_add)

    p = sub.add_parser("price")
    p.add_argument("qid")
    p.add_argument("--force", action="store_true")
    p.set_defaults(fn=cmd_price)

    p = sub.add_parser("seal")
    p.add_argument("qids", nargs="+")
    p.add_argument("--note", default="")
    p.set_defaults(fn=cmd_seal)

    sub.add_parser("check").set_defaults(fn=cmd_check)

    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
