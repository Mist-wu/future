#!/usr/bin/env python3
"""事件题的题库和账本：建题、记概率、结算、查看。

用法：
  ledger.py new --title "..." --criteria "..." --close 2026-12-31 [--title-zh ...] [--decision ...] [--tags a,b]
  ledger.py forecast q0001 ai_blind 0.35 [--mode single|ensemble] [--note ...]
  ledger.py skip q0001                     你跳过盲测
  ledger.py resolve q0001 yes|no|void [--note ...] [--evidence URL]
  ledger.py open                           未结算的题
  ledger.py show q0001                     一道题的全部记录
"""
from __future__ import annotations

import argparse
import re
import sys

from common import (QUESTIONS, append_jsonl, inv_logit, iso, local, logit, now,
                    parse_iso, parse_p, pct, read_jsonl)

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


def latest(qid: str, source: str) -> float | None:
    rows = [r for r in forecasts(qid) if r["source"] == source and r.get("p") is not None]
    return rows[-1]["p"] if rows else None


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:40].rstrip("-")
    return slug or "question"


def create_question(*, title: str, criteria: str, close: str, source: str = "manual",
                    title_zh: str = "", decision: str = "", tags: list[str] | None = None,
                    url: str = "", pm: dict | None = None) -> dict:
    qid = f"q{len(questions()) + 1:04d}"
    close_dt = parse_iso(close)
    rec = {
        "qid": qid,
        "source": source,
        "title": title,
        "title_zh": title_zh,
        "criteria": criteria,
        "close": iso(close_dt),
        "decision": decision,
        "tags": tags or [],
        "url": url,
        "file": f"questions/{qid}-{slugify(title)}.md",
    }
    if pm:
        rec["pm"] = pm
    append_jsonl("questions.jsonl", rec)

    QUESTIONS.mkdir(exist_ok=True)
    lines = [
        f"# {qid} {title_zh or title}",
        "",
        f"- 来源：{source}",
        f"- 截止：{local(close_dt)}",
    ]
    if decision:
        lines.append(f"- 相关决定：{decision}")
    if tags:
        lines.append(f"- 标签：{'、'.join(tags)}")
    if url:
        lines.append(f"- 链接：{url}")
    lines += ["", "## 题目原文", "", title, "", "## 判定标准（原文）", "", criteria.strip(), "",
              "## 判定标准（中文）", "", "（待补）", "", "## 预测记录", "", "## 复盘", ""]
    (QUESTIONS.parent / rec["file"]).write_text("\n".join(lines), encoding="utf-8")
    return rec


def add_forecast(qid: str, source: str, p: float | None, mode: str = "", note: str = "",
                 skipped: bool = False) -> dict:
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
    rec = append_jsonl("forecasts.jsonl", rec)

    # 你的盲测值和 AI 盲测值都有了，就自动记一条机械平均（对数几率上各占一半）
    if source in ("ai_blind", "human_blind") and p is not None:
        a, h = latest(qid, "ai_blind"), latest(qid, "human_blind")
        if a is not None and h is not None:
            avg = inv_logit((logit(a) + logit(h)) / 2)
            append_jsonl("forecasts.jsonl", {"qid": qid, "source": "mech_avg", "p": round(avg, 4)})
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
    return append_jsonl("resolutions.jsonl", rec)


def cmd_new(a):
    rec = create_question(title=a.title, criteria=a.criteria, close=a.close, title_zh=a.title_zh,
                          decision=a.decision, tags=[t for t in a.tags.split(",") if t], url=a.url)
    print(f"已建题 {rec['qid']}：{rec['file']}")


def cmd_forecast(a):
    rec = add_forecast(a.qid, a.source, parse_p(a.p), a.mode, a.note)
    print(f"已记账：{a.qid} {SOURCE_ZH[a.source]} {pct(rec['p']).strip()}")


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
        print(f"  {q['qid']}  {local(parse_iso(q['close']), '%m-%d')}（{when}）  {q['title_zh'] or q['title']}")
        print(f"         已记：{marks}")


def cmd_show(a):
    q = questions().get(a.qid) or sys.exit(f"没有这道题：{a.qid}")
    print(f"{q['qid']}  {q['title_zh'] or q['title']}")
    print(f"截止：{local(parse_iso(q['close']))}   文件：{q['file']}")
    if q.get("decision"):
        print(f"相关决定：{q['decision']}")
    for r in forecasts(a.qid):
        extra = "（跳过）" if r.get("skipped") else ""
        mode = f" [{r['mode']}]" if r.get("mode") else ""
        print(f"  {local(parse_iso(r['ts']))}  {SOURCE_ZH[r['source']]:<6} {pct(r.get('p'))}{extra}{mode}  {r.get('note', '')}")
    r = resolutions().get(a.qid)
    if r:
        print(f"结算：{r['outcome']}（{local(parse_iso(r['resolved_at']))}）{r.get('note', '')}")


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
    p.set_defaults(fn=cmd_show)

    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
