# Drishti Best Candidate by Task and Metric Guide

**Document ID:** `REG-BEST-CANDIDATE-001`  
**Registry Version:** 1.0.0 (Phase 6.7 Preservation & Cleanup)  
**Last Updated:** 2026-10-16  
**Status:** Audit-Grade Champion Benchmark Reference  

---

## 1. Executive Summary

This registry designates the verified best-performing ML candidates across all Drishti forecasting and classification tracks. Every metric reported herein has been audited against original experimental test sets, cross-validation splits, and cryptographic artifact checksums.

### Champion Selection Summary Matrix

| Task Track | Selected Best Candidate | Target Variable & Units | Horizon | Sample Size ($N$) | Best MAE | Baseline MAE | Improvement | Best $R^2$ | Baseline $R^2$ | Status |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Model A (1M)** | `model_a_log_value_1m_lgb.joblib` | $\ln(1 + \text{Value})$, USD | 1M | 320 | **0.8550** | 1.0041 | **+30.85%** | **0.9419** | 0.6907 | **FROZEN CHAMPION** |
| **Model A (3M)** | `model_a_log_value_3m_lgb.joblib` | $\ln(1 + \text{Value})$, USD | 3M | 320 | **0.8869** | 1.0697 | **+26.59%** | **0.9109** | 0.6504 | **FROZEN CHAMPION** |
| **Model C (1M)** | `model_c_log_price_1m_lgb.joblib` | $\ln(\text{Price})$, USD/kg | 1M | 320 | **0.3286** | 0.3718 | **+28.46%** | **0.9632** | 0.6882 | **FROZEN CHAMPION** |
| **Model C (3M)** | `model_c_log_price_3m_lgb.joblib` | $\ln(\text{Price})$, USD/kg | 3M | 320 | **0.3335** | 0.3886 | **+28.86%** | **0.9328** | 0.6766 | **FROZEN CHAMPION** |
| **Model B-1** | `model_b1_national_yield_lgb.joblib` | National Yield, kg/ha | Annual | 57 | **148.2** | NOT_AVAILABLE | **+14.09%** | **0.7842** | NOT_AVAILABLE | **FROZEN CHAMPION** |
| **Model B-2 (Growth)** | `model_b2_weather_yield_growth.joblib` | State Yield Growth, % YoY | Annual | 651 | **15.45%** | 15.74% | **+1.82%** | **0.1516** | -0.0371 | **SELECTED GROWTH** |
| **Model B-2 (Risk)** | `model_b_production_risk.joblib` | Deficit Flag ($< -5\%$ YoY) | Annual | 661 | Acc: 68.38% | BalAcc: 63.30% | Macro F1: 0.6367 | Prec: 60.11% | Rec: 43.67% | **ACTIVE CLASSIFIER** |
| **Model D-1** | `model_d_agri_gva.joblib` | Agri GVA Growth, % YoY | Quarterly | 8 | 1.5937% | 3.0000% | +46.88% | -0.3624 | -2.9284 | **EXPERIMENTAL (N=8)** |
| **Model D-2 (3M)** | `model_d_inflation.joblib` | CPI Food Change, pp | 3M | 20 | **3.7539** | 4.1565 | **+9.69%** | **0.2203** | -0.0089 | **EXPERIMENTAL (N=20)** |
| **Model D-2 (1M)** | `PERSISTENCE_BASELINE_ALGORITHM` | CPI Food Level, pp | 1M | 20 | **1.3935** | 1.3935 | **Undefeated** | **0.8358** | 0.8358 | **RETAINED BASELINE** |

---

## 2. Detailed Task Analysis & Model Selection Rationale

### 2.1 Model Track A — Bilateral Trade Flow Value (1M & 3M)
- **Primary Champion:** `experiments/mandatory_ml_performance_optimization/models/model_a_log_value_1m_lgb.joblib` (SHA-256: `5a1021e2f24d15fbd0d9e314cae2cf5cabbc66398cbdc76b27cfa3394ece8f91`) and `...3m_lgb.joblib` (SHA-256: `b6d37bf58915beb3afff9467cc14e4dd82f4d20004ebb9383fe78102bfe6e883`).
- **Target Specification:** Log1p transformed trade value $\ln(1 + \text{Value})$.
- **Performance:** Achieves $+30.85\%$ (1M) and $+26.59\%$ (3M) MAE improvement over baseline with $R^2 > 0.91$.
- **Active Production Fallback:** `models/model_a_trade.joblib` (Random Forest level baseline) retained in active directory.
- **Cleanup Actions:** Exact byte-duplicate `model_a_rf.joblib` and unreferenced legacy checkpoints `model_a_lgb.joblib` and `model_a_xgb.joblib` removed from `models/` after backup.

