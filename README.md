# Pairs Trading in Python
A robust statistical arbitrage framework for cointegrated stock pairs. Forked and extended from AJeanis/Pairs-Trading.

## Overview
This project implements a statistical arbitrage strategy based on pairs trading, leveraging cointegration and mean-reversion principles. The framework has been significantly extended to evaluate multiple sector-specific pairs for robustness, and to provide quantitative risk-adjusted performance metrics using CAPM regression.

## Features
- **Multi-Sector Pairs Evaluation:** Systematically identifies and tests cointegrated stock pairs across various sectors, reducing sector-specific and asynchronous risk.
- **Statistical Arbitrage Strategy:** Executes long/short trades on pairs whose price ratio deviates from its historical mean, exploiting mean-reversion.
- **Dynamic Z-Score Thresholds:** Entry and exit signals are generated using optimized z-score thresholds, ensuring trades are only placed when deviations are statistically significant.
- **Alpha & Beta Calculation via CAPM:** The strategy's performance is quantitatively assessed by regressing returns against market benchmarks (e.g., S&P 500 ETF) to compute:
  - **Alpha:** Risk-adjusted outperformance above the market expectation.
  - **Beta:** Sensitivity of the strategy to market movements.
- **Backtesting & Benchmarking:** Includes comprehensive backtesting and comparison against risk-free assets (e.g., Treasury Notes) and market indices.

## Methodology
### Pair Selection & Cointegration Testing
- Download historical price data for a universe of stocks across multiple sectors.
- Test all possible pairs for cointegration using the Engle-Granger method.
- Select pairs with statistically significant cointegration and stationarity.

### Signal Generation
- Calculate the price ratio and rolling z-score for each selected pair.
- **Entry:** Open positions when z-score exceeds ±1.25.
- **Exit:** Close positions when z-score reverts within ±0.5.

### Risk & Performance Analysis
- Compute strategy returns and compare to market benchmarks.
- Run CAPM regression to extract alpha (excess return) and beta (market risk).
- Analyze performance across different sectors and time periods.

## Quick Start
1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
2. **Configure your strategy** in `algo/config.py` (set symbols, z-score thresholds, etc.)
3. **Run the backtest**
   ```bash
   python run_backtest.py
   ```
4. **Review results**
   - Performance metrics, trade logs, and plots are generated for analysis.

## Example: Calculating Alpha & Beta via CAPM
After running a backtest, the framework regresses strategy returns against a market benchmark (e.g., S&P 500 ETF) to compute:
- **Alpha:** Risk-adjusted outperformance
- **Beta:** Market sensitivity

## Attribution
- **Original Author:** Alexander Jeanis
- **Forked & Extended by:** [Your Name]
  - Multi-sector robustness
  - Alpha/beta/CAPM analytics
  - Z-score threshold optimization
  - Modular code and improved documentation

---