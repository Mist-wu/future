#!/usr/bin/env python3
"""事件题的题库和账本：建题、记概率、结算、查看。

用法：
  ledger.py new --title "..." --criteria "..." --close 2026-12-31 [--title-zh ...] [--decision ...] [--tags a,b] [--private]
  ledger.py forecast q0001 ai_blind 0.35 [--mode single|ensemble] [--note ...]
  ledger.py skip q0001                     你跳过盲测
  ledger.py resolve q0001 yes|no|void [--note ...] [--evidence URL]
  ledger.py open                           未结算的题
  ledger.py show q0001                     一道题的全部记录。用户没给盲测值时，AI 的数会遮住
  ledger.py decide q0001 "相关决定"        给一道题补上或修改相关决定
  ledger.py decisions                      按相关决定分组列出预测

市场价的封存：
  给 Polymarket 的题记 ai_blind 时，脚本会同时取一次市场价存进账本，但不显示。
  这样市场价和 AI 盲测值是同一时刻的，用户晚几天回数也不影响对比。
  用 polymarket.py price 揭晓。揭晓之前，show 不显示封存的数值。

公开和私有：
  公开题的编号是 q0001 这样的，记录在 ledger/ 和 questions/ 里，会推送到公开仓库。
  加 --private 建的题编号是 p0001 这样的，整道题都记在 private/ 里，只留在本机。
  “相关决定”不管题目是否公开，一律记在 private/ 里。
"""
from __future__ import annotations

import argparse
import re
import sys

from common import (ROOT, append_jsonl, append_private, inv_logit, iso, local, logit, now,
                    parse_iso, parse_p, pct, read_jsonl, read_private)

SOURCES = ["ai_blind", "ai_informed", "human_blind", "human_final", "market", "mech_avg"]
SOURCE_ZH = {
    "ai_blind": "AI 盲测",
    "ai_informed": "AI 知情",
    "human_blind": "你 盲测",
    "human_final": "你 最终",
    "market": "市场价",
    "mech_avg": "机械平均",
}


def questions() -> dict[str, dict]:
    return {q["qid"]: q for q in read_jsonl("questions.jsonl")}


def resolutions() -> dict[str, dict]:
    return {r["qid"]: r for r in read_jsonl("resolutions.jsonl")}


def forecasts(qid: str | None = None) -> list[dict]:
    rows = read_jsonl("forecasts.jsonl")
    return [r for r in rows if qid is None or r["qid"] == qid]


def market_revealed(qid: str) -> bool:
    """市场价是否已经揭晓过。封存的记录带 sealed 标记，揭晓时会记一条不带标记的。"""
    return any(r["source"] == "market" and not r.get("sealed") for r in forecasts(qid))


def latest(qid: str, source: str) -> float | None:
    rows = [r for r in forecasts(qid) if r["source"] == source and r.get("p") is not None]
    return rows[-1]["p"] if rows else None


def is_private(qid: str) -> bool:
    return bool(questions().get(qid, {}).get("private"))


def decisions() -> dict[str, str]:
    """题目编号 → 相关决定。只存在 private/ 里，后写的覆盖先写的。"""
    out = {q["qid"]: q["decision"] for q in questions().values() if q.get("decision")}
    for r in read_private("decisions.jsonl"):
        out[r["qid"]] = r["decision"]
    return {k: v for k, v in out.items() if v}


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:40].rstrip("-")
    return slug or "question"


