---
name: forecast-round
description: 预测工作区的“跑一次”全流程：结算到期的事件题和市场预测、更新成绩、出新的市场预测、复查未到期的事件题、给新的候选题、写简报并提交。用户说“跑一次”“例行检查”“更新一下预测”时使用。
---

# 跑一次

全流程有六步。用户只要其中几步时，只做那几步。命令都在工作区根目录运行。

## 1. 结算

```bash
python3 scripts/market.py settle
python3 scripts/polymarket.py check
python3 scripts/ledger.py open
```

前两条命令会自动结算到期的市场预测和已出结果的 Polymarket 题。第三条列出未结算的题，其中标着“已过截止”的手动题，按 `resolve-review` 手册结算。

这一步新结算了事件题，就按 `resolve-review` 手册给每道题写复盘。

## 2. 更新成绩

```bash
python3 scripts/score.py
```

把输出贴给用户。读法见 `scoreboard` 手册。

## 3. 市场预测

按 `market-forecast` 手册，给 `config.toml` 里的每个资产出新的 7 天和 30 天预测。

## 4. 复查未到期的事件题

每道题的文件里，上次预测的末尾写着“什么消息会让我改判断”。逐题搜最近的消息：

- 触发了：按 `event-forecast` 手册重新预测，记一条新的 `ai_informed`。条件允许时也更新 `ai_blind`。
- 没触发：在题目文件的“预测记录”里加一行，写明日期和“复查，无变化”。

离截止不到 7 天的题，不管有没有触发，都重新预测一次。

## 5. 新候选题

```bash
python3 scripts/polymarket.py candidates
```

把候选列给用户，请用户挑 3 到 5 道，也可以直接提自己的问题。之后按 `event-forecast` 手册走盲测流程。

## 6. 简报和提交

写 `briefs/YYYY-MM-DD.md`，一页以内，内容按这个顺序：

1. 这次结算了什么，结果如何。
2. 当前成绩和样本量。
3. 新的市场预测：每个资产的五档价格、阈值概率、你的调整和理由。
4. 事件题里概率变动超过 10 个百分点的，写明原因。
5. 按“相关决定”分组，列出和每个决定有关的预测。
6. 建议下次检查的时间和提前检查的条件。

然后提交：

```bash
git add -A && git commit -m "预测记录 YYYY-MM-DD：<一句话概括>"
```

最后在对话里告诉用户建议的下次检查时间。算法见 `market-forecast` 手册的最后一节，再把事件题的截止日算进去。
