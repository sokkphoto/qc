class TrendGrid(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2021, 8, 1)
        self.SetEndDate(2021, 8, 30)
        self.SetCash(10000)
        
        self.orderQuantity = int(self.GetParameter("order-quantity"))
        self.gridSpace = float(self.GetParameter("grid-space"))
        
        self.Data = {}

        for ticker in ["EURUSD"]:
            symbol = self.AddForex(ticker , Resolution.Minute, Market.Oanda).Symbol
            self.Log('Initializing data for ' + str(symbol))
            
            emaFast = self.EMA(symbol, int(self.GetParameter("ema-fast")), Resolution.Hour)
            emaSlow = self.EMA(symbol, int(self.GetParameter("ema-slow")), Resolution.Hour)
            
            self.Data[symbol] = SymbolData(emaFast, emaSlow)
            
        warmupPeriod = int(self.GetParameter("ema-slow"))
        self.SetWarmUp(warmupPeriod, Resolution.Hour)
            
            
    def OnData(self, data):
        if self.IsWarmingUp:
            return
        
        for symbol, symData in self.Data.items():
            
            price = data[symbol].Close
            emaFast = symData.emaFast.Current.Value
            emaSlow = symData.emaSlow.Current.Value
            
            if emaFast > emaSlow:
                
                if self.Portfolio[symbol].IsShort:
                    self.Log(f'--- EMA cross, trending higher on {symbol}, closing all positions @ {price} ---')
                    self.Liquidate(symbol)
                
                # new trades long
                if not self.Portfolio[symbol].IsLong:
                    self.Log(f'Initial long with {symbol} @ {price}')
                    self.tradeLong(symbol)
                elif price < (self.Data[symbol].entry - self.gridSpace):
                    self.Log(f'Lower line hit on long {symbol} @ {price}')
                    self.tradeLong(symbol)
                    
            if emaFast < emaSlow:
                
                if self.Portfolio[symbol].IsLong:
                    self.Log(f'--- EMA cross, trending lower on {symbol}, closing all positions @ {price} ---')
                    self.Liquidate(symbol)
                
                # new trades short
                if not self.Portfolio[symbol].IsShort:
                    self.Log(f'Initial short with {symbol} @ {price}')
                    self.tradeShort(symbol)
                elif price > (self.Data[symbol].entry + self.gridSpace):
                    self.Log(f'Upper line hit on short {symbol} @ {price}')
                    self.tradeLong(symbol)
                    
                    
    def OnOrderEvent(self, orderEvent):
        order = self.Transactions.GetOrderById(orderEvent.OrderId)
        symbol = order.Symbol
        price = orderEvent.FillPrice
        
        if order.Status == OrderStatus.Filled and order.Type == OrderType.Limit:
            if orderEvent.FillQuantity < 0:
                self.Log(f'TP hit on long {symbol} @ {price}')
                self.tradeLong(symbol)
            elif orderEvent.FillQuantity > 0:
                self.Log(f'TP hit on short {symbol} @ {price}')
                self.tradeShort(symbol)
                
            
    def tradeLong(self, symbol):
        market = self.MarketOrder(symbol, self.orderQuantity)
        price = market.AverageFillPrice
        self.Data[symbol].entry = market.AverageFillPrice
        target = round(price + self.gridSpace , 5)
        self.LimitOrder(symbol, - self.orderQuantity, target)
        self.Log(f'Entered long with {symbol} @ {price} | Target @ {target}')
        
    def tradeShort(self, symbol):
        market = self.MarketOrder(symbol, - self.orderQuantity)
        price = market.AverageFillPrice
        self.Data[symbol].entry = market.AverageFillPrice
        target = round(price - self.gridSpace , 5)
        self.LimitOrder(symbol, self.orderQuantity, target)
        self.Log(f'Entered short with {symbol} @ {price} | Target @ {target}')
        
    
            
class SymbolData:
    
    def __init__(self, emaFast, emaSlow):
        self.emaFast = emaFast
        self.emaSlow = emaSlow
        