# Phase 11: Forecast Evaluation Metrics

## 1. Metrics Suite
InsightFlow AI computes mathematical forecast metrics across out-of-sample holdout partitions:

### 1. Mean Absolute Error (MAE)
$$\text{MAE} = \frac{1}{K} \sum_{k=1}^K |y_k - \hat{y}_k|$$
Primary selection metric due to robustness against outlier skew.

### 2. Root Mean Squared Error (RMSE)
$$\text{RMSE} = \sqrt{\frac{1}{K} \sum_{k=1}^K (y_k - \hat{y}_k)^2}$$
Penalizes larger forecast errors more heavily.

### 3. Mean Absolute Percentage Error (MAPE)
$$\text{MAPE} = \frac{100\%}{K} \sum_{k=1}^K \left| \frac{y_k - \hat{y}_k}{\max(|y_k|, 10^{-4})} \right|$$
Stabilized against division by zero for near-zero targets.

### 4. Symmetric Mean Absolute Percentage Error (sMAPE)
$$\text{sMAPE} = \frac{100\%}{K} \sum_{k=1}^K \frac{|y_k - \hat{y}_k|}{(|y_k| + |\hat{y}_k|)/2 + 10^{-4}}$$
Bounded between 0% and 200%, avoiding asymmetric penalties.

### 5. Relative Improvement over Baseline
$$\text{Improvement} = \frac{\text{MAE}_{\text{baseline}} - \text{MAE}_{\text{model}}}{\text{MAE}_{\text{baseline}}} \times 100\%$$
Quantifies whether the selected model outperforms a Naive/Seasonal Naive baseline.
