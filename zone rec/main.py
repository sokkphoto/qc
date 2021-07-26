class GreenMuleZoneRec(QCAlgorithm):

    def Initialize(self):
        
        self.SetCash(1000)
        self.SetStartDate(2017, 5, 1)
        self.SetEndDate(2017, 5, 15)
        self.pair = self.AddForex("AUDUSD", Resolution.Hour, Market.Oanda).Symbol
        self.SetBrokerageModel(BrokerageName.OandaBrokerage)
        
        self.lotSize = self.Securities[self.pair].SymbolProperties.LotSize
        self.Log("Lot size is " + str(self.lotSize))
        
        self.sma = self.SMA(self.pair, 200, Resolution.Hour)
        self.orderQuantity = 1000
        self.slPips = 100
        self.tpPips = 50

        
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
            # self.Log('Opening first pos at market: ' + str(first.Symbol) + str(first.Price))


    
    def OnOrderEvent(self, orderEvent):
        order = self.Transactions.GetOrderById(orderEvent.OrderId)
        
        if order.Status == OrderStatus.Filled:
            # if TP hit, cancel all orders
            if order.Type == OrderType.Limit:
                self.Transactions.CancelOpenOrders(order.Symbol)
                
            #if SL hit, open reverse recovery at market
            elif order.Type == OrderType.StopMarket:
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

        # new entry at market, update tag
        trade = self.MarketOrder(self.pair, position)
        updateSettings = UpdateOrderFields()
        updateSettings.Tag = str('MKT#' + tradeNum)
        trade.Update(updateSettings)
        
        sl = self.StopMarketOrder(self.pair, - position, (self.price - (self.slPips / 10000)), (str('SL#' + tradeNum)))
        tp = self.LimitOrder(self.pair, - position, (self.price + (self.slPips / 10000)), (str('TP#' + tradeNum)))
        return