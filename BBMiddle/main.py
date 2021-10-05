from AlgorithmImports import *

class BBMiddle(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2020, 2, 1)
        self.SetEndDate(2020, 3, 1)
        self.SetCash(10000)
        
        self.OrderQuantity = int(self.GetParameter("order-quantity"))
        
        self.Data = {}

        for ticker in ["EURUSD"]:
           symbol = self.AddForex(ticker , Resolution.Hour).Symbol
           self.Log('Initializing data for ' + str(symbol))
           
           self.Data[symbol] = SymbolData(
               self.BB(symbol, int(self.GetParameter("bb-period")), float(self.GetParameter("bb-stddev")), Resolution.Hour),
               self.ATR(symbol, int(self.GetParameter("atr-period")), MovingAverageType.Simple, Resolution.Hour))
        
        warmupPeriod = max(int(self.GetParameter("bb-period")), int(self.GetParameter("atr-period")))
        self.SetWarmUp(warmupPeriod, Resolution.Hour)


    def OnData(self, data):
        if self.IsWarmingUp:
            return
        
        for symbol, symData in self.Data.items():
            upper = symData.bb.UpperBand.Current.Value
            mid = symData.bb.MiddleBand.Current.Value
            lower = symData.bb.LowerBand.Current.Value
            atr = symData.atr.Current.Value
            
            price = data[symbol].Close
            
            # entry on passing upper/lower band. exit on passing middle.
            # fade entry by adding to position if entry passed by x times ATR
            if not self.Portfolio[symbol].Invested:
                if price < lower:
                    self.Log(f"Entering long with {symbol}")
                    self.MarketOrder(symbol, self.OrderQuantity)
                    symData.entry = price
                elif price > upper:
                    self.Log(f"Entering short with {symbol}")
                    self.MarketOrder(symbol, -self.OrderQuantity)
                    symData.entry = price
                    
            elif self.Portfolio[symbol].IsLong:
                if price > mid:
                    self.Log(f"Mid band passed, closing {symbol}")
                    self.Liquidate(symbol)
                    symData.entry = None
                elif price < (symData.entry - (2 *atr)) and abs(self.Portfolio[symbol].Quantity) <= self.OrderQuantity:
                    self.Debug(f"Fading {symbol}, adding to long")
                    self.MarketOrder(symbol, self.OrderQuantity)
                    
            elif self.Portfolio[symbol].IsShort:
                if price < mid:
                    self.Log(f"Mid band passed, closing {symbol}")
                    self.Liquidate(symbol)
                    symData.entry = None
                elif price > (symData.entry + (2 *atr)) and abs(self.Portfolio[symbol].Quantity) <= self.OrderQuantity:
                    self.Debug(f"Fading {symbol}, adding to short")
                    self.MarketOrder(symbol, -self.OrderQuantity)
                    
                    
                
class SymbolData:
    
    def __init__(self, bb, atr):
        self.bb = bb
        self.atr = atr