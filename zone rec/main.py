class BrownBadgerZoneRec(QCAlgorithm):

    def Initialize(self):
        
        self.SetCash(1000)
        self.SetStartDate(2020, 1, 1)
        self.SetEndDate(2021, 1, 1)
        self.pair = self.AddForex("EURUSD", Resolution.Minute, Market.Oanda).Symbol
        self.SetBrokerageModel(BrokerageName.OandaBrokerage)
        self.lotSize = self.Securities[self.pair].SymbolProperties.LotSize
        
        self.smaSlow = self.SMA(self.pair, 200, Resolution.Hour)
        self.smaFast = self.SMA(self.pair, 9, Resolution.Hour)
        self.atr = self.ATR(self.pair, 5, MovingAverageType.Simple, Resolution.Hour)
        self.RegisterIndicator(self.pair, self.atr, Resolution.Hour)
        
        self.orderQuantity = 1000
        self.maxQuantity = 16000
        #self.slPips = 60
        #self.tpPips = 30
        self.atrFactorSL = 6
        self.atrFactorTP = 3
        self.minEntryATR = 0.0020
        self.slPipsMax = 200
        self.slPipsMin = 0
        self.tpPipsMax = 200
        self.tpPipsMin = 0
        
        self.Log('Order quantity is ' + str(self.orderQuantity))
        self.tradeNum = 0
        
    def OnData(self, data):
        if not self.smaSlow.IsReady or self.pair not in data:
            return
        
        self.price = data[self.pair].Close
        
        # get direction of first pos and open
        if self.smaFast.Current.Value > self.smaSlow.Current.Value and self.price < self.smaFast.Current.Value:
            firstPosition = self.orderQuantity
        elif self.smaFast.Current.Value < self.smaSlow.Current.Value and self.price > self.smaFast.Current.Value:
            firstPosition = - self.orderQuantity
        else:
            return
        
        if not self.Portfolio.Invested and self.atr.Current.Value > self.minEntryATR:
            self.Log('First entry conditions met. Slow SMA: ' + str(self.smaSlow.Current.Value) + 
                ' | Fast SMA: ' + str(self.smaFast.Current.Value) + ' | Price: ' + str(self.price))
            #self.Log('SL pips: ' + str(self.slPips) + ' | TP pips: ' + str(self.tpPips))
            self.tradeNum = 1
            
            def limit(num, minimum, maximum):
                return max(min(num, maximum), minimum)
            
            #set SL & TP with ATR
            self.slPips = self.atr.Current.Value * self.atrFactorSL * 10000
            self.slPips = limit(self.slPips, self.slPipsMin, self.slPipsMax)
            self.tpPips = self.atr.Current.Value * self.atrFactorTP * 10000
            self.tpPips = limit(self.tpPips, self.tpPipsMin, self.tpPipsMax)
            self.Log('SL pips set to: ' + str(self.slPips) + ' | TP pips set to: ' + str(self.tpPips))
            
            first = self.newTrade(self.tradeNum, firstPosition)
            

    
    def OnOrderEvent(self, orderEvent):
        order = self.Transactions.GetOrderById(orderEvent.OrderId)
        
        if order.Status == OrderStatus.Filled:
            # if TP hit, cancel all orders
            if order.Type == OrderType.Limit:
                self.Transactions.CancelOpenOrders()
                self.Log(str(order.Type) + str(order.Tag) + ' hit at ' + str(self.price))
                self.tradeNum = 0
                
            #if SL hit, open reverse recovery at market
            elif order.Type == OrderType.StopMarket:
                self.Transactions.CancelOpenOrders()
                self.Log(str(order.Type) + str(order.Tag) + ' hit at ' + str(self.price) + '. Opening recovery.')
                
                self.tradeNum = self.tradeNum + 1
                #newTradeNum = (int(str(order.Tag).split('#', 1)[1:][0])) + 1
                #same direction as SL ! (reverse to original market)
                newPosition = order.Quantity * 2
                if not abs(newPosition) > self.maxQuantity:
                    self.Log('New recovery position: ' + str(newPosition))
                    self.newTrade(self.tradeNum, newPosition)
                else:
                    self.Log('Recovery not opened, maxQuantity reached.')
                
                
        if order.Status == OrderStatus.Canceled:
            self.Log(str(orderEvent))
    
    
    def newTrade(self, n, position):
        tradeNum = str(n)

        # new entry at market
        trade = self.MarketOrder(self.pair, position)
        self.Log('New entry at market #' + tradeNum + ' | ' + str(position) + ' @ ' + str(self.price))
        
        #update tag, not working!
        response = trade.UpdateTag(str('MKT#' + tradeNum))
        if response.IsSuccess:
            self.Log('Tag set to ' + str('MKT#' + tradeNum))
        
        # set SL and TP
        if position > 0:
            sl = self.StopMarketOrder(self.pair, - position, (self.price - (self.slPips / 10000)), (str('SL#' + tradeNum)))
            tp = self.LimitOrder(self.pair, - position, (self.price + (self.slPips / 10000)), (str('TP#' + tradeNum)))
            
        elif position < 0:
            sl = self.StopMarketOrder(self.pair, - position, (self.price + (self.slPips / 10000)), (str('SL#' + tradeNum)))
            tp = self.LimitOrder(self.pair, - position, (self.price - (self.slPips / 10000)), (str('TP#' + tradeNum)))
        self.Log('SL#' + tradeNum + ' set at ' + ' | ' + 'TP#' + tradeNum + ' set at ')
        
        return