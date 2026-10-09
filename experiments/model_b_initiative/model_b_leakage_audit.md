# Model B Initiative: Data Leakage, Temporal Validity, and Integrity Audit

**Project**: Drishti Macro-Econometric Supply Chain Cascade  
**Scope**: Model B-1 (Agricultural Production & Yield Growth) & Model B-2 (Production Risk Classification)  
**Branch**: `ml-model-improvement-v2`  
**Execution Timestamp**: October 2026  
**Auditor**: Antigravity Empirical Validation Subsystem  
**Overall Status**: **PASSED (Zero Leakage Verified)**  

---

## 1. Executive Summary & Audit Checklist

This audit independently inspects the mathematical, structural, and temporal integrity of the controlled experiments conducted in `experiments/model_b_initiative/`.

| Audit Criterion | Verification Standard | Implementation Status | Findings & Evidence |
| :--- | :--- | :--- | :--- |
| **Temporal Isolation** | $\text{Train}_{\max} < \text{Val}_{\min} \le \text{Test}_{\min}$ | **PASSED** | Train strictly $\le 2021$; Val $= 2022$; Test $\ge 2023$. Zero test rows in training splits. |
| **Frozen Test Purity** | No test tuning or threshold optimization | **PASSED** | Model selection, hyperparameters, and quantiles fitted strictly on $\le 2021$ or Val $2022$. |
| **Target Leakage** | No concurrent agricultural outcomes in $X$ | **PASSED** | Realized $P_t, Y_t, \text{Risk}_t$ strictly excluded from feature matrix. |
| **Lag Timing** | Lag $t-1$ represents historical prior year | **PASSED** | Lags computed on unique `[HS4, Month]` annual panels before trade merge. |
| **Pseudo-Replication** | No intra-month trade row shift leakage | **PASSED** | Eliminated risk of `shift(1)` pointing to adjacent trade partners in the same month. |
| **Area Predetermination**| Sown area $A_t$ is observed at planting | **PASSED** | Acreage $A_t$ observed at sowing (MoAFW sowing reports) months prior to harvest. |
| **Downstream Integrity** | Models A, C, D and core pipeline untouched | **PASSED** | Candidates saved strictly in `experiments/model_b_initiative/models/`. |

---

## 2. Temporal Boundary Isolation

The experimental pipeline enforces strict temporal barriers across all training and evaluation passes:

```
+---------------------------------------------------------------------------------------+
|  CHRONOLOGICAL TIMELINE                                                               |
|                                                                                       |
|  [ 1997 -------------- 2021 ]          [ 2022 ]                 [ 2023 ]              |
|        TRAINING PERIOD                 VALIDATION PERIOD         FROZEN TEST PERIOD   |
|        N = 11,360 trade rows           N = 2,942 trade rows      N = 661 trade rows   |
|        N = 888 crop-season cells       N = 239 crop-season cells N = 57 crop cells    |
|        (Fit models, Scalers, Labels)   (Tune thresholds/eval)   (Zero tuning; pure)   |
+---------------------------------------------------------------------------------------+
```

### Verification Checks:
1. **No Lookahead Leakage**: No data from 2022 or 2023 is present during scaler fitting (`StandardScaler().fit(X_train)`), model parameter optimization, or label quartile boundary determination.
2. **Walk-Forward Validation**: In Track 4, rolling temporal validation evaluated 4 separate historical windows ($2020$ using $\le 2019$; $2021$ using $\le 2020$; $2022$ using $\le 2021$; $2023$ using $\le 2022$), ensuring every prediction step respected strict historical causality.

---

## 3. Prevention of Pseudo-Replicated Target Leakage

### The Threat
In the bilateral trade panel (`merged_b`), each national crop harvest is duplicated across an average of **12.64 trade rows** (e.g., Rice in October 2021 appears for trade with USA, UAE, Saudi Arabia, Nepal, Bangladesh, etc.).
- If a naive feature engineer sorts by `[HS4, Year, Month]` and calls `.shift(1)`, row $i-1$ is the **same year and month** from the preceding country row.
- The feature would therefore contain the **exact contemporaneous target value** from that same harvest month, causing artificial test performance (MAE $\approx 1.2\%$).

