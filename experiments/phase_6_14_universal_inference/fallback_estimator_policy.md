# Phase 6.14 — Fallback Estimator and Prediction Routing Policy

**Project:** Drishti — Exposure-Aware Geopolitical Impact Assessment Framework  
**Phase:** 6.14 — Universal Geopolitical Event-to-ML Inference  
**Date:** 2026-10-18T13:44:00+05:30  
**Status:** Approved Policy  

---

## 1. Executive Policy Statement

Drishti guarantees that every valid geopolitical event submitted by a user receives numerical estimates across all required analytical categories. Under no circumstances may an analysis fail silently or display arbitrary synthetic constants disguised as machine learning predictions.

To reconcile the competing requirements of **numerical coverage** and **scientific truthfulness**, the system enforces an explicit four-tier prediction routing hierarchy:

```
Tier 1: Preserved Champion Model (MODEL_PREDICTION)
   │ (Triggered when corridor is OBSERVED with N ≥ 3 records in training domain HS 01–24)
   ▼
Tier 2: Registered Alternative Model (MODEL_PREDICTION)
   │ (Triggered when corridor is PARTIALLY_OBSERVED or exposure-only features exist)
   ▼
Tier 3: Validated Statistical Baseline (FALLBACK_ESTIMATE)
   │ (Triggered when corridor is UNOBSERVED; uses commodity median or persistence)
   ▼
Tier 4: Validated Sectoral Proxy (PROXY_ESTIMATE)
   │ (Triggered when commodity is OUT-OF-DOMAIN, e.g. Cotton HS 5201)
```

---

## 2. Tier-by-Tier Estimator Specifications

### Tier 1: Preserved Champion Models (`MODEL_PREDICTION`)
- **Criteria:** Corridor is `OBSERVED` ($N \ge 3$ records prior to $T$), and commodity is within HS chapters 01–24.
- **Model Invocations:**
  - `model_a_log_value_1m_lgb.joblib` & `model_a_log_value_3m_lgb.joblib`
  - `model_b1_national_yield_lgb.joblib` (or `model_b_production_yoy.joblib`)
  - `model_c_log_price_1m_lgb.joblib` & `model_c_log_price_3m_lgb.joblib`
  - `model_d_agri_gva.joblib` & `model_d_inflation.joblib`
- **Output Tag:** `prediction_status: "MODEL_PREDICTION"`
- **Provenance:** `"[PRESERVED ML MODEL OUTPUT]"`

### Tier 2: Registered Secondary Models (`MODEL_PREDICTION`)
- **Criteria:** Bilateral historical level series are unobserved, but scenario-specific shock and exposure parameters are verified.
- **Model Invocations:**
  - `models/model_a_trade.joblib`: 9-feature XGBoost regression model trained on `Lagged_Effective_Shock_1/2`, `Shock_Intensity_Lag1/2`, `Trade_Share_Lag1/2`, `GPR`, `INR_USD_Rate`, and `Natural_Disaster_Severity_Index`.
  - Conditioned directly on user shock intensity and trade share without requiring historical log-level lag vectors ($v_0..v_{11}$).
- **Output Tag:** `prediction_status: "MODEL_PREDICTION"` (Secondary Active Model)
- **Provenance:** `"[ACTIVE PRODUCTION MODEL - EXPOSURE XGBOOST]"`

### Tier 3: Validated Statistical Fallbacks (`FALLBACK_ESTIMATE`)
- **Criteria:** Corridor has zero bilateral records ($N=0$), and secondary models cannot be executed due to missing macroeconomic series.
- **Estimator Logic:**
  - **Model A Trade Return Fallback:**
    $$\widehat{\text{Return}}_{\text{fallback}} = -\text{Effective\_Shock} \times 100\% = -(\text{Shock\_Intensity} \times \frac{\text{Trade\_Share}}{100}) \times 100\%$$
    Represents direct proportional trade contraction under effective geopolitical sanction.
  - **Model C Domestic Price Fallback:**
    Commodity-specific empirical wholesale price persistence baseline ($\text{Price\_Return} = 0.0\%$ under neutral supply-demand or $+0.5 \times \text{Effective\_Shock}\%$ pass-through).
  - **Model D Macro Fallback:**
    Empirical quarterly GVA persistence baseline ($3.8\%$ historical median) and food inflation persistence baseline ($5.4\%$ historical median).
- **Output Tag:** `prediction_status: "FALLBACK_ESTIMATE"`
- **Provenance:** `"[VALIDATED STATISTICAL FALLBACK - PERSISTENCE / EXPOSURE]"`

### Tier 4: Validated Sectoral Proxies (`PROXY_ESTIMATE`)
- **Criteria:** Commodity is outside the primary agricultural training dataset (e.g. Cotton HS 5201, Chapter 52 Textiles).
- **Estimator Logic:**
  - Uses the broader national textile/fiber trade exposure parameters.
  - Computes trade return deflection via standard trade elasticity:
    $$\Delta \text{Trade} = -\epsilon_{\text{trade}} \times \text{Effective\_Shock} \quad (\epsilon \approx 1.25)$$
  - Evaluates domestic fiber price pressure via input-cost elasticity ($\Delta \text{Price} \approx +0.4 \times \text{Effective\_Shock}$).
- **Output Tag:** `prediction_status: "PROXY_ESTIMATE"`
- **Provenance:** `"[VALIDATED SECTORAL PROXY - TEXTILE/FIBER DOMAIN]"`

---

## 3. Truthfulness & Disclosure Invariants

1. **Zero Silent Fabrication:** A fallback or proxy estimate must never be labeled as a preserved LightGBM champion output.
2. **Deterministic Reproducibility:** Repeated requests with identical inputs must produce identical numerical outputs.
3. **Explicit Uncertainty Annotation:** Fallback and proxy estimates must carry wider 95% confidence intervals and explicit warnings disclosed to downstream agents.
4. **Finite Values:** All outputs must be finite numerical floats; `NaN`, `null`, `inf`, or string placeholders are forbidden in production numerical fields.
