---
name: event-forecast
description: 预测工作区里事件题的全过程：从 Polymarket 候选里选题入库、把用户的一句话改写成可结算的问题、按五步法预测、走盲测流程、记账。用户提新问题、挑候选题、要你预测某件事会不会发生，或者说“认真做”时使用。
---

# 事件题：选题、预测和盲测

先读 `lessons.md`。命令都在工作区根目录运行。

## 入库

**Polymarket 的题**：

```bash
python3 scripts/polymarket.py candidates
python3 scripts/polymarket.py add <市场编号> --title-zh "中文题目" --decision "相关决定" --tags 标签
```

这两条命令都不显示价格。入库后打开题目文件，把判定标准译成中文，填进“判定标准（中文）”。原文保留。

**用户自己提的问题**：把用户的一句话改写成可结算的题，写明三样东西：截止日期、什么情况算发生、以什么来源为准。改写稿给用户确认后再入库：

```bash
python3 scripts/ledger.py new --title "题目" --criteria "判定标准" --close 2026-12-31 --title-zh "中文题目" --decision "相关决定"
```

问用户这道题关系到哪个决定，有就填 `--decision`。相关决定只记在本机的 `private/` 里，不进公开仓库。之后要补或者改，用 `python3 scripts/ledger.py decide q0001 "相关决定"`。

**公开题还是私有题**：这个仓库是公开的。题目谈的是公共话题，就建成公开题。题目涉及用户的私事，比如收入、工作、健康、身边的人，建题时加 `--private`：

```bash
python3 scripts/ledger.py new --private --title "题目" --criteria "判定标准" --close 2026-12-31
```

私有题的编号以 `p` 开头，题目文件在 `private/questions/`，概率和结算记在 `private/ledger/`。之后的预测、盲测和结算命令和公开题完全一样，脚本按编号自动分流。拿不准是否算私事时，问用户。

公开题的题目文件会被推送。写推理时只写公开信息，用户在对话里提到的持仓、成本价和个人打算不写进去。

## 五步法

每次预测都把这五步写进题目文件的“预测记录”，用日期作小标题。

1. **基准率**。先不看这件事的细节。找历史上同类事情发生的比例，写明用的是哪一类、数字从哪来。
2. **具体证据**。搜最新消息，分别列出支持和反对的关键证据，附来源链接。
3. **调整**。从基准率出发，逐条说明证据把概率移动了多少。
4. **反向设想**。假设结果和你的判断相反，写出最可能的原因。原因很容易想到，就把概率往 50% 收一点。
5. **概率和触发条件**。写下概率，再写“什么消息会让我明显改判断”。下次“跑一次”靠这一条决定要不要重新预测。

## 盲测流程

一道题记六个数。顺序决定了谁能看到什么，所以按这个顺序走。

**第一轮（你）**：

1. 做五步法，全程避开预测市场的价格。搜索结果里碰巧出现了价格，在记录里注明“已见市场价”。
2. 记账，对话里先不说这个数：

   ```bash
   python3 scripts/ledger.py forecast q0001 ai_blind 0.35 --mode single --note "一句话理由"
   ```

3. 把题目和判定标准发给用户，请用户回一个概率，或者说“跳过”。多道题可以一次列完。

**第二轮（用户回了数之后）**：

4. 记下用户的盲测值。两个盲测值都有了，脚本会自动记一条机械平均。

   ```bash
   python3 scripts/ledger.py forecast q0001 human_blind 0.5
   python3 scripts/ledger.py skip q0001      # 用户跳过时用这条
   ```

5. 揭晓市场价。手动题没有市场价，跳过这一步。

   ```bash
   python3 scripts/polymarket.py price q0001
   ```

6. 看过市场价后再想一遍，给出知情值。市场价和你的盲测值差得多时，先想市场可能知道什么你不知道的，再决定往市场靠多少。

   ```bash
   python3 scripts/ledger.py forecast q0001 ai_informed 0.3 --mode single --note "一句话理由"
   ```

7. 把三个数和主要理由告诉用户：AI 盲测、市场价、AI 知情。请用户给最终值，可以不改。

   ```bash
   python3 scripts/ledger.py forecast q0001 human_final 0.45
   ```

用户想先看 AI 的结果再给数，也照做，这道题用 `skip` 记盲测，再记 `human_final`。

## “认真做”

用户说“认真做”时，第一轮改成这样：

1. 派 3 个子代理，各自从空白上下文开始。给每个子代理的材料只有题目、判定标准、截止日期和五步法的要求，并说明不要查预测市场的价格。
2. 每个子代理交回概率和推理。
3. 三个概率在对数几率上取平均，作为 `ai_blind`，记账时用 `--mode ensemble`。
4. 把三份推理的要点和分歧写进题目文件。

第二轮的知情值由你在主对话里给，同样记 `--mode ensemble`。

## 查看

```bash
python3 scripts/ledger.py open           # 未结算的题
python3 scripts/ledger.py show q0001     # 一道题的全部记录
```
