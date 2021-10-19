from AlgorithmImports import *
from System.Drawing import Color

class BBExtremes(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2021, 1, 1)
        self.SetEndDate(2021, 2, 1)
        self.SetCash(10000)
        
        self.OrderQuantity = int(self.GetParameter("order-quantity"))
        
        self.Data = {}

        for ticker in ["AUDNZD"]:
            symbol = self.AddForex(ticker , Resolution.Hour, Market.Oanda).Symbol
            
            self.Log('Initializing data for ' + str(symbol))
            
            bb = self.BB(symbol, int(self.GetParameter("bb-period")), float(self.GetParameter("bb-stddev")), Resolution.Hour)
            self.RegisterIndicator(symbol, bb, Resolution.Hour)
            atr = self.ATR(symbol, int(self.GetParameter("atr-period")), MovingAverageType.Simple, Resolution.Hour)
            self.RegisterIndicator(symbol, atr, Resolution.Hour)
            ema = self.EMA(symbol, int(self.GetParameter("ema-period")), Resolution.Hour)
            self.RegisterIndicator(symbol, ema, Resolution.Hour)
           
            self.Data[symbol] = SymbolData(bb, atr, ema)
           

        
        warmupPeriod = max(int(self.GetParameter("bb-period")), int(self.GetParameter("atr-period")), int(self.GetParameter("ema-period")))
        self.SetWarmUp(warmupPeriod, Resolution.Hour)
        
        stockPlot = Chart('Trade Plot')
        stockPlot.AddSeries(Series('Buy', SeriesType.Scatter, '$', 
                            Color.Green, ScatterMarkerSymbol.Triangle))
        stockPlot.AddSeries(Series('Sell', SeriesType.Scatter, '$', 
                            Color.Red, ScatterMarkerSymbol.TriangleDown))
        stockPlot.AddSeries(Series('Liquidate', SeriesType.Scatter, '$', 
                            Color.Blue, ScatterMarkerSymbol.Diamond))
        self.AddChart(stockPlot)


    def OnData(self, data):
        if self.IsWarmingUp:
            return
        
        for symbol, symData in self.Data.items():
            upper = symData.bb.UpperBand.Current.Value
            mid = symData.bb.MiddleBand.Current.Value
            lower = symData.bb.LowerBand.Current.Value
            atr = symData.atr.Current.Value
            ema = symData.ema.Current.Value
            
            price = data[symbol].Close
            priceHi = data[symbol].High
            priceLo = data[symbol].Low
            slDistance = symData.atr.Current.Value * 2
            
            self.Plot("Trade Plot", "Price", price)
            self.Plot("Trade Plot", "MiddleBand", mid)
            self.Plot("Trade Plot", "UpperBand", upper)
            self.Plot("Trade Plot", "LowerBand", lower)
            self.Plot("Trade Plot", "EMA", ema)
            
            # check conditions & enter
            # bounce between BB, follow trend with mid & EMA
            # short: if close > upper and mid < EMA, wait for close < upper, then enter short
            # sl x times atr above upper/lower
            # exit: same as entry on reverse band
            if not self.Portfolio[symbol].Invested:
                if price < lower and mid > ema:
                    symData.bandPassedEntry = True
                    self.Log(f"Entry condition - lower band passed on {symbol} @ {price}")
                    self.Log(f"Lower {lower} | Upper {upper} | EMA {ema}")
                    
                elif (price > lower and price < mid and mid > ema and symData.bandPassedEntry == True) or (priceLo < lower and price > lower and mid > ema):
                    self.Log(f"Entering long with {symbol} @ {price}")
                    self.MarketOrder(symbol, self.OrderQuantity)
                    slPrice = round((lower - slDistance), 5)
                    sl = self.StopMarketOrder(symbol, - self.OrderQuantity, slPrice)
                    self.Log(f"Stop set at {slPrice}")
                    symData.bandPassedEntry = False
                    
                elif price > upper and mid < ema:
                    symData.bandPassedEntry = True
                    self.Log(f"Entry condition - upper band passed on {symbol} @ {price}")
                
                elif (price < upper and price > mid and mid < ema and symData.bandPassedEntry == True) or (priceHi > upper and price < upper and mid < ema):
                    self.Log(f"Entering short with {symbol} @ {price}")
                    self.MarketOrder(symbol, -self.OrderQuantity)
                    slPrice = round((upper + slDistance), 5)
                    sl = self.StopMarketOrder(symbol, self.OrderQuantity, slPrice)
                    self.Log(f"Stop set at {slPrice}")
                    symData.bandPassedEntry = False
                    
            elif self.Portfolio[symbol].IsLong:
                if price > upper:
                    symData.bandPassed = True
                    self.Log(f"Upper band passed on {symbol} @ {price}")
                    
                elif price < upper and symData.bandPassed == True:
                    self.Liquidate(symbol)
                    symData.bandPassed = False
                    symData.bandPassedEntry = False
                    self.Log(f"Back below upper on {symbol} @ {price}, closing.")
                    self.Transactions.CancelOpenOrders(symbol)
            
            elif self.Portfolio[symbol].IsShort:
                if price < lower:
                    symData.bandPassed = True
                    self.Log(f"Lower band passed on {symbol} @ {price}")
                    
                elif price > lower and symData.bandPassed == True:
                    self.Liquidate(symbol)
                    symData.bandPassed = False
                    symData.bandPassedEntry = False
                    self.Log(f"Back above lower on {symbol} @ {price}, closing.")
                    self.Transactions.CancelOpenOrders(symbol)
                    
    
    def OnOrderEvent(self, orderEvent):
        order = self.Transactions.GetOrderById(orderEvent.OrderId)
        
        if order.Status == OrderStatus.Filled:
            if order.Type == OrderType.StopMarket:
                self.Log(f"SL hit on {order.Symbol} @ {orderEvent.FillPrice}")
                
                

class SymbolData:
    
    def __init__(self, bb, atr, ema):
        self.bb = bb
        self.atr = atr
        self.ema = ema
        self.bandPassed = None
        self.bandPassedEntry = None