### The Implemented Defense
In `scripts/run_model_b_track3_4_ablations.py` and `scripts/run_model_b_track5_risk.py`:
1. The deduplicated table `crop_by_hs4` is constructed with **exactly one row per `(HS4, Year, Month)`**.
2. Grouping is applied strictly by `[HS4, Month]` and sorted by `Year`.
3. The operation `.shift(1)` is executed on this deduplicated table:
   $$\text{Lag1}(\text{Target})_{y, m} \equiv \text{Target}_{y-1, m}$$
   Row $y-1$ is strictly the harvest from the preceding year.
4. Only after true temporal lags are computed is `crop_by_hs4` left-joined into the bilateral trade panel.
5. **Audit Result**: Zero intra-month target leakage.

---

## 4. Predetermination of Information in Yield-Decomposed Forecasting

In Experiment **E1C**, total output is forecasted via the decomposition:

$$\hat{P}_t = A_t \times \hat{Y}_t$$

### Information Timing Audit:
- **Acreage $A_t$**: In Indian agriculture, sowing reports are published weekly by the Directorate of Economics and Statistics (DES) during the sowing window (June–July for Kharif, October–November for Rabi). By harvest time (October–November for Kharif, March–April for Rabi), final sown acreage $A_t$ is a known, predetermined state variable.
- **Yield Growth $\hat{Y}_t$**: Forecasted out-of-sample using only predetermined and exogenous variables:
  $$\hat{Y}_t = f(\text{Ag\_Yield\_Lag1}, \text{Ag\_Yield\_3Y\_Mean}, \text{Season}, \text{Trade\_Shares}, \text{GPR}, \text{FX}, \text{Disaster\_Index})$$
- Neither $A_t$ nor $\hat{Y}_t$ contains concurrent harvest output or future information.
- **Audit Result**: Statistically and economically valid forecasting decomposition.

---

## 5. Model B-2 Label Calculation Purity

### Scheme 1 (Original Raw Tonnage):
- Replicated faithfully for diagnostic benchmarking. The quantile boundaries ($q_{25} = -25.26$ t, $q_{50} = +19.53$ t) were documented as pathological because 2018 cold-start zero deviation inflated Class 2 to 96.3% of training rows, leading to the $0.00\%$ test accuracy anomaly.

### Scheme 2 (Relative Percentage Deviation):
- Baseline rolling mean is calculated strictly on **past 3 years** (`shift(1).rolling(3, min_periods=1).mean()`).
- The current year's harvest is **never included in the baseline mean**.
- Fixed agronomic thresholds ($\pm 5\%, -15\%$) are pre-specified domain constants, eliminating any dependence on future test set quantile distributions.

### Scheme 3 (Standardized Z-Score Anomaly):
- Historical mean $\mu_{c, \text{prior}}$ and standard deviation $\sigma_{c, \text{prior}}$ are computed via expanding window strictly over years prior to $t$ (`shift(1).expanding()`).
- No future test statistics leak into historical z-scores.

---

## 6. Cascade Interface Compatibility

All candidate models maintain strict compatibility with the downstream cascade:
- Candidate Model B-1 outputs standard YoY percentage growth for `Production_Growth_Pred`, the expected input for Model C (Commodity Price Elasticity).
- Candidate Model B-2 outputs standard categorical labels for `Production_Risk` (`"Low"`, `"Medium"`, `"High"`, `"Critical"`).
- Original trained artifacts (`model_b_production_yoy.joblib`, `model_b_yield_yoy.joblib`, `model_b_production_risk.joblib`) remain intact in `models/`.
- All candidate models are safely isolated in `experiments/model_b_initiative/models/`.
