## TrendGrid MRtoEMA

use unrealized PL & maxopen to limit trades
2MA + price for entry: if fast > slow and price > fast: enter short
or 1 MA + price
profit target


## To Do

- test grid direction (eurchf, only short, 2021)

- test - grid direction on 2021-04-06 (ema's)
- test - why entry with gridspace + price -> worse perf

+ fix total PL calc

+ entry - n x ATR above/below fast EMA. try with 2x

+ remove pip conversions for JPY, HUF, INR
+ profit-target and unrealized-pl-stop to use ATR units

- entry filter - if 30 day high/low reached in last x hours, no entry


+ add dynamic profit target based on distance from VSlow, review charts
- add param for entry condition - distance from VSlow, review charts

- opt unrealizedPL (EURCHF)
- run volatility check for 2020-21 again
- opt to get best pairs
-- 
