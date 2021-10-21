# Strat
- check trend with EMAs
- if fast EMA > slow, open long,
- tp at x pips on next grid level. open next long.
- if price on lower grid level, open new long
- if trend reverses, liquidate all, cancel all open orders.

# To do

+ store list of openEntries with each short & long

+ added max-open

- try: liquidate if maxOpenTrades reached
if trend reverses, open new grid

- try: liquidate if in profit by n pips