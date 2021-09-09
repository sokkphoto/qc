from datetime import timedelta

class MAMultiPair(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2020, 1, 1)
        self.SetEndDate(2020, 6, 1)
        self.SetCash(10000)
        
        emaFactor = float(self.GetParameter("ema-speed-factor"))
        emaSpeedMid = round((int(self.GetParameter("ema-fast"))) * emaFactor)
        emaSpeedSlow = round((int(self.GetParameter("ema-fast"))) * emaFactor * emaFactor)

        self.Data = {}

        for ticker in ["NZDUSD","EURUSD"]:
           symbol = self.AddForex(ticker , Resolution.Hour).Symbol
           self.Data[symbol] = SymbolData(
                self.EMA(symbol, int(self.GetParameter("ema-fast")), Resolution.Hour),
                self.EMA(symbol, emaSpeedMid, Resolution.Hour),
                self.EMA(symbol, emaSpeedSlow, Resolution.Hour),
                self.ATR(symbol, int(self.GetParameter("atr")), MovingAverageType.Simple, Resolution.Hour),
                self.ADX(symbol, int(self.GetParameter("adx-period")), Resolution.Hour))
        
        self.Log('** EMAs ** Fast: ' + str(self.GetParameter("ema-fast")) + ' Mid: ' + str(emaSpeedMid) + ' Slow: ' + str(emaSpeedSlow))
        self.tradeNum = 0

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
            validCross = self.checkValidCross(fast, mid, slow, atr)
            
            # check entry conditions
            if (price < fast and
                    validCross == 1 and
                    adx > self.adxMin):
                self.position = self.orderQuantity
            elif (price > fast and
                    validCross == -1 and
                    adx > self.adxMin):
                self.position = - self.orderQuantity
            else: 
                return
            
            if not self.Portfolio.Invested:
                self.Log('First entry conditions met. Slow SMA: ' + str(slow) + 
                    ' | Fast SMA: ' + str(fast) + ' | Mid SMA: ' + str(mid) + ' | Price: ' + str(price))
                self.Log('ADX: ' + str(adx))
                
                # store cross direction & tradenum
                self.crossAtEntry = validCross
                if self.tradeNum == 0: 
                    self.tradeNum = 1
                self.Log('Opening trade #' + str(self.tradeNum))
                
                position = round(self.orderQuantity)
                self.Log('Position: ' + str(self.position))
                
                self.trade = self.newTrade(self.tradeNum, position, symbol, price)
            
                
                
    
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
        
        
    def newTrade(self, tradeNum, position, symbol, price):
        tradeNum = str(tradeNum)
        trade = self.MarketOrder(symbol, position)
        self.Log('New entry at market: ' + str(trade.Quantity) + ' @ ' + str(price))
        
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
            sl = self.StopMarketOrder(symbol, - position, round((price - slDistance), 5), (str('SL#' + tradeNum)))
            tp = self.LimitOrder(symbol, - position, round((price + tpDistance), 5), (str('TP#' + tradeNum)))
            
        elif position < 0:
            sl = self.StopMarketOrder(symbol, - position, round((price + (slDistance / 10000)), 5), (str('SL#' + tradeNum)))
            tp = self.LimitOrder(symbol, - position, round((price - (tpDistance / 10000)), 5), (str('TP#' + tradeNum)))
        self.Log('SL#' + tradeNum + ' set at ' + str(sl.Get(OrderField.StopPrice)) + ' | ' + 'TP#' + tradeNum + ' set at ' + str(tp.Get(OrderField.LimitPrice)))
        return
                
    

class SymbolData:
    
    def __init__(self, fast, mid, slow, atr, adx):
        self.fast = fast
        self.mid = mid
        self.slow = slow
        self.atr = atr
        self.adx = adx
        