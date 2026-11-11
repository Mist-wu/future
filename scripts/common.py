"""公共函数：路径、时间、JSONL 账本读写、HTTP、概率换算。"""
from __future__ import annotations

import json
import math
import os
import time
import tomllib
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# FUTURE_ROOT 只在测试时用：把账本和题库指到临时目录
ROOT = Path(os.environ.get("FUTURE_ROOT") or Path(__file__).resolve().parent.parent)
LEDGER = ROOT / "ledger"
QUESTIONS = ROOT / "questions"
PRIVATE = ROOT / "private"   # 不进公开仓库：私有题、相关决定、私有简报
INCLUDE_PRIVATE = True       # score.py --public 会把它关掉，只算公开账本


def now() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(text: str) -> datetime:
    text = text.strip()
    if len(text) == 10:  # 只有日期，按当天结束算
        text += "T23:59:59Z"
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def local(dt: datetime, fmt: str = "%Y-%m-%d %H:%M %Z") -> str:
    """按本机时区显示，默认带时区缩写。"""
    return dt.astimezone().strftime(fmt)


def config() -> dict:
    with open(ROOT / "config.toml", "rb") as f:
        return tomllib.load(f)


def _read(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def read_jsonl(name: str) -> list[dict]:
    """读账本。公开账本和私有账本合在一起，按写入时间排序。"""
    rows = _read(LEDGER / name)
    if INCLUDE_PRIVATE:
        extra = _read(PRIVATE / "ledger" / name)
        if extra:
            rows = sorted(rows + extra, key=lambda r: r.get("ts", ""))
    return rows


def _append(path: Path, record: dict) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {"ts": iso(now()), **record}
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def append_jsonl(name: str, record: dict, private: bool = False) -> dict:
    """账本只追加，不改写。每条记录自动带上写入时间 ts。private=True 时写进私有账本。"""
    return _append((PRIVATE / "ledger" if private else LEDGER) / name, record)


def read_private(name: str) -> list[dict]:
    return _read(PRIVATE / name) if INCLUDE_PRIVATE else []


def append_private(name: str, record: dict) -> dict:
    return _append(PRIVATE / name, record)


def http_json(url: str, params: dict | None = None, retries: int = 3):
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    last: Exception | None = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            if e.code < 500 and e.code != 429:
                raise
            last = e
        except (urllib.error.URLError, TimeoutError) as e:
            last = e
        time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"请求失败：{url}（{last}）")


def clip(p: float, lo: float = 0.01, hi: float = 0.99) -> float:
    return min(hi, max(lo, p))


def logit(p: float) -> float:
    p = clip(p)
    return math.log(p / (1 - p))


def inv_logit(x: float) -> float:
    return 1 / (1 + math.exp(-x))


def parse_p(text: str) -> float:
    """接受 0.35、35% 或 35 三种写法，返回 0 到 1 之间的概率。"""
    text = str(text).strip()
    if text.endswith("%"):
        p = float(text[:-1]) / 100
    else:
        p = float(text)
        if p > 1:
            p /= 100
    if not 0 <= p <= 1:
        raise ValueError(f"概率超出范围：{text}")
    return p


def pct(p: float | None) -> str:
    return "  -  " if p is None else f"{p * 100:4.0f}%"
