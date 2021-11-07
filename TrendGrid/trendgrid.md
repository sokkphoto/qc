# Strat
- check trend with EMAs
- if fast EMA > slow, open long,
- tp at x pips on next grid level. open next long.
- if price on lower grid level, open new long
- if trend reverses, liquidate all, cancel all open orders.

# To do

+ store list of openEntries with each short & long

+ added max-open param

-------
+ try: liquidate if in profit by n $
https://www.quantconnect.com/docs/algorithm-reference/securities-and-portfolio

+ 21-10-25 use unrealizedProfit target before closeAll

+ 27-10-25 add condition to exit early if trend reverses.
if trend reversed & totalPL > 0: closeAll
+ added ATR multiplier for gridspace

+ for JPY pairs - convert target & stop to multiple of gridSpace


- use emaMid for trend confirmation ?
review charts

- try: early exit if totalPL > (profitTargetPips / 2)



-------
+ indi to measure?
https://www.elearnmarkets.com/blog/know-5-important-volatility-indicators

+ to backtest - get approx longest grid periods for different pairs? EURCHF, EURGBP, GBPUSD, GBPJPY, AUDJPY -> avg between 78-573; max between 330-1897
- get min, max, average time to TP 

- get pairs with best short term range / long term range ratio (for mean reversion)
- get pairs with best longterm range (for trend) -> get range according to grid period

- mean reversion methods? trade to revert to slow EMA?
- signals for trending pairs? supertrend? MACD