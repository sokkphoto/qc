class GreenMuleZoneRec(QCAlgorithm):

    def Initialize(self):

        self.SetCash(1000)
        self.SetStartDate(2017, 5, 1)
        self.SetEndDate(2017, 5, 31)
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
            self.recTrade(0, firstPosition)
            
        # cancel all orders if a TP is hit
        elif self.tpRec0.Status == OrderStatus.Filled or self.tpRec1.Status == OrderStatus.Filled or self.tpRec2.Status == OrderStatus.Filled:
            self.Transactions.CancelOpenOrders(self.pair)
        
        # open recovery trades
        elif self.slRec0.Status == OrderStatus.Filled:
            self.tpRec0.Cancel()
            self.recTrade(1, (2 * (- firstPosition)))
        elif slRec1.Status == OrderStatus.Filled:
            self.tpRec1.Cancel()
            self.recTrade(2, (4 * firstPosition))
        elif slRec2.Status == OrderStatus.Filled:
            self.tpRec2.Cancel()
            self.recTrade(3, (8 * (- firstPosition)))


    def recTrade(self, recNum, position):
        recTag = str("rec" + (f'{recNum}'.split('=')[0]))
        slRecTag = str("slRec" + (f'{recNum}'.split('=')[0]))
        tpRecTag = str("tpRec" + (f'{recNum}'.split('=')[0]))
        
        (globals()[recTag]) = self.MarketOrder(self.pair, position)
        self.Log("Trade " + str(recNum) + " at " + str(self.price))
        (globals()[slRecTag]) = self.StopMarketOrder(self.pair, -self.orderQuantity, (self.price - (self.slPips / 10000)))
        (globals()[tpRecTag]) = self.LimitOrder(self.pair, -self.orderQuantity, (self.price + (self.slPips / 10000)))
        self.Log("SL " + str(recNum) + " at " + str(self.price - (self.slPips / 10000)) + " | TP " + str(recNum) + " at " 
                                + str(self.price + (self.tpPips / 10000)))
        
        self.rec0 = rec0
        self.slRec0 = slRec0
        self.tpRec0 = tpRec0
        self.rec1 = rec1
        self.slRec1 = slRec1
        self.tpRec1 = tpRec1
        self.rec2 = rec2
        self.slRec2 = slRec2
        self.tpRec2 = tpRec2
        
        return
            