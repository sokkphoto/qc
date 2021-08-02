class MuscularApricotSalmon(QCAlgorithm):

    def Initialize(self):
        self.SetCash(1000)
        self.SetStartDate(2020, 1, 1)
        self.SetEndDate(2020, 3, 1)
        self.pair = self.AddForex("EURUSD", Resolution.Minute, Market.Oanda).Symbol
        self.SetBrokerageModel(BrokerageName.OandaBrokerage)
        self.lotSize = self.Securities[self.pair].SymbolProperties.LotSize
        
        self.smaSlow = self.SMA(self.pair, int(self.GetParameter("sma-slow")), Resolution.Hour)
        self.smaMid = self.SMA(self.pair, int(self.GetParameter("sma-mid")), Resolution.Hour)
        self.smaFast = self.SMA(self.pair, int(self.GetParameter("sma-fast")), Resolution.Hour)
        
        self.atr = self.ATR(self.pair, int(self.GetParameter("atr")), MovingAverageType.Simple, Resolution.Hour)
        self.RegisterIndicator(self.pair, self.atr, Resolution.Hour)
        
        self.orderQuantity = int(self.GetParameter("order-quantity"))
        self.atrFactorSL = float(self.GetParameter("atr-factor-sl"))
        self.atrFactorTP = float(self.GetParameter("atr-factor-tp"))
        self.slPipsMax = int(self.GetParameter("slpips-max"))
        self.slPipsMin = int(self.GetParameter("slpips-min"))
        self.tpPipsMax = int(self.GetParameter("tppips-max"))
        self.tpPipsMin = int(self.GetParameter("tppips-min"))
        
        self.Log('Order quantity is ' + str(self.orderQuantity))

    def OnData(self, data):
        if not self.smaSlow.IsReady or self.pair not in data:
            return
        
        self.price = data[self.pair].Close
        
        # check conditions
        if (self.smaMid.Current.Value > self.smaSlow.Current.Value and 
                self.smaFast.Current.Value > self.smaMid.Current.Value and 
                self.price < self.smaFast.Current.Value):
            self.position = self.orderQuantity
        elif (self.smaMid.Current.Value < self.smaSlow.Current.Value and 
                self.smaFast.Current.Value < self.smaMid.Current.Value and 
                self.price > self.smaFast.Current.Value):
            self.position = - self.orderQuantity
        else: 
            return
    
        # set SL and TP based on ATR
        def limit(num, minimum, maximum):
            return max(min(num, maximum), minimum)
            
        self.tpPips = self.atr.Current.Value * self.atrFactorTP * 10000
        self.tpPips = limit(self.tpPips, self.tpPipsMin, self.tpPipsMax)
        self.slPips = self.atr.Current.Value * self.atrFactorSL * 10000
        self.slPips = limit(self.slPips, self.slPipsMin, self.slPipsMax)
        
        # enter if conditions met & already not in trade
        if not self.Portfolio.Invested:
            self.Log('First entry conditions met. Slow SMA: ' + str(self.smaSlow.Current.Value) + 
                ' | Fast SMA: ' + str(self.smaFast.Current.Value) + ' | Mid SMA: ' + str(self.smaMid.Current.Value) + ' | Price: ' + str(self.price))
            
            if self.tradeNum == 0: self.tradeNum = 1
            first = self.newTrade(self.tradeNum, self.position)
            
        # if already in trade, trail stop
        else:
            self.trailStop(self.sl)


    def OnOrderEvent(self, orderEvent):
        order = self.Transactions.GetOrderById(orderEvent.OrderId)
        
        if order.Status == OrderStatus.Filled:
            # if TP hit, cancel all orders
            if order.Type == OrderType.Limit:
                self.Transactions.CancelOpenOrders()
                self.Log(str(order.Tag) + ' hit at ' + str(self.price))
                self.tradeNum = 0
                
            #if SL hit, open reverse recovery at market
            elif order.Type == OrderType.StopMarket:
                self.Transactions.CancelOpenOrders()
                self.Log(str(order.Tag) + ' hit at ' + str(self.price))
                
                self.tradeNum = self.tradeNum + 1
                
        if order.Status == OrderStatus.Canceled:
            self.Log(str(orderEvent))
                
                
    def newTrade(self, n, position):
        self.trade = self.MarketOrder(self.pair, position)
        self.Log('New entry at market: ' + str(self.trade.Quantity) + ' @ ' + str(self.price))
            
        # set SL and TP
        if position > 0:
            sl = self.StopMarketOrder(self.pair, - position, (self.price - (self.slPips / 10000)), (str('SL#' + tradeNum)))
            tp = self.LimitOrder(self.pair, - position, (self.price + (self.tpPips / 10000)), (str('TP#' + tradeNum)))
            
        elif position < 0:
            sl = self.StopMarketOrder(self.pair, - position, (self.price + (self.slPips / 10000)), (str('SL#' + tradeNum)))
            tp = self.LimitOrder(self.pair, - position, (self.price - (self.tpPips / 10000)), (str('TP#' + tradeNum)))
        self.Log('SL#' + tradeNum + ' set at ' + ' | ' + 'TP#' + tradeNum + ' set at ')
        
        
    def trailStop(self, trade, position):
        
        updateSettingsSl = UpdateOrderFields()
        slPos = self.sl.Get(OrderField.StopPrice)
        self.Debug('SL pos size is ' + str(slPos))
        
        if slPos > 0:
            if self.price < 
            updateSettingsSl.StopPrice = self.price - (self.slPips / 10000)
        elif slPos < 0:
            updateSettingsSl.StopPrice = self.price + (self.slPips / 10000)
        responseSl = self.sl.Update(updateSettingsSl)

        if responseSl.IsSuccess:
             self.Debug("SL updated to " + str(updateSettingsSl.StopPrice))

    