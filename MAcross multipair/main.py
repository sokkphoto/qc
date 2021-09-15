class MAMultiPair(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2020, 1, 1)
        self.SetEndDate(2020, 4, 1)
        self.SetCash(10000)
        
        emaFactor = float(self.GetParameter("ema-speed-factor"))
        emaSpeedMid = round((int(self.GetParameter("ema-fast"))) * emaFactor)
        emaSpeedSlow = round((int(self.GetParameter("ema-fast"))) * emaFactor * emaFactor)

        self.Data = {}

        for ticker in ["NZDUSD","EURUSD"]:
           symbol = self.AddForex(ticker , Resolution.Hour).Symbol
           self.Log('Initializing data for ' + str(symbol))
           self.Data[symbol] = SymbolData(
                self.EMA(symbol, int(self.GetParameter("ema-fast")), Resolution.Hour),
                self.EMA(symbol, emaSpeedMid, Resolution.Hour),
                self.EMA(symbol, emaSpeedSlow, Resolution.Hour),
                self.ATR(symbol, int(self.GetParameter("atr")), MovingAverageType.Simple, Resolution.Hour),
                self.ADX(symbol, int(self.GetParameter("adx-period")), Resolution.Hour))
            
        
        self.Log('** EMAs ** Fast: ' + str(self.GetParameter("ema-fast")) + ' Mid: ' + str(emaSpeedMid) + ' Slow: ' + str(emaSpeedSlow))

        self.orderQuantity = int(self.GetParameter("order-quantity"))
        self.atrFactorSL = float(self.GetParameter("atr-factor-sl"))
        self.atrFactorTP = float(self.GetParameter("atr-factor-tp"))
        self.slPipsMax = int(self.GetParameter("slpips-max"))
        self.slPipsMin = int(self.GetParameter("slpips-min"))
        self.tpPipsMax = int(self.GetParameter("tppips-max"))
        self.tpPipsMin = int(self.GetParameter("tppips-min"))
        self.adxMin = int(self.GetParameter("adx-min"))

        self.SetWarmUp(203, Resolution.Hour)


    def OnData(self, data):
        if self.IsWarmingUp:
            return

        for symbol, symbolData in self.Data.items():
            
            fast = symbolData.fast.Current.Value
            mid = symbolData.mid.Current.Value
            slow = symbolData.slow.Current.Value
            atr = symbolData.atr.Current.Value
            adx = symbolData.adx.Current.Value
            price = data[symbol].Close
            # validCross = self.checkValidCross(fast, mid, slow, atr)
            
            # check entry conditions
            if (price < fast and
                    fast > mid and fast > slow and 
                    # validCross == 1 and
                    adx > self.adxMin):
                position = self.orderQuantity
            elif (price > fast and
                    fast < mid and fast < slow and
                    # validCross == -1 and
                    adx > self.adxMin):
                position = - self.orderQuantity
            else: 
                return
            
            if not self.Portfolio[symbol].Invested:
                self.Log(str(symbol) + ' Entry conditions met. Slow SMA: ' + str(round(slow, 5)) + ' | Mid SMA: ' + str(round(mid, 5)) +
                    ' | Fast SMA: ' + str(round(fast, 5)) +' | Price: ' + str(round(price, 5)))
                self.Log('ADX: ' + str(adx))
                
                # store cross direction
                #crossAtEntry = validCross
                
                self.Log('Position: ' + str(position))
                
                trade = self.newTrade(position, symbol, price)
            
                
                
    
    def checkValidCross(self, fast, mid, slow, atr):
        if (fast > mid and 
                fast > slow and 
                abs(fast - mid) < (atr * 0.5)):
            if self.validCross != 1:
                self.validCross = 1
                self.Log('Crossed up')
        elif (fast < mid and 
            fast < slow and 
            abs(fast - mid) < (atr * 0.5)):
            if self.validCross != -1:
                self.validCross = -1
                self.Log('Crossed down')
        else:
            self.validCross = 0
        return self.validCross
        
        
    def newTrade(self, position, symbol, price):
        trade = self.MarketOrder(symbol, position)
        self.Log('New entry at market: ' + str(symbol) + ' ' + str(position) + ' @ ' + str(price))
        
        # TO DO - set based on ATR    
        """
        def limit(self, num, minimum, maximum):
            return max(min(num, maximum), minimum)
    
        # set SL and TP based on ATR
        def slPips(self):
            pips = self.atr.Current.Value * self.atrFactorSL * 10000
            pips = self.limit(self.slPips, self.slPipsMin, self.slPipsMax)
            return pips
        
        def tpPips(self):
            pips = self.atr.Current.Value * self.atrFactorTP * 10000
            pips = self.limit(self.tpPips, self.tpPipsMin, self.tpPipsMax)
            return pips
        """
        # set SL and TP
        slDistance = 0.0050
        tpDistance = 0.0100
        
        if position > 0:
            sl = self.StopMarketOrder(symbol, - position, round((price - slDistance), 5))
            tp = self.LimitOrder(symbol, - position, round((price + tpDistance), 5))
            
        elif position < 0:
            sl = self.StopMarketOrder(symbol, - position, round((price + slDistance), 5))
            tp = self.LimitOrder(symbol, - position, round((price - tpDistance), 5))
        self.Log('SL set at ' + str(sl.Get(OrderField.StopPrice)) + ' | ' + 'TP set at ' + str(tp.Get(OrderField.LimitPrice)))
        return
    
    
    
    def OnOrderEvent(self, orderEvent):
        order = self.Transactions.GetOrderById(orderEvent.OrderId)
        
        if order.Status == OrderStatus.Filled:
            # if TP hit, cancel all orders
            if order.Type == OrderType.Limit:
                self.Log(str(order.Symbol) + ' TP hit at ' + str(orderEvent.FillPrice))
                self.Transactions.CancelOpenOrders(order.Symbol)
                
                # self.tradeNum = 0
                
            #if SL hit, open reverse recovery at market
            elif order.Type == OrderType.StopMarket:
                self.Log(str(order.Symbol) + ' SL hit at ' + str(orderEvent.FillPrice))
                self.Transactions.CancelOpenOrders(order.Symbol)
                
                
                
        if order.Status == OrderStatus.Canceled:
            self.Log(str(orderEvent))
                
    

class SymbolData:
    
    def __init__(self, fast, mid, slow, atr, adx):
        self.fast = fast
        self.mid = mid
        self.slow = slow
        self.atr = atr
        self.adx = adx
        