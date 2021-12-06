# BB 1h
use BB (20) and emaSlow (100)
start grid (long):
if BBmid > emaSlow and price < BBlower

close grid:
if BBmid < emaSlow


## Technical - To Do

- bug - if pair has Resolution.Minute, indi values are off.
-- use x60 MA value for BB

## Analysis

- test with different profit-targets
- opt: pairs, gridspace; walk winning pairs 2017-2019
- review charts of winning pairs for best ema, bb, stddev
