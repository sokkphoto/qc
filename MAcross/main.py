from AlgorithmImports import *

# 3MA cross
class MuscularApricotSalmon(QCAlgorithm):

    def Initialize(self):
        self.SetCash(1000)
        self.SetStartDate(2020, 6, 1)
        self.SetEndDate(2021, 1, 1)
        self.pair = self.AddForex("EURUSD", Resolution.Hour, Market.Oanda).Symbol
        self.SetBrokerageModel(BrokerageName.OandaBrokerage)
        self.lotSize = self.Securities[self.pair].SymbolProperties.LotSize
        
        self.emaFast = self.EMA(self.pair, int(self.GetParameter("ema-fast")), Resolution.Hour)
        emaFactor = float(self.GetParameter("ema-speed-factor"))
        emaSpeedMid = round((int(self.GetParameter("ema-fast"))) * emaFactor)
        emaSpeedSlow = round((int(self.GetParameter("ema-fast"))) * emaFactor * emaFactor)
        self.emaMid = self.EMA(self.pair, emaSpeedMid, Resolution.Hour)
        self.emaSlow = self.EMA(self.pair, emaSpeedSlow, Resolution.Hour)
        self.Log('** EMAs ** Fast: ' + str(self.GetParameter("ema-fast")) + ' Mid: ' + str(emaSpeedMid) + ' Slow: ' + str(emaSpeedSlow))
        
        self.adx = self.ADX(self.pair, int(self.GetParameter("adx-period")), Resolution.Hour)
        
        self.atr = self.ATR(self.pair, int(self.GetParameter("atr")), MovingAverageType.Simple, Resolution.Hour)
        self.RegisterIndicator(self.pair, self.atr, Resolution.Hour)
        
        self.orderQuantity = int(self.GetParameter("order-quantity"))
        self.atrFactorSL = float(self.GetParameter("atr-factor-sl"))
        self.atrFactorTP = float(self.GetParameter("atr-factor-tp"))
        self.slPipsMax = int(self.GetParameter("slpips-max"))
        self.slPipsMin = int(self.GetParameter("slpips-min"))
        self.tpPipsMax = int(self.GetParameter("tppips-max"))
        self.tpPipsMin = int(self.GetParameter("tppips-min"))
        self.adxMin = int(self.GetParameter("adx-min"))
        self.reverseCrossExitenabled = int(self.GetParameter("reverse-cross-exit"))
        self.orderInc = float(self.GetParameter("order-inc"))
        
        self.Log('Order quantity is ' + str(self.orderQuantity))
        self.tradeNum = 0
        self.validCross = 0

    def OnData(self, data):
        if not self.emaSlow.IsReady or self.pair not in data:
            return
        
        self.price = data[self.pair].Close
        self.checkValidCross(self.emaFast.Current.Value, self.emaMid.Current.Value, self.emaSlow.Current.Value, self.atr.Current.Value)
        
        # exit on reverse cross
        if self.Portfolio.Invested and self.reverseCrossExitenabled == 1:
            self.reverseCrossExit(self.crossAtEntry, self.emaFast.Current.Value, self.emaMid.Current.Value, self.emaSlow.Current.Value)
        
        # check entry conditions
        if (self.price < self.emaFast.Current.Value and
                self.validCross == 1 and
                self.adx.Current.Value > self.adxMin):
            self.position = self.orderQuantity
        elif (self.price > self.emaFast.Current.Value and
                self.validCross == -1 and
                self.adx.Current.Value > self.adxMin):
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
            self.Log('First entry conditions met. Slow SMA: ' + str(self.emaSlow.Current.Value) + 
                ' | Fast SMA: ' + str(self.emaFast.Current.Value) + ' | Mid SMA: ' + str(self.emaMid.Current.Value) + ' | Price: ' + str(self.price))
            self.Log('ADX: ' + str(self.adx.Current.Value))
            
            # store cross direction & tradenum
            self.crossAtEntry = self.validCross
            if self.tradeNum == 0: 
                self.tradeNum = 1
            self.Log('Opening trade #' + str(self.tradeNum))
            
            self.position = round(self.orderQuantity * pow(self.orderInc, self.tradeNum - 1))
            self.Log('Position: ' + str(self.position))
            
            self.trade = self.newTrade(self.tradeNum, self.position)
            
        # if already in trade, trail stop
        else: 
            self.trailStop(self.sl, self.position)

            


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
                
                if self.checkTradePL(self.entryPrice, self.price) < 0 :
                    self.tradeNum = self.tradeNum + 1
                else:
                    self.tradeNum = 0
                
        if order.Status == OrderStatus.Canceled:
            self.Log(str(orderEvent))
                
                
    def newTrade(self, tradeNum, position):
        tradeNum = str(tradeNum)
        self.trade = self.MarketOrder(self.pair, position)
        self.Log('New entry at market: ' + str(self.trade.Quantity) + ' @ ' + str(self.price))
        self.entryPrice = self.price
            
        # set SL and TP
        if position > 0:
            self.sl = self.StopMarketOrder(self.pair, - position, round((self.price - (self.slPips / 10000)), 5), (str('SL#' + tradeNum)))
            tp = self.LimitOrder(self.pair, - position, round((self.price + (self.tpPips / 10000)), 5), (str('TP#' + tradeNum)))
            
        elif position < 0:
            self.sl = self.StopMarketOrder(self.pair, - position, round((self.price + (self.slPips / 10000)), 5), (str('SL#' + tradeNum)))
            tp = self.LimitOrder(self.pair, - position, round((self.price - (self.tpPips / 10000)), 5), (str('TP#' + tradeNum)))
        self.Log('SL#' + tradeNum + ' set at ' + str(self.sl.Get(OrderField.StopPrice)) + ' | ' + 'TP#' + tradeNum + ' set at ' + str(tp.Get(OrderField.LimitPrice)))
        return
        
    
    # stop trade ticket and original trade position as input    
    def trailStop(self, stoptrade, position):
        
        slPrice = stoptrade.Get(OrderField.StopPrice)
        
        updateSettingsSl = UpdateOrderFields()
        # trade is long, SL short
        if self.price > slPrice + (self.slPips / 10000) and position > 0:
            updateSettingsSl.StopPrice = round(self.price - (self.slPips / 10000), 5)
            responseSl = self.sl.Update(updateSettingsSl)
            self.Log('SL updated to ' + str(updateSettingsSl.StopPrice))
            
        # trade is short, SL long
        elif self.price < slPrice - (self.slPips / 10000) and position < 0:
            updateSettingsSl.StopPrice = round(self.price + (self.slPips / 10000), 5)
            responseSl = self.sl.Update(updateSettingsSl)
            self.Log('SL updated to ' + str(updateSettingsSl.StopPrice))
            
        return
        
        
    
    # exit & cancel all orders if crossed in opposite direction & price > emaFast 
    def reverseCrossExit(self, currentPosition, fast, mid, slow):
        # self.Log(str(currentPosition) + '  ' + str(fast) + '  ' + str(mid))
        if (currentPosition > 0 and fast < mid and mid < slow):
            liquidate = True
        elif (currentPosition < 0 and fast > mid and mid > slow):
            liquidate = True
        else:
            liquidate = False
        
        if liquidate == True:
            self.Log('Reverse cross detected, exiting.')
            self.Liquidate()
            if self.checkTradePL(self.entryPrice, self.price) < 0 :
                self.tradeNum = self.tradeNum + 1
            else:
                self.tradeNum = 0
        
        return
    
    
    # check if the MAs have been in a proximity of x ATRs, and crossed
    # this is to avoid entry too late (when MAs are already apart), before reversion
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
    
    # get trade P/L in pips
    def checkTradePL(self, entryPrice, exitPrice):
        if self.position > 0:
            pl = exitPrice - entryPrice
        elif self.position < 0:
            pl = entryPrice - exitPrice
        
        pl = round(pl * 10000)
        self.Log('Trade P/L: ' + str(pl) + ' pips')
        return pl
    