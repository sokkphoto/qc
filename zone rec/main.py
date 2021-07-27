class GreenMuleZoneRec(QCAlgorithm):

    def Initialize(self):
        
        self.SetCash(1000)
        self.SetStartDate(2020, 1, 1)
        self.SetEndDate(2020, 1, 30)
        self.pair = self.AddForex("AUDUSD", Resolution.Minute, Market.Oanda).Symbol
        self.SetBrokerageModel(BrokerageName.OandaBrokerage)
        
        self.lotSize = self.Securities[self.pair].SymbolProperties.LotSize
        
        self.sma = self.SMA(self.pair, 200, Resolution.Hour)
        self.orderQuantity = 1000
        self.slPips = 60
        self.tpPips = 30
        
        self.Log('Quantity is ' + str(self.orderQuantity) + ' | SL pips: ' + str(self.slPips) + ' | TP pips: ' + str(self.tpPips))

        
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
            first = self.newTrade(1, firstPosition)
            

    
    def OnOrderEvent(self, orderEvent):
        order = self.Transactions.GetOrderById(orderEvent.OrderId)
        
        if order.Status == OrderStatus.Filled:
            # if TP hit, cancel all orders
            if order.Type == OrderType.Limit:
                self.Transactions.CancelOpenOrders(order.Symbol)
                self.Log(str(order.Tag) + 'hit at' + str(self.price) + '. Cancelled open orders.')
                
            #if SL hit, open reverse recovery at market
            elif order.Type == OrderType.StopMarket:
                self.Log(str(order.Tag) + 'hit at' + str(self.price) + '. Opening recovery.')
                newTradeNum = (int(str(order.Tag).split('#', 1)[1:][0])) + 1
                if order.Quantity > 0:
                    newPosition = order.Quantity * 2
                elif order.Quantity < 0:
                    newPosition = - (order.Quantity * 2)
                
                self.newTrade(newTradeNum, newPosition)
                
                
        if order.Status == OrderStatus.Canceled:
            self.Log(str(orderEvent))
    
    
    def newTrade(self, tradeNum, position):
        tradeNum = str(tradeNum)

        # new entry at market
        trade = self.MarketOrder(self.pair, position)
        self.Log('New entry at market #' + tradeNum + ' | ' + str(position) + ' @ ' + str(self.price))
        
        #update tag
        response = trade.UpdateTag(str('MKT#' + tradeNum))
        
        if response.IsSuccess:
            self.Log('Tag set to ' + str('MKT#' + tradeNum))
        
        # set SL and TP
        if position > 0:
            sl = self.StopMarketOrder(self.pair, - position, (self.price - (self.slPips / 10000)), (str('SL#' + tradeNum)))
            tp = self.LimitOrder(self.pair, - position, (self.price + (self.slPips / 10000)), (str('TP#' + tradeNum)))
            
        elif position < 0:
            sl = self.StopMarketOrder(self.pair, position, (self.price + (self.slPips / 10000)), (str('SL#' + tradeNum)))
            tp = self.LimitOrder(self.pair, position, (self.price - (self.slPips / 10000)), (str('TP#' + tradeNum)))
        self.Log('SL#' + tradeNum + 'set at ' + ' | ' + 'TP#' + tradeNum + 'set at ')
        
        return