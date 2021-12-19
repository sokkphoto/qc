from AlgorithmImports import *
from datetime import datetime, timedelta
import datetime

class TrendGrid(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2021, 1, 1)
        self.endDate = datetime.date(2021, 11, 28)
        self.SetEndDate(self.endDate)
        self.SetCash(10000)
        
        self.orderQuantity = int(self.GetParameter("order-quantity"))
        self.gridSpaceAtr = float(self.GetParameter("grid-space-atr"))
        self.maxOpen = int(self.GetParameter("max-open"))
        self.entryDistATRs = float(self.GetParameter("entry-dist-atrs"))
        self.profitTargetATRs = int(self.GetParameter("profit-target-atrs"))
        self.unrealizedPLStopATRs = int(self.GetParameter("unrealized-pl-stop-atrs"))
        self.emaSlow = int(self.GetParameter("ema-slow"))
        self.bbPeriod = int(self.GetParameter("bb-period"))
        self.atrPeriod = int(self.GetParameter("atr-period"))
        self.targetToUPL = float(self.GetParameter("target-upl-ratio"))
        self.pairInList = int(self.GetParameter("pair-in-list"))

        self.SetBrokerageModel(BrokerageName.OandaBrokerage)

        self.Log('--- PARAMS ---')
        self.Log(f'grid-space-atr: {self.gridSpaceAtr} | unrealized-pl-stop-atrs: {self.unrealizedPLStopATRs} | max-open: {self.maxOpen} | ema-slow: {self.emaSlow}')

        self.Data = {}

        pairs = ['AUDUSD']
        # pairs = [pairs[self.pairInList]]

        for ticker in pairs:
            symbol = self.AddForex(ticker , Resolution.Minute, Market.Oanda).Symbol
            self.Log('Initializing data for ' + str(symbol))

            emaSlow = self.EMA(symbol, self.emaSlow, Resolution.Hour)
            bb = self.BB(symbol, int(self.GetParameter("bb-period")), float(self.GetParameter("bb-stddev")), Resolution.Hour)
            atr = self.ATR(symbol, int(self.atrPeriod), MovingAverageType.Simple, Resolution.Hour)

            self.Data[symbol] = SymbolData(emaSlow, bb, atr)
            
            #plot = Chart(f'{ticker}')
            #plot.AddSeries(Series("emaSlow", SeriesType.Line, 0))
            #plot.AddSeries(Series("price", SeriesType.Line, 0))
            #plot.AddSeries(Series("long entry", SeriesType.Scatter, 0))
            #plot.AddSeries(Series("short entry", SeriesType.Scatter, 0))
            #plot.AddSeries(Series("close all", SeriesType.Scatter, 0))
            #plot.AddSeries(Series("mid", SeriesType.Line, 0))
            #plot.AddSeries(Series("upper", SeriesType.Line, 0))
            #plot.AddSeries(Series("lower", SeriesType.Line, 0))
            #self.AddChart(plot)


        warmupPeriod = int(max(self.bbPeriod, self.emaSlow))
        self.SetWarmUp(warmupPeriod, Resolution.Hour)

        #plPlot = Chart(f'runningPL')
        #plPlot.AddSeries(Series("total PL", SeriesType.Line, 0))
        #plPlot.AddSeries(Series("unrealized PL", SeriesType.Line, 0))
        #self.AddChart(plPlot)
            
            
    def OnData(self, data):
        if self.IsWarmingUp:
            return
        
        for symbol, symData in self.Data.items():
            
            price = data[symbol].Close
            emaSlow = symData.emaSlow.Current.Value
            bbMid = symData.bb.MiddleBand.Current.Value
            bbUpper = symData.bb.UpperBand.Current.Value
            bbLower = symData.bb.LowerBand.Current.Value

            # --- entry ---
            if not self.Portfolio[symbol].Invested:
                # entryDist = round(symData.atr.Current.Value * self.entryDistATRs, 4)

                def symbolGridParams():
                    symData.gridSpace = round(symData.atr.Current.Value * self.gridSpaceAtr, 4)
                    symData.unrealizedPLStop = round(symData.atr.Current.Value * self.unrealizedPLStopATRs, 4)
                    symData.profitTarget = round(symData.atr.Current.Value * self.profitTargetATRs, 4)

                if bbMid < emaSlow and price > bbUpper:
                    symbolGridParams()
                    #self.Plot(f'{symbol}', 'long entry', price)
                    self.Log(f'Initial long with {symbol} @ {price} | Grid spacing: {symData.gridSpace} | EMA slow: {emaSlow} | BB mid: {bbMid}')
                    self.tradeLong(symbol)
                    symData.gridStart = self.Time
                elif bbMid > emaSlow and price < bbLower:
                    symbolGridParams()
                    #self.Plot(f'{symbol}', 'short entry', price)
                    self.Log(f'Initial short with {symbol} @ {price} | Grid spacing: {symData.gridSpace} | EMA slow: {emaSlow} | BB mid: {bbMid}')
                    self.tradeShort(symbol)
                    symData.gridStart = self.Time

            # --- exit ---
            if self.Portfolio[symbol].IsLong:
                unrealizedPL = self.unrealizedPL(price, symData.openEntries, 1)
                totalPL = round(unrealizedPL + self.realizedPL(symbol, symData.tpCount), 4)
                
                if (price < emaSlow and totalPL > symData.profitTarget) or unrealizedPL < symData.unrealizedPLStop :
                    self.Log(f'--- Closing on long {symbol} | total PL: {totalPL} | unrealized: {unrealizedPL}---')
                    if price < emaSlow: self.Log('EMA cross')
                    if unrealizedPL < symData.unrealizedPLStop : self.Log('uPL hit')
                    #self.Plot(f'{symbol}', 'close all', price)
                    self.closeAll(symbol)
                    
                elif price < symData.prevLine:
                    self.Log(f'Lower line hit on long {symbol} @ {price}')
                    self.Log(f'Total PL: {totalPL} | Unrealized PL: {unrealizedPL}| Open: {symData.openEntries}')
                    if self.checkEntries(symbol, price, symData.openEntries) == None:
                        self.tradeLong(symbol)

            if self.Portfolio[symbol].IsShort:
                unrealizedPL = self.unrealizedPL(price, symData.openEntries, -1)
                totalPL = unrealizedPL + self.realizedPL(symbol, symData.tpCount)
                
                if (price > emaSlow and totalPL > symData.profitTarget) or unrealizedPL < symData.unrealizedPLStop:
                    self.Log(f'--- Closing on short {symbol} | total PL: {totalPL} | unrealized: {unrealizedPL}---')
                    if price > emaSlow: self.Log('EMA cross')
                    if unrealizedPL < symData.unrealizedPLStop : self.Log('uPL hit')
                    #self.Plot(f'{symbol}', 'close all', price)
                    self.closeAll(symbol)

                elif price > symData.prevLine:
                    self.Log(f'Upper line hit on short {symbol} @ {price}')
                    self.Log(f'Total PL: {totalPL} | Unrealized PL: {unrealizedPL}| Open: {symData.openEntries}')
                    if self.checkEntries(symbol, price, symData.openEntries) == None:
                        self.tradeShort(symbol)



            # log grid times in h
            def average(lst):
                a = sum(lst) / len(lst)
                return round(a, 4)

            # if self.Time.date() == self.endDate - timedelta(days = 1) and self.Time.hour == 23:
            #     minGridTime = round(min(symData.gridHours), 2)
            #     maxGridTime = round(max(symData.gridHours), 2)
            #     avgGridTime = round(average(symData.gridHours), 2)
            #     self.Log(f'{symbol} - min grid hours: {minGridTime}')
            #     self.Log(f'{symbol} - max grid hours: {maxGridTime}')
            #     self.Log(f'{symbol} - avg grid hours: {avgGridTime}')

            
            #self.Plot(f'{symbol}', 'emaSlow', symData.emaSlow.Current.Value)
            #self.Plot(f'{symbol}', 'mid', symData.bb.MiddleBand.Current.Value)
            #self.Plot(f'{symbol}', 'upper', symData.bb.UpperBand.Current.Value)
            #self.Plot(f'{symbol}', 'lower', symData.bb.LowerBand.Current.Value)

        #try:
        #    self.Plot('runningPL', 'total PL', totalPL)
        #    self.Plot('runningPL', 'unrealized PL', unrealizedPL)
        #except:
        #    pass


                    
    def OnOrderEvent(self, orderEvent):
        order = self.Transactions.GetOrderById(orderEvent.OrderId)
        symbol = order.Symbol
        price = orderEvent.FillPrice
        
        if order.Status == OrderStatus.Filled and order.Type == OrderType.Limit:
            if orderEvent.FillQuantity < 0:
                self.Log(f'TP hit on long {symbol} @ {price}')
                self.Data[symbol].tpCount += 1
                
                #delete original entry from openEntries
                originalEntryPrice = price - self.Data[symbol].gridSpace
                originalEntry = self.checkEntries(symbol, originalEntryPrice, self.Data[symbol].openEntries)
                if originalEntry != None:
                    self.Data[symbol].openEntries.remove(originalEntry)

                entriesCurrentPrice = self.checkEntries(symbol, price, self.Data[symbol].openEntries)
                if entriesCurrentPrice == None:
                    self.Log(f'Currently open trades: {self.Data[symbol].openEntries}')
                    self.Log(f'Opening long on {symbol} @ {price}')
                    self.tradeLong(symbol)
                else:
                    self.Log(f'Open entry already at {entriesCurrentPrice}')


            elif orderEvent.FillQuantity > 0:
                self.Log(f'TP hit on short {symbol} @ {price}')
                self.Data[symbol].tpCount += 1
                
                #delete original entry from openEntries
                originalEntryPrice = price + self.Data[symbol].gridSpace
                originalEntry = self.checkEntries(symbol, originalEntryPrice, self.Data[symbol].openEntries)
                if originalEntry != None:
                    self.Data[symbol].openEntries.remove(originalEntry)

                entriesCurrentPrice = self.checkEntries(symbol, price, self.Data[symbol].openEntries)
                if entriesCurrentPrice == None:
                    self.Log(f'Currently open trades: {self.Data[symbol].openEntries}')
                    self.Log(f'Opening short on {symbol} @ {price}')
                    self.tradeShort(symbol)
                else:
                    self.Log(f'Open entry already at {entriesCurrentPrice}')
                
            
    def tradeLong(self, symbol):
        if len(self.Data[symbol].openEntries) >= self.maxOpen:
            self.Log('Max open trades reached!')
            return

        market = self.MarketOrder(symbol, self.orderQuantity)
        price = market.AverageFillPrice
        # price = self.Securities[symbol].Price
        self.Data[symbol].entry = price
        target = round(price + self.Data[symbol].gridSpace , 4)
        self.LimitOrder(symbol, - self.orderQuantity, target)

        self.Data[symbol].prevLine = price - self.Data[symbol].gridSpace
        self.Data[symbol].openEntries.append(price)
        
    def tradeShort(self, symbol):
        if len(self.Data[symbol].openEntries) >= self.maxOpen:
            self.Log('Max open trades reached!')
            return

        market = self.MarketOrder(symbol, - self.orderQuantity)
        price = market.AverageFillPrice
        self.Data[symbol].entry = price
        target = round(price - self.Data[symbol].gridSpace , 4)
        self.LimitOrder(symbol, self.orderQuantity, target)

        self.Data[symbol].prevLine = price + self.Data[symbol].gridSpace
        self.Data[symbol].openEntries.append(price)

    def closeAll(self, symbol):
        self.Liquidate(symbol)
        self.Transactions.CancelOpenOrders(symbol)

        self.Data[symbol].entry = None
        self.Data[symbol].prevLine = None
        self.Data[symbol].openEntries = []
        self.Data[symbol].tpCount = 0
        
        # calculate and store grid period in h
        # self.Data[symbol].gridEnd = self.Time
        # diff = self.Data[symbol].gridEnd - self.Data[symbol].gridStart
        # diff = round(diff.total_seconds() / 3600, 2)
        # self.Data[symbol].gridHours.append(diff)
        # self.Data[symbol].gridEnd = None
        # self.Data[symbol].gridStart = None
        # self.Log(f'{symbol} - grid hours so far: {self.Data[symbol].gridHours}')


    def checkEntries(self, symbol, price, openlist):
        result = None
        for i in range(len(openlist)):
            if openlist[i] < (price + (0.4 * self.Data[symbol].gridSpace)) and openlist[i] > (price - (0.4 * self.Data[symbol].gridSpace)):
                result = openlist[i]
        return result

    def unrealizedPL(self, price, openlist, direction):
        unrealized = 0
        for i in range(len(openlist)):
            if direction > 0:
                unrealized += price - openlist[i]
            elif direction < 0:
                unrealized += openlist[i] - price
        return round(unrealized, 4)

    def realizedPL(self, symbol, tpcount):
        realized = tpcount * self.Data[symbol].gridSpace
        #self.Log(f'tpcount {tpcount}, gridspace {self.Data[symbol].gridSpace}, realized {realized}')
        return round(realized, 4)

    def minMaxCooldown(self, symbol):
        hoursSincelastMinMax = min(self.Data[symbol].min.PeriodsSinceMinimum, self.Data[symbol].max.PeriodsSinceMaximum)
        try:
            if hoursSincelastMinMax < self.minMaxCooldownHours:
                result = True
                if self.Time.hour == 23 and self.Time.minute == 59 : 
                    self.Log(f'Cooldown active, last min-max was {hoursSincelastMinMax} hours ago.')
            else:
                result = False
        except:
            result = False
        return result
        
    
            
class SymbolData:
    
    def __init__(self, emaSlow, bb, atr):
        self.emaSlow = emaSlow
        self.bb = bb
        self.atr = atr
        self.openEntries = []
        self.tpCount = 0
        self.gridHours = []