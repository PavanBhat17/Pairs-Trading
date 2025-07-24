import os

from dotenv import load_dotenv

load_dotenv()

class Config:

    alpha_api_key = os.getenv('ALPHA_API_KEY')
    

class DevelopmentConfig(Config):

    starting_cash = 100000
    interval_one = 5
    interval_two = 50
    stop_loss = .10
    algorithm_type = 'pairs'
    symbols = ['AMZN', 'TSLA']
    lower_range = '2018-04-01'
    upper_range = None
    trade_prop = .05
    entry_zscore = 1.0  # New: configurable entry threshold
    exit_zscore = 0.0   # New: configurable exit threshold

class ProductionConfig(Config):
    entry_zscore = 1.0
    exit_zscore = 0.0
    pass


config = DevelopmentConfig()