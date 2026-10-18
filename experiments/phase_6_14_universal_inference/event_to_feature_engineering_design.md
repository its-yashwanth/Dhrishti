# Phase 6.14 — Event-to-Feature Engineering Design Specification

**Project:** Drishti — Exposure-Aware Geopolitical Impact Assessment Framework  
**Phase:** 6.14 — Universal Geopolitical Event-to-ML Inference  
**Date:** 2026-10-18T13:40:00+05:30  
**Status:** Approved Architecture  

---

## 1. Overview and Core Philosophy

In geopolitical impact analysis, machine learning models cannot ingest raw headlines directly. Conversely, the absence of an exact historical match for a headline must not cause an analytical pipeline to abort or output arbitrary dummy constants.

The **Event-to-Feature Engineering Layer** bridges natural language geopolitics and econometric tabular models:
1. It ingests the structured event extracted by the Event Intelligence Agent.
2. It queries verified historical observations under strict chronological discipline ($Date < T$).
3. It derives mathematical shock, exposure, and volatility features using verified formulas from `derived_features.py` and `gdelt_final.py`.
4. It constructs schema-validated, model-specific tabular vectors for each registered model track.
5. It routes each request through the priority hierarchy:
   - **`MODEL_PREDICTION`**: Preserved LightGBM champion on observed data.
   - **`MODEL_PREDICTION` (Alternative)**: Registered secondary model (e.g. XGBoost exposure model).
   - **`FALLBACK_ESTIMATE`**: Validated statistical persistence or commodity median baseline.
   - **`PROXY_ESTIMATE`**: Validated broader-domain proxy for out-of-domain commodities (e.g. Cotton HS 5201).

---

## 2. Reusable Modular Feature Builders

Rather than generating features inside monolithic scripts, Phase 6.14 formalizes four explicit inference-time feature builders in `drishti_mcp/tools/feature_engine.py`:

```
                       ┌───────────────────────────────┐
                       │   Structured Event Context    │
                       │ (Country, Direction, HS4, etc)│
                       └──────────────┬────────────────┘
                                      │
               ┌──────────────────────┴──────────────────────┐
               ▼                                             ▼
    ┌─────────────────────┐                       ┌─────────────────────┐
    │  Historical Cache   │                       │ Macro Series Cache  │
    │  (Comtrade / DGFT)  │                       │   (RBI, MoSPI, GPR) │
    └──────────┬──────────┘                       └──────────┬──────────┘
               │                                             │
               └──────────────────────┬──────────────────────┘
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          ▼                           ▼                           ▼
┌───────────────────┐       ┌───────────────────┐       ┌───────────────────┐
│build_model_a_feat │       │build_model_b_feat │       │build_model_c_feat │
│• 16 LGBM features │       │• 26 Agronomic B-1 │       │• 15 LGBM features │
│• 9 XGB features   │       │• 12 Macro B-2     │       │• 11 Baseline feat │
└───────────────────┘       └───────────────────┘       └───────────────────┘
```

### 2.1 `build_model_a_features(event_dict, historical_context)`
- **Input Parameters:**
  - `country`: Foreign partner country string (e.g. `'BANGLADESH'`, `'RUSSIA'`).
  - `trade_type`: Direction from India's perspective (`'Export'` vs `'Import'`).
  - `hs4`: 4-digit Harmonized System code (e.g. `1001` for Wheat).
  - `event_date`: Forecast origin date string (e.g. `'2024-01-15'`).
  - `shock_intensity`: Event shock magnitude ($\ge 0$).
  - `trade_share`: Bilateral corridor trade share percentage ($[0, 100]$).
- **Extracted Vectors:**
  1. `features_a_lgb` (16 features):
     - `Log_Value_Lag0..11`: Derived from historical monthly records strictly where $Date < T$.
     - `Past_Return_1M`: $v_0 - v_1$.
     - `Roll_Means`: Rolling 3M, 6M, 12M means of `Log_Value_USD`.
     - `Month_Sin`, `Month_Cos`: $\sin(2\pi m / 12)$, $\cos(2\pi m / 12)$.
     - `GPR`, `INR_USD_Rate`: Synchronous macro indicators at origin date $T$.
     - `Shock_Intensity_Lag1`, `Trade_Share_Lag1`.
  2. `features_a_xgb` (9 features):
     - Exposure-only feature set: `Lagged_Effective_Shock_1/2`, `Shock_Intensity_Lag1/2`, `Trade_Share_Lag1/2`, `GPR`, `INR_USD_Rate`, `Natural_Disaster_Severity_Index`.
     - Can be constructed even when historical corridor lag levels are partially observed or unobserved.

### 2.2 `build_model_b_features(event_dict, historical_context)`
- **Extracts two distinct feature representations:**
  1. `features_b1_national_yield` (26 features):
     - Ingests crop panel data from `Crop_Production_Final.csv` for the specific crop associated with the HS4 code.
     - Computes national historical yield lags (`Yield_Lag1..3`), rolling stats (`Yield_3Y_Med/Mean/Std`), trend slopes (`Yield_Trend_Slope`, `Yield_Short_Trend`), yield coefficient of variation (`Yield_CV`), YoY lags, and seasonal flags.
     - Combines with lagged effective shock and macroeconomic variables.
  2. `features_b2_macro_deflection` (12 features):
     - Conditioned on effective shock ($\text{Shock} \times \text{Share} / 100$) and macro climate to evaluate aggregate Indian crop output deflection and deficit risk.

