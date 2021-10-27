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
looks good! ema-slow: 500, grid-space: 20, profit-target-pips: 120
if price > emaSlow: long




-------
- try: trade to revert to slow EMA
