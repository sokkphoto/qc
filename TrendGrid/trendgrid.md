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

- pairs with best volatility? indi to measure?

- use emaMid for trend confirmation ?
review charts

- try: early exit if totalPL > (profitTargetPips / 2)

+ calc general grid ranges to optimize unrealized PL stop
setting to -1000



-------
- try: trade to revert to slow EMA
