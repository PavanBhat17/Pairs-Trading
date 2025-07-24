from typing import Union, Dict

from .models.assets import Asset, QuoteAsset
from .config import DevelopmentConfig
from .algo import AlgoTradingPipeline
from .pipelines.retriever import TimeSeriesRetrieverPipeline
import yfinance as yf
import pandas as pd
import statsmodels.api as sm


class BacktestAlgoTradingPipeline(AlgoTradingPipeline):

    def __init__(self, development_config: DevelopmentConfig):
        super().__init__(development_config)
        self.init_data = None
        self.testing_data = None
        self._long_profit = None
        self._short_profit = None 
        self._long_value = None 
        self._short_value = None 

    @property 
    def long_profit(self):
        return self._long_profit

    @property 
    def long_value(self):
        return self._long_value 

    @property 
    def short_profit(self):
        return self._short_profit

    @property 
    def short_value(self):
        return self._short_value

    def initialize(self): 
        self._initialize_data()
        self._initialize_algo()

    def _initialize_data(self):
        max_interval = max(self.config.interval_one, self.config.interval_two)
        data = self.retriever.get_daily()
        data_one, data_two = [data[k] for k in data]
        self.init_data = [data_one[:max_interval], data_two[:max_interval]]
        self.testing_data = [data_one[max_interval:], data_two[max_interval:]]

    def _initialize_algo(self):
        data_one, data_two = self.init_data 
        self.algorithm.initialize(data_one, data_two)

    def trade(self, asset_dic: Dict[str, Union[Asset, QuoteAsset]]):
        self.evaluate(asset_dic)
        self.manage_risk(asset_dic)

    def assemble_asset_dic(self, data_one, data_two):
        return {self.config.symbols[0]: data_one, self.config.symbols[1]: data_two}

    def backtest(self):
        for data_one, data_two in zip(self.testing_data[0], self.testing_data[1]):
            asset_dic = self.assemble_asset_dic(data_one, data_two)
            self.trade(asset_dic)

    def get_strategy_returns(self):
        # Calculate daily returns of the strategy's account value
        # For simplicity, use the sum of long and short values as the strategy value
        values = []
        dates = []
        for data_one, data_two in zip(self.testing_data[0], self.testing_data[1]):
            asset_dic = self.assemble_asset_dic(data_one, data_two)
            value = self.longs.calculate_value(asset_dic) + self.shorts.calculate_value(asset_dic)
            # Use the date from one of the assets (assuming both have the same date)
            date = data_one.date if hasattr(data_one, 'date') else None
            values.append(value)
            dates.append(date)
        values = pd.Series(values, index=pd.to_datetime(dates))
        returns = values.pct_change().dropna().squeeze()
        return returns

    def get_benchmark_returns(self, symbol='SPY'):
        # Fetch benchmark (e.g., SPY) adjusted close prices for the test period
        start = self.config.lower_range or '2018-01-01'
        end = self.config.upper_range or pd.Timestamp.today().strftime('%Y-%m-%d')
        data = yf.download(symbol, start=start, end=end)
        prices = data['Close']
        prices.index = pd.to_datetime(prices.index)
        returns = prices.pct_change().dropna().squeeze()
        return returns

    def calculate_alpha_beta(self, strategy_returns, benchmark_returns):
        # Align indices
        common_index = strategy_returns.index.intersection(benchmark_returns.index)
        strategy_returns = strategy_returns.loc[common_index]
        benchmark_returns = benchmark_returns.loc[common_index]
        df = pd.DataFrame({'strategy': strategy_returns, 'benchmark': benchmark_returns}).dropna()
        if df.empty:
            print('No overlapping returns for alpha/beta calculation.')
            return None, None, None
        X = sm.add_constant(df['benchmark'])
        y = df['strategy']
        model = sm.OLS(y, X).fit()
        alpha = model.params['const']
        beta = model.params['benchmark']
        return alpha, beta, model

    def results(self):
        self.evaluate_results()
        print('Long Profit:', self.long_profit)
        print('Long Value:', self.long_value)
        print('Short Profit', self.short_profit)
        print('Short Value', self.short_value)
        print('ROI:', (self.long_value + self.short_value)/self.account.starting_cash)
        # Alpha/Beta calculation
        strategy_returns = self.get_strategy_returns()
        benchmark_returns = self.get_benchmark_returns()
        print("Strategy returns index:", strategy_returns.index)
        print("Benchmark returns index:", benchmark_returns.index)
        print("Common index:", strategy_returns.index.intersection(benchmark_returns.index))
        alpha, beta, model = self.calculate_alpha_beta(strategy_returns, benchmark_returns)
        if alpha is not None and beta is not None:
            print(f"Strategy Alpha (annualized): {alpha * 252:.4f}")
            print(f"Strategy Beta: {beta:.4f}")
        else:
            print("Alpha/Beta could not be calculated.")

    def evaluate_results(self):
        data_one, data_two = self.testing_data[0][-1], self.testing_data[1][-1]
        asset_dic = self.assemble_asset_dic(data_one, data_two)
        self.evaluate_long(asset_dic)
        self.evaluate_short(asset_dic)

    def evaluate_long(self, asset_dic):
        self._long_profit = self.longs.calculate_profit(asset_dic)
        self._long_value = self.longs.calculate_value(asset_dic) 
        
    def evaluate_short(self, asset_dic):
        self._short_profit = self.shorts.calculate_profit(asset_dic)
        self._short_value = self.shorts.calculate_value(asset_dic)

