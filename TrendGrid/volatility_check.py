from AlgorithmImports import *
import datetime
import pandas as pd

class VolatilityCheck(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2020, 1, 1)
        self.endDate = datetime.date(2021, 1, 1)
        self.SetEndDate(self.endDate)
        self.SetCash(10000)
        
        self.longPeriod = int(self.GetParameter("long-period"))
        self.shortPeriod = int(self.GetParameter("short-period"))

        self.SetBrokerageModel(BrokerageName.OandaBrokerage)

        self.Data = {}

        self.results = pd.DataFrame()
        headers = ['symbol', 'min_long', 'max_long', 'min_short', 'max_short', 'avg_long', 'avg_short', 'long_short_ratio']
        self.results = self.results.reindex(columns = headers)

        for ticker in ['AUDCAD', 'AUDCHF', 'AUDHKD', 'AUDJPY', 'AUDNZD', 'AUDSGD', 'AUDUSD', 'CADCHF', 'CADHKD', 'CADJPY', 'CADSGD', 'CHFHKD', 'CHFJPY', 'CHFZAR', 'EURAUD', 'EURCAD', 'EURCHF', 'EURCZK', 'EURDKK', 'EURGBP', 'EURHKD', 'EURHUF', 'EURJPY', 'EURNOK', 'EURNZD', 'EURPLN', 'EURSEK', 'EURSGD', 'EURTRY', 'EURUSD', 'EURZAR', 'GBPAUD', 'GBPCAD', 'GBPCHF', 'GBPHKD', 'GBPJPY', 'GBPNZD', 'GBPPLN', 'GBPSGD', 'GBPUSD', 'GBPZAR', 'HKDJPY', 'NZDCAD', 'NZDCHF', 'NZDHKD', 'NZDJPY', 'NZDSGD', 'NZDUSD', 'SGDCHF', 'SGDJPY', 'TRYJPY', 'USDCAD', 'USDCHF', 'USDCNH', 'USDCZK', 'USDDKK', 'USDHKD', 'USDHUF', 'USDJPY', 'USDMXN', 'USDNOK', 'USDPLN', 'USDSEK', 'USDSGD', 'USDTHB', 'USDTRY', 'USDZAR', 'ZARJPY']:
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
            # self.AddChart(plot)
    
            
        warmupPeriod = int(self.GetParameter("long-period"))
        self.SetWarmUp(warmupPeriod, Resolution.Hour)
            
            
    def OnData(self, data):
        if self.IsWarmingUp:
            return
        
        for symbol, symData in self.Data.items():
            
            rangeLong = symData.maxLong.Current.Value - symData.minLong.Current.Value
            rangeShort = symData.maxShort.Current.Value - symData.minShort.Current.Value
            rangeLong = (rangeLong / data[symbol].Close) * 100
            rangeShort = (rangeShort / data[symbol].Close) * 100
            
            # self.Plot(f'{symbol}', 'maxLong', symData.maxLong.Current.Value)
            # self.Plot(f'{symbol}', 'minLong', symData.minLong.Current.Value)
            # self.Plot(f'{symbol}', 'maxShort', symData.maxShort.Current.Value)
            # self.Plot(f'{symbol}', 'minShort', symData.minShort.Current.Value)
            # self.Plot(f'{symbol}', 'price', data[symbol].Close)
            
            symData.rangesLong.append(rangeLong)
            symData.rangesShort.append(rangeShort)

            def average(lst):
                a = sum(lst) / len(lst)
                return round(a, 4)

            if self.Time.date() == self.endDate - timedelta(days = 1) and self.Time.hour == 00:
                minRangeLong = round(min(symData.rangesLong), 4)
                maxRangeLong = round(max(symData.rangesLong), 4)
                avgRangeLong = average(symData.rangesLong)
                minRangeShort = round(min(symData.rangesShort), 4)
                maxRangeShort = round(max(symData.rangesShort), 4)
                avgRangeShort = average(symData.rangesShort)
                longShortRatio = round(avgRangeLong / avgRangeShort, 4)

                self.Log(f'{symbol} --- long/short ratio: {longShortRatio} ---')
                self.Log(f'{symbol} - min range long %: {minRangeLong}')
                self.Log(f'{symbol} - max range long %: {maxRangeLong}')
                self.Log(f'{symbol} - avg range long %: {avgRangeLong}')
                self.Log(f'{symbol} - min range short %: {minRangeShort}')
                self.Log(f'{symbol} - max range short %: {maxRangeShort}')
                self.Log(f'{symbol} - avg range short %: {avgRangeShort}')
                self.Log('-------------------------------')

                newrow = {'symbol': str(symbol), 'min_long': minRangeLong, 'max_long': maxRangeLong, 'avg_long': avgRangeLong, 
                        'min_short': minRangeShort, 'max_short': maxRangeShort, 'avg_short': avgRangeShort, 'long_short_ratio': longShortRatio}
                self.results = self.results.append(newrow, ignore_index = True)

        if self.Time.date() == self.endDate - timedelta(days = 1) and self.Time.hour == 00:        
            self.Log(self.results.to_dict())

            
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