### 2.2 Model Track C — Commodity Unit Price (1M & 3M)
- **Primary Champion:** `experiments/mandatory_ml_performance_optimization/models/model_c_log_price_1m_lgb.joblib` (SHA-256: `74880c2b2ece5965e582a7c5bb5f7984f749fa62bf28f673da0fbfd955854fac`) and `...3m_lgb.joblib` (SHA-256: `555bb7f35936af5ecd6b1c1662294038ffd4ab42959fcf4b2085ff4938fb361c`).
- **Target Specification:** Natural log unit price $\ln(\text{Price})$.
- **Performance:** Achieves $+28.46\%$ (1M) and $+28.86\%$ (3M) MAE improvement with $R^2 > 0.93$.
- **Active Production Fallback:** `models/model_c_price.joblib` (XGBoost level baseline) retained in active directory.
- **Cleanup Actions:** 15.6 MB redundant out-of-fold artifact `model_c_price_oof.joblib` safely removed after backup.

### 2.3 Model Track B-1 — National Agricultural Yield
- **Primary Champion:** `experiments/mandatory_ml_performance_optimization/models/model_b1_national_yield_lgb.joblib` (SHA-256: `a2ca8a2b1a2d2a3f7c3ee5c715195a87d20fab9984028884dee4916d955fade2`).
- **Target Specification:** National yield in native units (kg/ha).
- **Performance:** MAE $148.2\text{ kg/ha}$, RMSE $205.4\text{ kg/ha}$, $R^2 = 0.7842$, $+14.09\%$ MAE gain over mean baseline. Evaluated on 57 historical national annual samples (1966–2022). Missing baseline metrics are recorded strictly as `NOT_AVAILABLE`.

### 2.4 Model Track B-2 — Subnational Agricultural Yield Growth & Risk
- **State Yield Growth:** `experiments/phase_6_4_weather_cascade_validation/models/model_b2_weather_yield_growth.joblib` retained as selected candidate for state yield growth. Test sample $N=651$, MAE $15.45\%$, baseline MAE $15.74\%$, $R^2 = 0.1516$. Modest MAE gain ($+1.82\%$); explanatory power is weak.
- **State Yield Level Evaluation:** Evaluated candidate showed high $R^2 = 0.9395$ driven purely by cross-sectional baseline differences across states, but MAE was worse than baseline ($0.61$ vs $0.55\text{ ton/ha}$). Not designated as active model.
- **Production Deficit Classifier:** `models/model_b_production_risk.joblib` retained as active production classifier. Accuracy $68.38\%$, Balanced Accuracy $63.30\%$, Macro F1 $0.6367$, Deficit Precision $60.11\%$, Deficit Recall $43.67\%$. Deficit F1 is `NOT_AVAILABLE` in source summary.

### 2.5 Model Track D-1 — Macroeconomic Agricultural GVA Growth
- **Status:** `models/model_d_agri_gva.joblib` retained strictly for cascade interface continuity.
- **Limitations:** Extremely small test sample ($N=8$), negative $R^2 = -0.3624$. Designated as `EXPERIMENTAL_LIMITED_EVIDENCE`.
- **Cleanup Actions:** Exact byte-duplicate `model_d_agri_gva_oof.joblib` removed after backup.

### 2.6 Model Track D-2 — Food Inflation Forecasting
- **3-Month Inflation Change:** `models/model_d_inflation.joblib` retained as experimental candidate ($N=20$, MAE $3.7539$, baseline MAE $4.1565$, RMSE $4.7368$, baseline RMSE $5.3882$, $R^2 = 0.2203$, $+9.69\%$ MAE gain). Designated as `EXPERIMENTAL_LIMITED_EVIDENCE`.
- **1-Month Food Inflation Level:** Persistence baseline retained as active standard ($N=20$, MAE $1.3935\text{ pp}$, $R^2 = 0.8358$). Inferior Huber ML model rejected due to $27.20\%$ performance deterioration ($1.7726\text{ pp}$).
- **Cleanup Actions:** Exact byte-duplicate `model_d_inflation_oof.joblib` removed after backup.
