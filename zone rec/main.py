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
        
        self.trades = {'rec0': '', 'slRec0': '', 'tpRec0': '',
            'rec1': '', 'slRec1': '', 'tpRec1': '',
            'rec2': '', 'slRec2': '', 'tpRec2': '',
        }

        
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
            self.Log('trades: ' + str(self.trades))
            
        # cancel all orders if a TP is hit
        
        # can't use dict to store orders :(
        # Runtime Error: AttributeError : 'str' object has no attribute 'Status' at OnData elif self.trades['tpRec0'].Status == OrderStatus.Filled
        elif self.trades['tpRec0'].Status == OrderStatus.Filled or self.trades['tpRec1'].Status == OrderStatus.Filled or self.trades['tpRec2'].Status == OrderStatus.Filled:
            self.Transactions.CancelOpenOrders(self.pair)
        # open recovery trades
        elif self.trades[slRec0].Status == OrderStatus.Filled:
            self.trades[tpRec0].Cancel()
            self.recTrade(1, (2 * (- firstPosition)))
        elif self.trades[slRec1].Status == OrderStatus.Filled:
            self.trades[tpRec1].Cancel()
            self.recTrade(2, (4 * firstPosition))
        elif self.trades[slRec2].Status == OrderStatus.Filled:
            self.trades[tpRec2].Cancel()
            self.recTrade(3, (8 * (- firstPosition)))


    def recTrade(self, recNum, position):
        
        self.trades[str("rec" + str(recNum))] = self.MarketOrder(self.pair, position)
        self.trades[str("slRec" + str(recNum))] = self.StopMarketOrder(self.pair, -self.orderQuantity, (self.price - (self.slPips / 10000)))
        self.trades[str("tpRec" + str(recNum))] = self.LimitOrder(self.pair, -self.orderQuantity, (self.price + (self.slPips / 10000)))
        
        self.Log("rec" + str(recNum) + " at " + str(self.price) + " | " + 
                "slRec" + str(recNum) + " at " + str(self.price - (self.slPips / 10000)) + " | " +
                "tpRec" + str(recNum) + " at " + str(self.price + (self.tpPips / 10000)))
        # self.Log("SL " + str(recNum) + " at " + str(self.price - (self.slPips / 10000)) + " | TP " + str(recNum) + " at " + str(self.price + (self.tpPips / 10000)))
        
        return
            