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

- bug - EURHUF - too many open trades at same level opened, grid not calculated correctly


+ create simple version:
new grid direction on EMA cross (consider ranging conditions)
no profit target?


- use emaMid for trend confirmation ?
review charts

- try: early exit if totalPL > (profitTargetPips / 2)



-------
+ indi to measure?
https://www.elearnmarkets.com/blog/know-5-important-volatility-indicators

+ to backtest - get approx longest grid periods for different pairs? EURCHF, EURGBP, GBPUSD, GBPJPY, AUDJPY -> avg between 78-573; max between 330-1897
- get min, max, average time to TP 

+ get pairs with best short term range / long term range ratio (for mean reversion)
+ get pairs with best longterm range (for trend) -> get range according to grid period

- mean reversion methods? trade to revert to slow EMA?
- signals for trending pairs? supertrend? MACD

-----

- cli backtest

Hi all,

Following the examples at https://www.quantconnect.com/forum/discussion/10658/how-to-run-a-backtest-over-multiple-forex-pairs/p1
attempting to set up an algo to work with multiple forex pairs.

Turns out Lean CLI does not like the way the algo tries to 

        for ticker in ["NZDUSD","EURUSD"]:
           symbol = self.AddForex(ticker , Resolution.Hour).Symbol
           self.Log('Initializing data for ' + str(symbol))
           self.Data[symbol] = SymbolData(
                self.EMA(symbol, int(self.GetParameter("ema-fast")), Resolution.Hour),
                self.EMA(symbol, emaSpeedMid, Resolution.Hour),
                self.EMA(symbol, emaSpeedSlow, Resolution.Hour),
                self.ATR(symbol, int(self.GetParameter("atr")), MovingAverageType.Simple, Resolution.Hour),
                self.ADX(symbol, int(self.GetParameter("adx-period")), Resolution.Hour))

This results in an error:

20210912 13:07:06.180 ERROR:: During the algorithm initialization, the following exception has occurred: 
ApiDataProvider(): Must be subscribed to map and factor files to use the ApiDataProviderto download Equity data from 
QuantConnect. in ApiDataProvider.cs:line 220 ApiDataProvider(): Must be subscribed to map and factor files to use the 
ApiDataProviderto download Equity data from QuantConnect.