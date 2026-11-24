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

### 2026-11-14 知情值（单次）

- AI 盲测 6%，封存的市场价 7%（2026-11-14 13:14 JST），用户盲测 20%，机械平均 11%。
- 知情值 7%。市场价和盲测值只差一个百分点。首次预测之后英伟达收 162.85，比高点低 31.9%；SOXX 收 149.30，比高点低 31.6%，离 40% 的线还差 12%。用同一个模型重算，英伟达到年底收盘腰斩的概率约 10%，SOXX 过线的概率约 50%。英伟达腰斩时 SOXX 多半也已过线，两条同时发生约 8% 到 9%。超微电脑那一条是否算数仍按七成，合起来约 7%。
- 重估条件不变：英伟达收盘跌破 140，或 SOXX 收盘跌破 140；平台对超微电脑那一条给出说明；11 月 17 日英伟达财报后的走势。

### 2026-11-21 重新预测，从 7% 升到 57%

触发了重估条件：英伟达和 SOXX 都收盘跌破 140。

1. **现状**。11 月 20 日收盘：

   | 条件 | 现状 |
   |---|---|
   | 英伟达比高点低 50% | 收 125.53，比高点 239.24 低 47.5%，还差 4.7% 到 119.62 |
   | SOXX 比高点低 40% | 收 123.40，比高点 218.34 低 43.5%，**已满足** |
   | 五家供应商之一比高点低 50% | 超微电脑比高点低 81.8%，按字面已满足；其余四家在 −23% 到 −37% |
   | 另外三条 | 没有迹象 |

2. **证据**。英伟达 11 月 17 日财报好于预期，次日仍跌 2.9%，原因是继任问题和中国业务。11 月 20 日 Reuters 报道 SEC 在调查英伟达的会计，股价单日跌 14%，七连跌，创 2008 年 10 月以来最差的一周。纳斯达克当天跌 5.3%。Polymarket 这道题从约 9% 涨到 58%。Benzinga 向 Polymarket 询问超微电脑那一条怎么算，目前没有答复。来源：[Yahoo Finance](https://finance.yahoo.com/markets/stocks/articles/nvidia-stock-plunges-12-reuters-201702082.html)、[Axios](https://www.axios.com/2026/11/20/anthropic-ipo-nvidia-ai-tech-selloff)、[CNBC](https://www.cnbc.com/2026/11/18/nvidia-stock-earnings.html)、[Benzinga](https://www.benzinga.com/markets/prediction-markets/26/11/63508103/polymarket-ai-bubble)、[Prediction News](https://predictionnews.com/story/polymarket-amplifies-gensler-warning-that-ai-is-already-a-bubble)。
3. **调整**。用工作区的方法按收盘价模拟到年底的 26 个交易日，五只股票同日抽样以保留相关性：英伟达收盘跌破 119.62 的概率约 75%，其余四家任一腰斩约 35%。11 月 20 日的冲击让过滤后的波动偏高，英伟达那一条下调到 65%。超微电脑那一条是否算数，我从七成上调到 75%：它的条件写的是收盘价比高点低 50%，这个状态在 90 天窗口里每天都成立。不算数时还需要另一家腰斩，在英伟达已跌破的情形下约四成。合计 0.65 ×（0.75 + 0.25 × 0.4）≈ 55%。
4. **反向设想**。如果最后判 No：最可能是 SEC 调查很快有了澄清，英伟达止跌反弹，没有再跌 5%；或者 Polymarket 宣布超微电脑早在开盘前就已腰斩，不算本期。两条都不难想象。
5. **概率和触发条件**。看过市场价（58%）之后给出知情值 57%，没有新的盲测值。会让我明显改判断的消息：英伟达收盘跌破 119.62（只剩超微电脑那一条的争议，概率会到 75% 以上）；Polymarket 对超微电脑那一条给出说明；SEC 调查有了实质进展；英伟达收盘回到 150 以上。

### 2026-11-21 晚间复查，无变化

周六美股休市，没有新的收盘价。英伟达周五盘后报 130.01，比收盘高 3.6%，离 119.62 更远了。Polymarket 这道题从 58% 涨到 69%，我没找到对应的新消息，也没找到 Polymarket 对超微电脑那一条的说明。BTC 当天跌到两年来的低点，市场的上涨可能反映的是整体情绪。维持 57%。

### 2026-11-24 重新预测，从 57% 降到 13%

触发了重估条件：英伟达收盘回到 150 以上。

- **发生了什么**。11 月 23 日董事会宣布黄仁勋复任 CEO，英伟达当天涨 31.5%，收 165.05，是 2003 年以来最大的单日涨幅。纳斯达克 100 当天涨约 6.8%，SOXX 收 140.22。董事会的调查还没结束，公司新设了国家安全委员会，并在招首席合规官。来源：[CNN](https://www.cnn.com/2026/11/23/markets/us-stocks-rebound-intl)、[Fortune](https://fortune.com/2026/11/23/wall-street-1-trillion-jensen-huang-nvidia-stock-market-cap/)、[24/7 Wall St.](https://247wallst.com/investing/2026/11/23/nvidia-stock-soars-27-before-the-bell-after-its-board-reinstated-jensen-huang-as-ceo-it-still-needs-50-to-get-back-to-its-record/)。
- **现状**。SOXX 在 11 月 20 日收盘时已跌过 40% 的线，这一条已经发生过，仍然算数。超微电脑那一条不变。英伟达比高点低 31.0%，要再跌 27.5% 到 119.62。
- **调整**。11 月 13 日英伟达离这条线的距离差不多（约 28%），当时我给它到年底跌破的概率 9%。现在剩 26 个交易日，时间短了一些，但波动大得多，SEC 调查也还在，我给 15%。超微电脑那一条算数的概率仍按 75%，不算数时还需要另一家腰斩，在英伟达已跌破的情形下约五成。合计 0.15 ×（0.75 + 0.25 × 0.5）≈ 13%。市场价 14%。
- **反向设想**。如果判了 Yes：SEC 调查有了实质结论，或者复职引出新的治理问题，英伟达把这周的涨幅全部吐回去，再跌一截。上周已经出现过五天跌 25% 的行情，这条路径不算远。
- **重估条件**：英伟达收盘跌破 140；SEC 调查有了实质进展；Polymarket 对超微电脑那一条给出说明。

## 复盘
