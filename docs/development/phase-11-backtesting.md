# Phase 11: Chronological Backtesting & Leakage Protection

## 1. Zero Lookahead Data Leakage Guarantee
Random train/test shuffling causes temporal leakage in time series. InsightFlow AI enforces strict chronological partitioning:
$$\text{Data} = [t_1, t_2, \dots, t_{\text{train}}] \parallel [t_{\text{train}+1}, \dots, t_N]$$

The validation partition is strictly out-of-sample:
- Size: $\max(2, \min(h, \lfloor N / 4 \rfloor))$ where $h$ is requested horizon and $N$ is total observations.
- All candidate models are fitted only on $[t_1 \dots t_{\text{train}}]$ and evaluated on $[t_{\text{train}+1} \dots t_N]$.
- Future actuals are never visible during fitting or hyperparameter selection.

## 2. Walk-Forward / Holdout Backtest Strategy
1. Baseline calculation: Naive or Seasonal Naive evaluated on the validation window.
2. Candidate generation: Registry builds candidate model instances.
3. Out-of-sample scoring: Point predictions are compared to known historical holdouts.
4. Selection rule: Lowest MAE model is selected.
5. Final Fit: The selected model is retrained on all available historical data ($1 \dots N$) to generate future predictions ($N+1 \dots N+h$).
