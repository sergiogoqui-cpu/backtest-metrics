from backtest_metrics import summary, STOCKS_DAILY
equity = [10_000, 10_150, 10_090, 10_400, 10_380, 10_700]
pnls = [150, -60, 310, -20, 320]
for k, v in summary(equity, pnls, periods_per_year=STOCKS_DAILY).items():
    print(f"{k:>22}: {v:.4f}" if isinstance(v, float) else f"{k:>22}: {v}")
