class TrendGrid(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2021, 2, 1)
        self.SetEndDate(2021, 3, 30)
        self.SetCash(10000)
        
        self.orderQuantity = int(self.GetParameter("order-quantity"))
        self.gridSpace = float(self.GetParameter("grid-space"))
        self.SetBrokerageModel(BrokerageName.OandaBrokerage)
        
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
                    self.closeAll(symbol)
                
                # new trades long
                if not self.Portfolio[symbol].IsLong:
                    self.Log(f'Initial long with {symbol} @ {price}')
                    self.tradeLong(symbol)
                elif price < symData.prevLine:
                    self.Log(f'Lower line hit on long {symbol} @ {price}')
                    if self.checkEntries(price, symData.openEntries) == None:
                        self.tradeLong(symbol)
                    
            if emaFast < emaSlow:
                
                if self.Portfolio[symbol].IsLong:
                    self.Log(f'--- EMA cross, trending lower on {symbol}, closing all positions @ {price} ---')
                    self.closeAll(symbol)
                
                # new trades short
                if not self.Portfolio[symbol].IsShort:
                    self.Log(f'Initial short with {symbol} @ {price}')
                    self.tradeShort(symbol)
                elif price > symData.prevLine:
                    self.Log(f'Upper line hit on short {symbol} @ {price}')
                    if self.checkEntries(price, symData.openEntries) == None:
                        self.tradeShort(symbol)
                    
                    
    def OnOrderEvent(self, orderEvent):
        order = self.Transactions.GetOrderById(orderEvent.OrderId)
        symbol = order.Symbol
        price = orderEvent.FillPrice
        
        if order.Status == OrderStatus.Filled and order.Type == OrderType.Limit:
            if orderEvent.FillQuantity < 0:
                self.Log(f'TP hit on long {symbol} @ {price}')
                
                #delete original entry from openEntries
                originalEntryPrice = price - self.gridSpace
                originalEntry = self.checkEntries(originalEntryPrice, self.Data[symbol].openEntries)
                if originalEntry != None:
                    self.Data[symbol].openEntries.remove(originalEntry)
                    
                entriesCurrentPrice = self.checkEntries(price, self.Data[symbol].openEntries)
                if entriesCurrentPrice == None:
                    self.tradeLong(symbol)
                else:
                    self.Log(f'Open entry already at {entriesCurrentPrice}')

            elif orderEvent.FillQuantity > 0:
                self.Log(f'TP hit on short {symbol} @ {price}')
                
                #delete original entry from openEntries
                originalEntryPrice = price + self.gridSpace
                originalEntry = self.checkEntries(originalEntryPrice, self.Data[symbol].openEntries)
                if originalEntry != None:
                    self.Data[symbol].openEntries.remove(originalEntry)
                    
                entriesCurrentPrice = self.checkEntries(price, self.Data[symbol].openEntries)
                if entriesCurrentPrice == None:
                    self.tradeShort(symbol)
                else:
                    self.Log(f'Open entry already at {entriesCurrentPrice}')
                
            
    def tradeLong(self, symbol):
        market = self.MarketOrder(symbol, self.orderQuantity)
        price = market.AverageFillPrice
        # price = self.Securities[symbol].Price
        self.Data[symbol].entry = price
        target = round(price + self.gridSpace , 5)
        self.LimitOrder(symbol, - self.orderQuantity, target)
        self.Log(f'Entered long with {symbol} @ {price} | Target @ {target}')

        self.Data[symbol].entry = price
        self.Data[symbol].target = target
        self.Data[symbol].prevLine = price - self.gridSpace
        self.Data[symbol].openEntries.append(price)
        
    def tradeShort(self, symbol):
        market = self.MarketOrder(symbol, - self.orderQuantity)
        price = market.AverageFillPrice
        self.Data[symbol].entry = price
        target = round(price - self.gridSpace , 5)
        self.LimitOrder(symbol, self.orderQuantity, target)
        self.Log(f'Entered short with {symbol} @ {price} | Target @ {target}')

        self.Data[symbol].entry = price
        self.Data[symbol].target = target
        self.Data[symbol].prevLine = price + self.gridSpace
        self.Data[symbol].openEntries.append(price)

    def closeAll(self, symbol):
        self.Liquidate(symbol)
        self.Transactions.CancelOpenOrders(symbol)

        self.Data[symbol].entry = None
        self.Data[symbol].target = None
        self.Data[symbol].prevLine = None
        self.Data[symbol].openEntries = []

    def checkEntries(self, price, openlist):
        self.Log(f'Currently open: {openlist}')
        result = None
        for i in range(len(openlist)):
            if openlist[i] < (price + (0.5 * self.gridSpace)) and openlist[i] > (price - (0.5 * self.gridSpace)):
                result = openlist[i]
        return result
        
    
            
class SymbolData:
    
    def __init__(self, emaFast, emaSlow):
        self.emaFast = emaFast
        self.emaSlow = emaSlow
        self.openEntries = []
        