def create_question(*, title: str, criteria: str, close: str, source: str = "manual",
                    title_zh: str = "", decision: str = "", tags: list[str] | None = None,
                    url: str = "", pm: dict | None = None, private: bool = False) -> dict:
    prefix = "p" if private else "q"
    qid = f"{prefix}{sum(q.startswith(prefix) for q in questions()) + 1:04d}"
    close_dt = parse_iso(close)
    folder = "private/questions" if private else "questions"
    rec = {
        "qid": qid,
        "source": source,
        "title": title,
        "title_zh": title_zh,
        "criteria": criteria,
        "close": iso(close_dt),
        "tags": tags or [],
        "url": url,
        "file": f"{folder}/{qid}-{slugify(title)}.md",
    }
    if pm:
        rec["pm"] = pm
    if private:
        rec["private"] = True
    append_jsonl("questions.jsonl", rec, private=private)
    if decision:
        append_private("decisions.jsonl", {"qid": qid, "decision": decision})

    lines = [
        f"# {qid} {title_zh or title}",
        "",
        f"- 来源：{source}",
        f"- 截止：{local(close_dt)}",
    ]
    if decision and private:  # 公开题的文件里不写相关决定
        lines.append(f"- 相关决定：{decision}")
    if tags:
        lines.append(f"- 标签：{'、'.join(tags)}")
    if url:
        lines.append(f"- 链接：{url}")
    lines += ["", "## 题目原文", "", title, "", "## 判定标准（原文）", "", criteria.strip(), "",
              "## 判定标准（中文）", "", "（待补）", "", "## 预测记录", "", "## 复盘", ""]
    path = ROOT / rec["file"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return rec


def add_forecast(qid: str, source: str, p: float | None, mode: str = "", note: str = "",
                 skipped: bool = False, sealed: bool = False) -> dict:
    if qid not in questions():
        sys.exit(f"没有这道题：{qid}")
    if source not in SOURCES:
        sys.exit(f"来源必须是 {SOURCES} 之一")
    if qid in resolutions():
        sys.exit(f"{qid} 已结算，不能再记预测")
    rec = {"qid": qid, "source": source, "p": p}
    if mode:
        rec["mode"] = mode
    if note:
        rec["note"] = note
    if skipped:
        rec["skipped"] = True
    if sealed:
        rec["sealed"] = True
    private = is_private(qid)
    rec = append_jsonl("forecasts.jsonl", rec, private=private)

    # 你的盲测值和 AI 盲测值都有了，就自动记一条机械平均（对数几率上各占一半）
    if source in ("ai_blind", "human_blind") and p is not None:
        a, h = latest(qid, "ai_blind"), latest(qid, "human_blind")
        if a is not None and h is not None:
            avg = inv_logit((logit(a) + logit(h)) / 2)
            append_jsonl("forecasts.jsonl", {"qid": qid, "source": "mech_avg", "p": round(avg, 4)}, private=private)
    return rec


def add_resolution(qid: str, outcome: str, note: str = "", evidence: str = "",
                   resolved_at: str = "") -> dict:
    if qid not in questions():
        sys.exit(f"没有这道题：{qid}")
    if qid in resolutions():
        sys.exit(f"{qid} 已经结算过：{resolutions()[qid]['outcome']}")
    rec = {"qid": qid, "outcome": outcome, "resolved_at": resolved_at or iso(now())}
    if note:
        rec["note"] = note
    if evidence:
        rec["evidence"] = evidence
    return append_jsonl("resolutions.jsonl", rec, private=is_private(qid))


def cmd_new(a):
    rec = create_question(title=a.title, criteria=a.criteria, close=a.close, title_zh=a.title_zh,
                          decision=a.decision, tags=[t for t in a.tags.split(",") if t], url=a.url,
                          private=a.private)
    where = "私有题，只留在本机" if a.private else "公开题"
    print(f"已建题 {rec['qid']}（{where}）：{rec['file']}")


def cmd_forecast(a):
    rec = add_forecast(a.qid, a.source, parse_p(a.p), a.mode, a.note)
    print(f"已记账：{a.qid} {SOURCE_ZH[a.source]} {pct(rec['p']).strip()}")
    q = questions()[a.qid]
    if a.source == "ai_blind" and q["source"] == "polymarket" and not market_revealed(a.qid):
        # 同一时刻封存市场价，不显示
        try:
            import polymarket
            p = polymarket.current_price(q)
            if p is None:
                raise RuntimeError("接口没有返回价格")
            add_forecast(a.qid, "market", p, sealed=True)
            print("市场价已同时存下，没有显示。")
        except Exception as e:  # 取价失败不影响盲测值入账
            print(f"提醒：市场价没存上（{e}）。稍后用 polymarket.py seal {a.qid} 补存。")


def cmd_skip(a):
    add_forecast(a.qid, "human_blind", None, skipped=True)
    print(f"已记账：{a.qid} 你跳过了盲测")


def cmd_resolve(a):
    add_resolution(a.qid, a.outcome, a.note, a.evidence)
    print(f"已结算：{a.qid} → {a.outcome}")


def cmd_open(_):
    res, rows = resolutions(), forecasts()
    todo = [q for q in questions().values() if q["qid"] not in res]
    if not todo:
        print("没有未结算的题。")
        return
    print(f"未结算 {len(todo)} 道（只显示哪些数已记，不显示数值）：")
    for q in sorted(todo, key=lambda q: q["close"]):
        days = (parse_iso(q["close"]) - now()).total_seconds() / 86400
        when = f"还有 {days:.0f} 天" if days >= 0 else f"已过截止 {-days:.0f} 天，待结算"
        have = {r["source"] for r in rows if r["qid"] == q["qid"]}
        marks = " ".join(SOURCE_ZH[s] for s in SOURCES if s in have) or "还没有任何预测"
        mark = "〔私有〕" if q.get("private") else ""
        print(f"  {q['qid']}  {local(parse_iso(q['close']), '%m-%d')}（{when}）  {mark}{q['title_zh'] or q['title']}")
        print(f"         已记：{marks}")


def cmd_show(a):
    q = questions().get(a.qid) or sys.exit(f"没有这道题：{a.qid}")
    print(f"{q['qid']}  {q['title_zh'] or q['title']}")
    print(f"截止：{local(parse_iso(q['close']))}   文件：{q['file']}")
    if a.qid in decisions():
        print(f"相关决定：{decisions()[a.qid]}（只存在本机）")
    rows = forecasts(a.qid)
    open_q = a.qid not in resolutions()
    hide_market = open_q and not market_revealed(a.qid)
    # 用户还没给盲测值时，AI 的数也先遮住，免得在对话里露出来
    hide_ai = open_q and not a.all and not any(r["source"] == "human_blind" for r in rows)
    for r in rows:
        extra = "（跳过）" if r.get("skipped") else ""
        mode = f" [{r['mode']}]" if r.get("mode") else ""
        if r.get("sealed") and hide_market:
            value, note = "已存，未揭晓", r.get("note", "")
        elif r["source"] in ("ai_blind", "ai_informed") and hide_ai:
            value, note = "已记，等用户先给数", ""
        else:
            value, note = pct(r.get("p")), r.get("note", "")
        print(f"  {local(parse_iso(r['ts']))}  {SOURCE_ZH[r['source']]:<6} {value}{extra}{mode}  {note}")
    r = resolutions().get(a.qid)
    if r:
        print(f"结算：{r['outcome']}（{local(parse_iso(r['resolved_at']))}）{r.get('note', '')}")


def cmd_decide(a):
    if a.qid not in questions():
        sys.exit(f"没有这道题：{a.qid}")
    append_private("decisions.jsonl", {"qid": a.qid, "decision": a.decision})
    print(f"已记下 {a.qid} 的相关决定（只存在本机）")


def cmd_decisions(_):
    qs, res = questions(), resolutions()
    groups: dict[str, list[str]] = {}
    for qid, d in decisions().items():
        groups.setdefault(d, []).append(qid)
    if not groups:
        print("还没有哪道题标了相关决定。")
        return
    for d, qids in groups.items():
        print(f"【{d}】")
        for qid in sorted(qids):
            q = qs[qid]
            ai = latest(qid, "ai_informed") or latest(qid, "ai_blind")
            state = f"已结算 {res[qid]['outcome']}" if qid in res else f"截止 {local(parse_iso(q['close']), '%m-%d')}"
            print(f"  {qid}  AI {pct(ai).strip()}  你 {pct(latest(qid, 'human_final') or latest(qid, 'human_blind')).strip()}  {state}  {q['title_zh'] or q['title']}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("new")
    p.add_argument("--title", required=True)
    p.add_argument("--criteria", required=True)
    p.add_argument("--close", required=True)
    p.add_argument("--title-zh", default="")
    p.add_argument("--decision", default="")
    p.add_argument("--tags", default="")
    p.add_argument("--url", default="")
    p.add_argument("--private", action="store_true", help="私有题：整道题只留在本机")
    p.set_defaults(fn=cmd_new)

    p = sub.add_parser("forecast")
    p.add_argument("qid")
    p.add_argument("source", choices=[s for s in SOURCES if s != "mech_avg"])
    p.add_argument("p")
    p.add_argument("--mode", default="", choices=["", "single", "ensemble"])
    p.add_argument("--note", default="")
    p.set_defaults(fn=cmd_forecast)

    p = sub.add_parser("skip")
    p.add_argument("qid")
    p.set_defaults(fn=cmd_skip)

    p = sub.add_parser("resolve")
    p.add_argument("qid")
    p.add_argument("outcome", choices=["yes", "no", "void"])
    p.add_argument("--note", default="")
    p.add_argument("--evidence", default="")
    p.set_defaults(fn=cmd_resolve)

    sub.add_parser("open").set_defaults(fn=cmd_open)

    p = sub.add_parser("show")
    p.add_argument("qid")
    p.add_argument("--all", action="store_true", help="用户还没给盲测值时，也显示 AI 的数")
    p.set_defaults(fn=cmd_show)

    p = sub.add_parser("decide")
    p.add_argument("qid")
    p.add_argument("decision")
    p.set_defaults(fn=cmd_decide)

    sub.add_parser("decisions").set_defaults(fn=cmd_decisions)

    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
