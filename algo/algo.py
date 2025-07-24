import matplotlib.pyplot as plt 
import pandas as pd

from typing import List, Union, Dict

from .models.account import Account
from .models.assets import Asset, QuoteAsset
from .models.trade import TradeHolder
from .pipelines.algorithms import PairsTradingPipeline
from .pipelines.execution import LongExecutionPipeline, ShortExecutionPipeline
from .pipelines.retriever import TimeSeriesRetrieverPipeline
from .config import config, Config

ALGO_SELECTION = {
    'pairs': PairsTradingPipeline(config.interval_one, config.interval_two, config=config)
}


class AlgoTradingPipeline:

    def __init__(self, config: Config):
        self._account = Account(config.starting_cash)
        self._algorithm = ALGO_SELECTION[config.algorithm_type]
        self._longs = LongExecutionPipeline()
        self._shorts = ShortExecutionPipeline()
        self._retriver = TimeSeriesRetrieverPipeline(
            config.symbols, config.lower_range, config.upper_range)
        self.config = config
        self.open_positions = []  # Track open trades for exit logic

    @property
    def account(self):
        return self._account

    @property
    def algorithm(self):
        return self._algorithm

    @property
    def longs(self):
        return self._longs

    @property
    def shorts(self):
        return self._shorts

    @property
    def retriever(self):
        return self._retriver

    def initialize(self):
        self._initialize_algo()

    def _initialize_algo(self):
        data = self.retriever.get_daily()
        data_one, data_two = [data[k] for k in data]
        self.algorithm.initialize(data_one, data_two)

    def open_trades(self, trade_eval: Dict[str, str], asset_dic: Dict[str, Union[Asset, QuoteAsset]]):
        if not trade_eval: 
            return []
        asset_one_eval, asset_two_eval = trade_eval
        if asset_one_eval['trade_type'] == 'short':
            short_trade = self.shorts.execute_trade(
                asset_dic[asset_one_eval['symbol']], trade_prop=self.config.trade_prop, cash=self.account.cash)
            long_trade = self.longs.execute_trade(
                asset_dic[asset_two_eval['symbol']], trade_prop=self.config.trade_prop, cash=self.account.cash)
        else:
            short_trade = self.shorts.execute_trade(
                asset_dic[asset_two_eval['symbol']], trade_prop=self.config.trade_prop, cash=self.account.cash)
            long_trade = self.longs.execute_trade(
                asset_dic[asset_one_eval['symbol']], trade_prop=self.config.trade_prop, cash=self.account.cash)
        return [short_trade, long_trade]

    def update_account(self, trades: List[Union[Asset, QuoteAsset]]):
        for trade in trades:
            self.account.execute_trade(trade)

    def evaluate_trade(self, asset_one: Union[Asset, QuoteAsset], asset_two: Union[Asset, QuoteAsset]):
        self.algorithm.append(asset_one, asset_two)
        trade_eval = self.algorithm.evaluate_trade()
        return trade_eval

    def evaluate(self, asset_dic: Dict[str, Union[Asset, QuoteAsset]]):
        data_one, data_two = [asset_dic[k] for k in asset_dic]
        trade_eval = self.evaluate_trade(data_one, data_two)
        new_trades = self.open_trades(trade_eval, asset_dic)
        self.update_account(new_trades)
        # Track open positions for exit logic
        for trade in new_trades:
            if trade:
                self.open_positions.append(trade)
        # Check for exit condition
        self.close_trades(asset_dic)

    def close_trades(self, asset_dic: Dict[str, Union[Asset, QuoteAsset]]):
        # If abs(zscore) < exit_zscore, close all open positions
        zscore = abs(self.algorithm.zscore)
        exit_z = self.config.exit_zscore
        if zscore < exit_z and self.open_positions:
            print(f"[Z-Score Exit] Closing all positions: zscore={zscore:.4f} < exit_zscore={exit_z}")
            for trade in self.open_positions:
                # Close trade using the appropriate pipeline
                if trade.trade_type == 'long':
                    self.longs.trade_holder.get_trade(trade.id).close_trade(trade.asset.price)
                    self.longs.closed_holder.add_trade(trade)
                    self.longs.trade_holder.delete_trade(trade.id)
                elif trade.trade_type == 'short':
                    self.shorts.trade_holder.get_trade(trade.id).close_trade(trade.asset.price)
                    self.shorts.closed_holder.add_trade(trade)
                    self.shorts.trade_holder.delete_trade(trade.id)
                self.account.execute_trade(trade)
            self.open_positions = []

    def manage_risk(self, asset_dic: Dict[str, Union[Asset, QuoteAsset]]):
        closed_risky_longs = self.longs.manage_risk(asset_dic, self.config.stop_loss)
        closed_risky_shorts = self.shorts.manage_risk(asset_dic, self.config.stop_loss)
        all_trades = closed_risky_shorts + closed_risky_longs
        self.update_account(all_trades)
    
    def trade(self):
        asset_dic = self.retriever.get_quote()
        self.evaluate(asset_dic)
        self.manage_risk(asset_dic)
    


