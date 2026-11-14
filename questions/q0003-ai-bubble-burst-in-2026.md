# q0003 AI 泡沫在 2026 年破裂？

- 来源：polymarket
- 截止：2027-01-01 13:59 JST
- 标签：ai、tech
- 链接：https://polymarket.com/market/ai-industry-downturn-by-december-31-2026-857

## 题目原文

AI bubble burst in 2026?

## 判定标准（原文）

This market will resolve to "Yes" if the AI industry experiences an industry downturn by the specified date, 11:59 PM ET. Otherwise, this market will resolve to "No".

For the purposes of this market, the AI industry will be considered to have experienced an industry downturn once at least three of the following events have occurred within 90 days of this market's specified timeframe:
- NVIDIA Corporation (NVDA) closing stock price is down 50% from its all-time high.
- iShares PHLX Semiconductor ETF (SOXX) closing stock price is down 40% from its all-time high.
- OpenAI, Inc. or Anthropic PBC declares bankruptcy.
- OpenAI, Inc. is acquired.
- H100 rental price falls to $1.00 or lower for five consecutive days, as shown on the SiliconData Silicon Index at:
https://www.silicondata.com/products/silicon-index.
- Major AI Hardware Supplier Collapse: Taiwan Semiconductor Manufacturing Company Limited (TSM), ASML Holding N.V. (ASML), Broadcom Inc. (AVGO), Arista Networks, Inc. (ANET), or Super Micro Computer, Inc. (SMCI), closing stock price is down 50% from its all-time high.

This market may resolve immediately once three conditions have been met within 90 days of the specified timeframe.

This market will not resolve to "Yes" until three conditions have been met, regardless of reporting of an industry downturn or similar claims.

The primary resolution source will be official information from the respective companies and listing exchanges; however, a consensus of credible reporting will also be used.

## 判定标准（中文）

到 2026 年 12 月 31 日 23:59（美东时间）前，下面六件事里至少发生三件，判 Yes，否则判 No：

- 英伟达（NVDA）收盘价比历史最高点低 50%。
- iShares 半导体 ETF（SOXX）收盘价比历史最高点低 40%。
- OpenAI 或 Anthropic 宣布破产。
- OpenAI 被收购。
- H100 租赁价格连续五天在每小时 1.00 美元或以下，以 SiliconData 的指数为准。
- 台积电（TSM）、阿斯麦（ASML）、博通（AVGO）、Arista（ANET）、超微电脑（SMCI）中任意一家的收盘价比历史最高点低 50%。

三件事要发生在本题时间范围的 90 天之内。满足三条后可以立即结算。媒体怎么报道“泡沫破裂”不算数，只看这六条。

## 预测记录

### 2026-11-13 首次预测（单次，AI 盲测）

没有见过这道题的市场价。

1. **基准率**。先看六条的现状，数据来自 Yahoo 的收盘价：

   | 条件 | 现状 | 到年底发生的概率 |
   |---|---|---|
   | 英伟达比高点低 50% | 现价 166.31，比高点 239.24 低 30.5%，要跌到 119.62 | 约 9% |
   | SOXX 比高点低 40% | 现价 156.39，比高点低 28.4%；11 月初最低收盘低 39.6%，差一点 | 约 30% 到 38% |
   | OpenAI 或 Anthropic 破产 | 没有迹象 | 接近 0 |
   | OpenAI 被收购 | 没有迹象 | 接近 0 |
   | H100 租金不高于 1 美元 | 11 月 9 日约 3.01 美元，一年来在涨 | 接近 0 |
   | 五家供应商之一比高点低 50% | 超微电脑比 2024 年的高点低 75.8%，已经满足 | 见下 |

   概率用工作区的统计模型按收盘价模拟 34 个交易日得到。
2. **证据**。超微电脑那一条按字面已经成立。剩下能凑数的只有英伟达和 SOXX 两条，必须同时发生。两者高度相关：英伟达再跌 28% 时，SOXX 多半也跌过了线。但黄仁勋辞职当天，AMD 和博通是涨的，说明英伟达也可能单独下跌。来源：[NVIDIA 8-K](https://www.sec.gov/Archives/edgar/data/0001045810/000104581026000082/nvidiaannouncesceotransiti.htm)、[Wolf Street](https://wolfstreet.com/2026/11/05/bloodletting-in-semiconductor-stocks/)、[gr1d](https://gr1d.us/insights/rent-vs-buy-gpu-servers)。
3. **调整**。英伟达触及的概率取 9%，此时 SOXX 也过线的概率取 75%，两条同时发生约 7%。判定上有一处不确定：平台可能认为超微电脑早就跌破，不算本期“发生”。我给“算数”七成。不算数时还需要另一家供应商也腰斩，概率约 3%。合起来约 6%。
4. **反向设想**。如果判了 Yes：英伟达五周已经跌了 30%，再来一轮同样的下跌就够了。可能的推手是财报指引下调、辞职事件牵出监管问题，或者美联储加息 50 个基点。这条路径是现实的，所以没有给到 3% 以下。
5. **概率和触发条件**。概率 6%。会让我明显改判断的消息：英伟达收盘跌破 140，或 SOXX 收盘跌破 140；平台对超微电脑那一条给出说明；11 月 17 日英伟达财报后的走势。

### 2026-11-14 复查，无变化

没有触发重估条件。英伟达 11 月 13 日收 162.85，SOXX 收 149.30，都在 140 的触发线上方。平台没有对超微电脑那一条给出说明。

## 复盘