### 2.3 `build_model_c_features(event_dict, historical_context)`
- **Input Parameters:** Same event attributes + historical price series.
- **Extracted Vectors:**
  - `features_c_lgb` (15 features):
    - `Log_Price_Lag0..11`: Derived from historical commodity wholesale unit prices strictly where $Date < T$.
    - `Past_Price_Return_1M`: $p_0 - p_1$.
    - `Roll_Means`: Rolling 3M, 6M, 12M means of `Log_Unit_Price`.
    - `Month_Sin`, `Month_Cos`, `GPR`, `INR_USD_Rate`, `Shock_Intensity_Lag1`.

### 2.4 `build_model_d_features(event_dict, historical_context, upstream_preds)`
- **Input Parameters:** Macro indicators + upstream Model C price return.
- **Extracted Vectors:**
  - 13 features: `Inflation_Lag1`, `Agri_GVA_Lag1`, `GDP_Lag1`, `Price_Lag1`, `Shock_Intensity_Lag1/2`, `Trade_Share_Lag1/2`, `Lagged_Effective_Shock_1/2`, `GPR`, `INR_USD_Rate`, and `Price_Return_1M_Pred_Lag1`.

---

## 3. Mathematical Exposure Formulas (Reused from `derived_features.py`)

All feature derivations directly match the verified training formulas:

1. **Trade Share:**
   $$\text{Trade\_Share} = \frac{\text{Value\_USD}_{\text{country, hs4, type}}}{\sum_{\text{hs4}} \text{Value\_USD}_{\text{country, type}}} \times 100$$
2. **Effective Shock:**
   $$\text{Effective\_Shock} = \text{Shock\_Intensity} \times \left(\frac{\text{Trade\_Share}}{100}\right)$$
3. **Directional Shock Exposure:**
   $$\text{Incoming\_Shock\_Exposure} = \text{Incoming\_Shock\_Count} \times \left(\frac{\text{Trade\_Share}}{100}\right)$$
   $$\text{Outgoing\_Shock\_Exposure} = \text{Outgoing\_Shock\_Count} \times \left(\frac{\text{Trade\_Share}}{100}\right)$$
   $$\text{Net\_Hostility\_Exposure} = (\text{Outgoing} - \text{Incoming}) \times \left(\frac{\text{Trade\_Share}}{100}\right)$$
4. **Log Transformation:**
   $$\text{Log\_Value\_USD} = \ln(1 + \text{Value\_USD})$$
   $$\text{Log\_Unit\_Price} = \ln(\max(10^{-4}, \text{Unit\_Price\_USD\_per\_KG}))$$
5. **Inverse Transformation:**
   $$\widehat{\text{Value\_USD}} = \exp(\hat{y}_{\log}) - 1.0$$
   $$\text{Trade\_Return\_1M} = \frac{\widehat{\text{Value\_USD}} - \text{Value\_USD}_t}{\text{Value\_USD}_t} \times 100\%$$
   $$\widehat{\text{Unit\_Price}} = \exp(\hat{p}_{\log})$$
   $$\text{Price\_Return\_1M} = \frac{\widehat{\text{Unit\_Price}} - \text{Unit\_Price}_t}{\text{Unit\_Price}_t} \times 100\%$$

---

## 4. Domain & Coverage Decision Matrix

| Case | Scenario Condition | Model A Route | Model B Route | Model C Route | Model D Route |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **Case A** | Observed corridor ($N \ge 3$) & HS 01–24 | Preserved LightGBM (`MODEL_PREDICTION`) | Preserved LightGBM B-1 (`MODEL_PREDICTION`) | Preserved LightGBM (`MODEL_PREDICTION`) | Model D Active (`MODEL_PREDICTION`) |
| **Case B** | New event in observed corridor | Fresh feature vector -> Preserved LightGBM | Fresh event features -> Preserved B-1 | Fresh event features -> Preserved LightGBM | Fresh upstream input -> Model D |
| **Case C** | Unobserved bilateral corridor ($N=0$), HS 01–24 | Model A XGBoost Exposure Model or Commodity Median Baseline (`FALLBACK_ESTIMATE`) | Active Production YoY & Deficit Risk (`MODEL_PREDICTION`) | Commodity Wholesale Persistence Baseline (`FALLBACK_ESTIMATE`) | Macro Baseline (`MODEL_PREDICTION`) |
| **Case D** | Out-of-Domain Commodity (e.g. Cotton HS 5201) | Sectoral Trade Elasticity Baseline (`PROXY_ESTIMATE`) | Sectoral Production Proxy Baseline (`PROXY_ESTIMATE`) | Wholesale Price Index Persistence (`PROXY_ESTIMATE`) | Macro Baseline (`MODEL_PREDICTION`) |
| **Case E** | Missing macro or temporal series | RBI/MoSPI Median Imputation with Warning | Crop Area Mean Imputation with Warning | National Food Price Imputation | Empirical Series Persistence |
