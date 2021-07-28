class GreenMuleZoneRec(QCAlgorithm):

    def Initialize(self):
        
        self.SetCash(1000)
        self.SetStartDate(2020, 1, 1)
        self.SetEndDate(2021, 1, 1)
        self.pair = self.AddForex("AUDUSD", Resolution.Minute, Market.Oanda).Symbol
        self.SetBrokerageModel(BrokerageName.OandaBrokerage)
        
        self.lotSize = self.Securities[self.pair].SymbolProperties.LotSize
        
        self.sma = self.SMA(self.pair, 200, Resolution.Hour)
        self.orderQuantity = 1000
        self.maxQuantity = 16000
        self.slPips = 60
        self.tpPips = 30
        
        self.Log('Quantity is ' + str(self.orderQuantity) + ' | SL pips: ' + str(self.slPips) + ' | TP pips: ' + str(self.tpPips))
        self.tradeNum = 0
        
    def OnData(self, data):
        if not self.sma.IsReady or self.pair not in data:
            return
        
        self.price = data[self.pair].Close
        
        # get direction of first pos and open
        if self.price > self.sma.Current.Value:
            firstPosition = self.orderQuantity
        elif self.price < self.sma.Current.Value:
            firstPosition = - self.orderQuantity
        
        if not self.Portfolio.Invested:
            self.tradeNum = 1
            first = self.newTrade(self.tradeNum, firstPosition)
            

    
    def OnOrderEvent(self, orderEvent):
        order = self.Transactions.GetOrderById(orderEvent.OrderId)
        
        if order.Status == OrderStatus.Filled:
            # if TP hit, cancel all orders
            if order.Type == OrderType.Limit:
                self.Transactions.CancelOpenOrders()
                self.Log(str(order.Type) + str(order.Tag) + 'hit at' + str(self.price))
                self.tradeNum = 0
                
            #if SL hit, open reverse recovery at market
            elif order.Type == OrderType.StopMarket:
                self.Transactions.CancelOpenOrders()
                self.Log(str(order.Type) + str(order.Tag) + 'hit at' + str(self.price) + '. Opening recovery.')
                
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
        self.Log('SL#' + tradeNum + 'set at ' + ' | ' + 'TP#' + tradeNum + 'set at ')
        
        return