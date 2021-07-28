## To Do

+ SL, TP direction fix
+ log TP & SL hit, 
+ store tradeNum in var + tag
+ reset tradeNum if TP hit

+ #2 opened at -2000 if #1 is -1000
+ tradeNum/maxQuantity piiraja

+ better first entry - MA cross, price below fast MA
- get ATR working for SL, TP
- better recovery entry - price below fast MA

- OnOrderEvent - logida fill price, mitte praegune market
- parameetrid
- populate indi values to start right after init
- new entry update tag not working
- SL & TP orderid - log stop, limit price


# Open questions

- how to get fill price for orders? AverageFillPrice for ticket no works.
https://www.quantconnect.com/docs/algorithm-reference/trading-and-orders
https://www.quantconnect.com/docs/algorithm-reference/trading-and-orders#Trading-and-Orders-Updating-Orders
OrderTicket

- 

## Strat
- review price chart where maxQuantity reached. 
- initial entry - use ATR for volatility to set SL, TP ?
- direction reset (based on indis) after 2 reco's ?
- reduce sl & tp pips by x% with each reco ?