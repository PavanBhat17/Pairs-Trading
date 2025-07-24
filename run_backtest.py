from algo.backtest import BacktestAlgoTradingPipeline
from algo.config import config

if __name__ == '__main__':
    backtester = BacktestAlgoTradingPipeline(config)
    backtester.initialize()
    backtester.backtest()
    backtester.results()
