class TrendGrid(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2021, 1, 1)
        self.SetEndDate(2021, 3, 1)
        self.SetCash(10000)
        
        self.orderQuantity = int(self.GetParameter("order-quantity"))
        self.gridSpaceAtr = float(self.GetParameter("grid-space-atr"))
        self.maxOpen = int(self.GetParameter("max-open"))
        self.profitTargetPips = int(self.GetParameter("profit-target-pips"))
        self.unrealizedPLStop = int(self.GetParameter("unrealized-pl-stop"))
        self.emaFast = int(self.GetParameter("ema-fast"))
        self.emaSlow = int(self.GetParameter("ema-slow"))
        self.atrPeriod = self.emaSlow / 2

        self.SetBrokerageModel(BrokerageName.OandaBrokerage)

        self.Log('--- PARAMS ---')
        self.Log(f'grid-space-atr: {self.gridSpaceAtr} | profit-target-pips: {self.profitTargetPips} | max-open: {self.maxOpen} | ema-fast: {self.emaFast} | ema-slow: {self.emaSlow}')

        self.Data = {}

        for ticker in ["EURUSD"]:
            symbol = self.AddForex(ticker , Resolution.Minute, Market.Oanda).Symbol
            self.Log('Initializing data for ' + str(symbol))

            emaFast = self.EMA(symbol, self.emaFast, Resolution.Hour)
            emaSlow = self.EMA(symbol, self.emaSlow, Resolution.Hour)
            atr = self.ATR(symbol, int(self.atrPeriod), MovingAverageType.Simple, Resolution.Hour)
            
            self.Data[symbol] = SymbolData(emaFast, emaSlow, atr)
            
        warmupPeriod = int(self.GetParameter("ema-slow"))
        self.SetWarmUp(warmupPeriod, Resolution.Hour)
            
            
    def OnData(self, data):
        if self.IsWarmingUp:
            return
        
        for symbol, symData in self.Data.items():
            
            price = data[symbol].Close
            emaFast = symData.emaFast.Current.Value
            emaSlow = symData.emaSlow.Current.Value
            
            
            if self.Portfolio[symbol].IsLong:
                unrealizedPL = self.unrealizedPL(price, symData.openEntries, 1)
                totalPL = unrealizedPL + self.realizedPL(symbol, symData.tpCount)
                
                if totalPL >= self.profitTargetPips or unrealizedPL < self.unrealizedPLStop:
                    self.Log(f'--- Profit target / PL stop reached on long {symbol}, total PL: {totalPL} ---')
                    self.closeAll(symbol)
                # early exit
                elif emaFast < emaSlow and unrealizedPL > 0:
                    self.Log(f'Trend reversed. Unrealized: {unrealizedPL}')
                    self.closeAll(symbol)
                elif price < symData.prevLine:
                    self.Log(f'Lower line hit on long {symbol} @ {price}')
                    self.Log(f'Total PL: {totalPL} | Open: {symData.openEntries}')
                    if self.checkEntries(symbol, price, symData.openEntries) == None:
                        self.tradeLong(symbol)

            if self.Portfolio[symbol].IsShort:
                unrealizedPL = self.unrealizedPL(price, symData.openEntries, -1)
                totalPL = unrealizedPL + self.realizedPL(symbol, symData.tpCount)
                
                if totalPL >= self.profitTargetPips or unrealizedPL < self.unrealizedPLStop:
                    self.Log(f'--- Profit target / PL stop reached on short {symbol}, total PL: {totalPL} ---')
                    self.closeAll(symbol)
                # early exit
                elif emaFast > emaSlow and unrealizedPL > 0:
                    self.Log(f'Trend reversed. Unrealized: {unrealizedPL}')
                    self.closeAll(symbol)
                elif price > symData.prevLine:
                    self.Log(f'Upper line hit on short {symbol} @ {price}')
                    self.Log(f'Total PL: {totalPL} | Open: {symData.openEntries}')
                    if self.checkEntries(symbol, price, symData.openEntries) == None:
                        self.tradeShort(symbol)
                        
            if not self.Portfolio[symbol].Invested:
                if emaFast > emaSlow and price < emaFast:
                    symData.gridSpace = symData.atr.Current.Value * self.gridSpaceAtr
                    self.Log(f'Initial long with {symbol} @ {price} | Grid spacing: {symData.gridSpace}')
                    self.tradeLong(symbol)
                elif emaFast < emaSlow and price > emaFast:
                    symData.gridSpace = symData.atr.Current.Value * self.gridSpaceAtr
                    self.Log(f'Initial short with {symbol} @ {price} | Grid spacing: {symData.gridSpace}')
                    self.tradeShort(symbol)
                    

                    
    def OnOrderEvent(self, orderEvent):
        order = self.Transactions.GetOrderById(orderEvent.OrderId)
        symbol = order.Symbol
        price = orderEvent.FillPrice
        
        if order.Status == OrderStatus.Filled and order.Type == OrderType.Limit:
            if orderEvent.FillQuantity < 0:
                self.Log(f'TP hit on long {symbol} @ {price}')
                self.Data[symbol].tpCount += 1
                
                #delete original entry from openEntries
                originalEntryPrice = price - self.Data[symbol].gridSpace
                originalEntry = self.checkEntries(symbol, originalEntryPrice, self.Data[symbol].openEntries)
                if originalEntry != None:
                    self.Data[symbol].openEntries.remove(originalEntry)

                entriesCurrentPrice = self.checkEntries(symbol, price, self.Data[symbol].openEntries)
                if entriesCurrentPrice == None:
                    self.Log(f'Currently open trades: {self.Data[symbol].openEntries}')
                    self.Log(f'Opening long on {symbol} @ {price}')
                    self.tradeLong(symbol)
                else:
                    self.Log(f'Open entry already at {entriesCurrentPrice}')


            elif orderEvent.FillQuantity > 0:
                self.Log(f'TP hit on short {symbol} @ {price}')
                self.Data[symbol].tpCount += 1
                
                #delete original entry from openEntries
                originalEntryPrice = price + self.Data[symbol].gridSpace
                originalEntry = self.checkEntries(symbol, originalEntryPrice, self.Data[symbol].openEntries)
                if originalEntry != None:
                    self.Data[symbol].openEntries.remove(originalEntry)

                entriesCurrentPrice = self.checkEntries(symbol, price, self.Data[symbol].openEntries)
                if entriesCurrentPrice == None:
                    self.Log(f'Currently open trades: {self.Data[symbol].openEntries}')
                    self.Log(f'Opening short on {symbol} @ {price}')
                    self.tradeShort(symbol)
                else:
                    self.Log(f'Open entry already at {entriesCurrentPrice}')
                
            
    def tradeLong(self, symbol):
        if len(self.Data[symbol].openEntries) >= self.maxOpen:
            self.Log('Max open trades reached!')
            return

        market = self.MarketOrder(symbol, self.orderQuantity)
        price = market.AverageFillPrice
        # price = self.Securities[symbol].Price
        self.Data[symbol].entry = price
        target = round(price + self.Data[symbol].gridSpace , 5)
        self.LimitOrder(symbol, - self.orderQuantity, target)

        self.Data[symbol].entry = price
        self.Data[symbol].prevLine = price - self.Data[symbol].gridSpace
        self.Data[symbol].openEntries.append(price)
        
    def tradeShort(self, symbol):
        if len(self.Data[symbol].openEntries) >= self.maxOpen:
            self.Log('Max open trades reached!')
            return

        market = self.MarketOrder(symbol, - self.orderQuantity)
        price = market.AverageFillPrice
        self.Data[symbol].entry = price
        target = round(price - self.Data[symbol].gridSpace , 5)
        self.LimitOrder(symbol, self.orderQuantity, target)

        self.Data[symbol].entry = price
        self.Data[symbol].prevLine = price + self.Data[symbol].gridSpace
        self.Data[symbol].openEntries.append(price)

    def closeAll(self, symbol):
        self.Liquidate(symbol)
        self.Transactions.CancelOpenOrders(symbol)

        self.Data[symbol].entry = None
        self.Data[symbol].prevLine = None
        self.Data[symbol].openEntries = []
        self.Data[symbol].tpCount = 0

    def checkEntries(self, symbol, price, openlist):
        result = None
        for i in range(len(openlist)):
            if openlist[i] < (price + (0.5 * self.Data[symbol].gridSpace)) and openlist[i] > (price - (0.5 * self.Data[symbol].gridSpace)):
                result = openlist[i]
        return result

    def unrealizedPL(self, price, openlist, direction):
        unrealized = 0
        for i in range(len(openlist)):
            if direction > 0:
                unrealized += price - openlist[i]
            elif direction < 0:
                unrealized += openlist[i] - price
        return round(unrealized * 10000)

    def realizedPL(self, symbol, tpcount):
        return round(tpcount * self.Data[symbol].gridSpace * 10000)
        
    
            
class SymbolData:
    
    def __init__(self, emaFast, emaSlow, atr):
        self.emaFast = emaFast
        self.emaSlow = emaSlow
        self.atr = atr
        self.openEntries = []
        self.tpCount = 0

        