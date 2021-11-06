from AlgorithmImports import *
import datetime

class VolatilityCheck(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2021, 9, 1)
        self.endDate = datetime.date(2021, 10, 1)
        self.SetEndDate(self.endDate)
        self.SetCash(10000)
        
        self.longPeriod = int(self.GetParameter("long-period"))
        self.shortPeriod = int(self.GetParameter("short-period"))

        self.SetBrokerageModel(BrokerageName.OandaBrokerage)

        self.Data = {}

        for ticker in ["GBPJPY", "EURUSD"]:
            symbol = self.AddForex(ticker , Resolution.Hour, Market.Oanda).Symbol
            self.Log('Initializing data for ' + str(symbol))

            minLong = self.MIN(symbol, self.longPeriod, Resolution.Hour)
            maxLong = self.MAX(symbol, self.longPeriod, Resolution.Hour)
            minShort = self.MIN(symbol, self.shortPeriod, Resolution.Hour)
            maxShort = self.MAX(symbol, self.shortPeriod, Resolution.Hour)

            self.Data[symbol] = SymbolData(minLong, maxLong, minShort, maxShort)
            
            plot = Chart(f'{ticker}')
            plot.AddSeries(Series("maxLong", SeriesType.Line, 0))
            plot.AddSeries(Series("minLong", SeriesType.Line, 0))
            plot.AddSeries(Series("maxShort", SeriesType.Line, 0))
            plot.AddSeries(Series("minShort", SeriesType.Line, 0))
            plot.AddSeries(Series("price", SeriesType.Line, 0))
            self.AddChart(plot)
    
            
        warmupPeriod = int(self.GetParameter("long-period"))
        self.SetWarmUp(warmupPeriod, Resolution.Hour)
            
            
    def OnData(self, data):
        if self.IsWarmingUp:
            return
        
        for symbol, symData in self.Data.items():
            
            rangeLong = symData.maxLong.Current.Value - symData.minLong.Current.Value
            rangeShort = symData.maxShort.Current.Value - symData.minShort.Current.Value
            

            if rangeLong > symData.maxRangeLong or symData.maxRangeLong == 0:
                symData.maxRangeLong = rangeLong
            if rangeLong < symData.minRangeLong or symData.minRangeLong == 0:
                symData.minRangeLong = rangeLong

            if rangeShort > symData.maxRangeShort or symData.maxRangeShort == 0:
                symData.maxRangeShort = rangeShort
            if rangeShort < symData.minRangeShort or symData.minRangeShort == 0:
                symData.minRangeShort = rangeShort
            
            self.Plot(f'{symbol}', 'maxLong', symData.maxLong.Current.Value)
            self.Plot(f'{symbol}', 'minLong', symData.minLong.Current.Value)
            self.Plot(f'{symbol}', 'maxShort', symData.maxShort.Current.Value)
            self.Plot(f'{symbol}', 'minShort', symData.minShort.Current.Value)
            # self.Plot(f'{symbol}', 'price', data[symbol].Close)
            
            symData.rangesLong.append(rangeLong)
            symData.rangesShort.append(rangeShort)

            def average(lst):
                a = sum(lst) / len(lst)
                return round(a, 4)

            if self.Time.date() == self.endDate - timedelta(days = 1) and self.Time.hour == 00:
                longShortRatio = round(average(symData.rangesLong) / average(symData.rangesShort), 4)

                self.Log(f'{symbol} --- long/short ratio: {longShortRatio} ---')
                self.Log(f'{symbol} - min range long: {round(min(symData.rangesLong), 4)}')
                self.Log(f'{symbol} - max range long: {round(max(symData.rangesLong), 4)}')
                self.Log(f'{symbol} - avg range long: {average(symData.rangesLong)}')
                
                self.Log(f'{symbol} - min range short: {round(min(symData.rangesShort), 4)}')
                self.Log(f'{symbol} - max range short: {round(max(symData.rangesShort), 4)}')
                self.Log(f'{symbol} - avg range short: {average(symData.rangesShort)}')
                self.Log('-------------------------------')


            

        
    
            
class SymbolData:
    
    def __init__(self, minLong, maxLong, minShort, maxShort):
        self.minLong = minLong
        self.maxLong = maxLong
        self.minShort = minShort
        self.maxShort = maxShort
        
        self.maxRangeLong = 0
        self.minRangeLong = 0
        self.maxRangeShort = 0
        self.minRangeShort = 0

        self.rangesLong = []
        self.rangesShort = []