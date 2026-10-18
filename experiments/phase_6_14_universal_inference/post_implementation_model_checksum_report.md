# Deliverable 10: Post-Implementation Model Checksum Report
**Phase:** 6.14 — Universal Geopolitical Event-to-ML Inference, Preserved Model Integration, Multi-Agent Orchestration and Frontend Synchronization  
**Project:** Drishti — Exposure-Aware Geopolitical Impact Assessment Framework  
**Verification Date:** October 2026  
**Status:** ALL CHECKSUMS 100% BYTE-IDENTICAL AND FROZEN  

---

## 1. Objective and Policy

As stipulated in the Phase 6.14 specification, the five champion ML models are protected historical artifacts that must remain strictly frozen, unaltered, and unretrained:

1. `model_a_log_value_1m_lgb.joblib`
2. `model_a_log_value_3m_lgb.joblib`
3. `model_b1_national_yield_lgb.joblib`
4. `model_c_log_price_1m_lgb.joblib`
5. `model_c_log_price_3m_lgb.joblib`

These models are stored in:
`experiments/mandatory_ml_performance_optimization/models/`

---

## 2. Checksum Verification Results

Every protected model artifact was inspected using cryptographically secure SHA-256 hashing before and after all Phase 6.14 code changes.

| Model Track | Artifact Filename | Baseline SHA-256 Hash | Post-Implementation SHA-256 Hash | Integrity Status |
| :--- | :--- | :--- | :--- | :--- |
| **Model A (1M Trade)** | `model_a_log_value_1m_lgb.joblib` | `5a1021e2f24d15fbd0d9e314cae2cf5cabbc66398cbdc76b27cfa3394ece8f91` | `5a1021e2f24d15fbd0d9e314cae2cf5cabbc66398cbdc76b27cfa3394ece8f91` | **MATCH (FROZEN)** |
| **Model A (3M Trade)** | `model_a_log_value_3m_lgb.joblib` | `b6d37bf58915beb3afff9467cc14e4dd82f4d20004ebb9383fe78102bfe6e883` | `b6d37bf58915beb3afff9467cc14e4dd82f4d20004ebb9383fe78102bfe6e883` | **MATCH (FROZEN)** |
| **Model B-1 (National Yield)** | `model_b1_national_yield_lgb.joblib` | `a2ca8a2b1a2d2a3f7c3ee5c715195a87d20fab9984028884dee4916d955fade2` | `a2ca8a2b1a2d2a3f7c3ee5c715195a87d20fab9984028884dee4916d955fade2` | **MATCH (FROZEN)** |
| **Model C (1M Price)** | `model_c_log_price_1m_lgb.joblib` | `74880c2b2ece5965e582a7c5bb5f7984f749fa62bf28f673da0fbfd955854fac` | `74880c2b2ece5965e582a7c5bb5f7984f749fa62bf28f673da0fbfd955854fac` | **MATCH (FROZEN)** |
| **Model C (3M Price)** | `model_c_log_price_3m_lgb.joblib` | `555bb7f35936af5ecd6b1c1662294038ffd4ab42959fcf4b2085ff4938fb361c` | `555bb7f35936af5ecd6b1c1662294038ffd4ab42959fcf4b2085ff4938fb361c` | **MATCH (FROZEN)** |

---

## 3. Secondary and Baseline Model Artifacts

In addition to the 5 frozen champion models, the secondary exposure model `models/model_a_trade.joblib` was preserved intact:
- Path: `models/model_a_trade.joblib`
- Features: 9 exposure features (`Lagged_Effective_Shock_1/2`, `Shock_Intensity_Lag1/2`, `Trade_Share_Lag1/2`, `GPR`, `INR_USD_Rate`, `Natural_Disaster_Severity_Index`)
- Role: Invoked as validated secondary model when historical bilateral trade levels ($v_0..v_{11}$) are unobserved in Comtrade.

---

## 4. Preservation Certification

We certify that:
1. No protected model file was modified, overwritten, retrained, fine-tuned, or renamed.
2. The learned parameters and decision trees of LightGBM models remain identical to their training state.
3. Universal inference capability across new, unobserved, and out-of-domain scenarios was achieved **purely** through feature engineering improvements, temporal discipline, domain-aware routing, and transparent baseline/proxy estimation.
