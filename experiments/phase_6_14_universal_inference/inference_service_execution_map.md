# Phase 6.14 — Inference Service Execution Map

**Project:** Drishti — Exposure-Aware Geopolitical Impact Assessment Framework  
**Phase:** 6.14 — Universal Geopolitical Event-to-ML Inference  
**Date:** 2026-10-18T13:45:00+05:30  
**Status:** Canonical Service Execution Map  

---

## 1. End-to-End Execution Flow

The canonical inference lifecycle in Drishti follows a strictly traceable 10-stage execution pipeline:

```
[1] User Event Query (Frontend: Dashboard / EventAnalysisPage)
 │
 ▼
[2] REST API POST /api/analyze (api/server.py)
 │   • Generates unique Scenario ID: scen-{timestamp}-{uuid}
 │   • Normalizes request payload
 │
 ▼
[3] Event Intelligence Agent (agents/event_intelligence_agent.py)
 │   • Ingests event text, country, commodity, trade direction
 │   • Queries GDELT DOC 2.0 (search_gdelt_news) with graceful rate-limit fallback
 │   • Computes Shock Intensity: abs(Goldstein) * ln(Mentions + 1) * multiplier
 │   • Resolves canonical 4-digit HS code
 │
 ▼
[4] Universal Event-to-Feature Engineering (drishti_mcp/tools/feature_engine.py)
 │   • Checks commodity domain (Agricultural HS 01-24 vs Out-of-Domain e.g. Cotton HS 5201)
 │   • Queries historical Comtrade/DGFT dataset under strict Date < T
 │   • Classifies corridor: OBSERVED (N≥3), PARTIALLY_OBSERVED (1≤N<3), UNOBSERVED (N=0)
 │   • Builds model-specific feature vectors:
 │     - build_model_a_features() -> 16-feat LGBM + 9-feat XGBoost
 │     - build_model_b_features() -> 26-feat B-1 Yield + 12-feat Macro B-2
 │     - build_model_c_features() -> 15-feat LGBM + Price series
 │     - build_model_d_features() -> 13-feat Macro Series
 │   • Computes SHA-256 input fingerprints
 │
 ▼
[5] Preserved & Composite Model Cascade (drishti_mcp/tools/ml_cascade_tool.py)
 │   • Executes 4 econometric stages under Fallback Estimator Policy:
 │     Stage A (Trade Flow 1M/3M):
 │       - Observed -> Preserved LightGBM 1M/3M Champions [MODEL_PREDICTION]
 │       - Unobserved -> Registered Exposure XGBoost / Fallback [FALLBACK_ESTIMATE]
 │       - Out-of-Domain -> Sectoral Elasticity Proxy [PROXY_ESTIMATE]
 │     Stage B (National Agricultural Production):
 │       - Preserved LightGBM B-1 Yield + Active Production YoY & Deficit Risk
 │     Stage C (Domestic Commodity Price 1M/3M):
 │       - Observed -> Preserved LightGBM 1M/3M Champions [MODEL_PREDICTION]
 │       - Unobserved -> Domestic Wholesale Persistence Baseline [FALLBACK_ESTIMATE]
 │       - Out-of-Domain -> Input-Cost Pass-Through Proxy [PROXY_ESTIMATE]
 │     Stage D (Macroeconomic Economy):
 │       - Active Regularized Ridge/Huber Macro Models [MODEL_PREDICTION]
 │   • Constructs Standard Prediction Contract objects for all stages
 │
 ▼
[6] Main Cascade Orchestrator (agents/orchestrator.py)
 │   • Receives authoritative Standard Prediction Contract
 │   • Assembles canonical analysis context
 │   • Distributes actual predictions to downstream agent network
 │
 ▼
[7] Downstream Multi-Agent Analysis:
 │   ├── Supply Chain Agent: NetworkX maritime routing & port HHI
 │   ├── Vulnerability Agent: District-level RAVS crop sensitivity (110k records)
 │   ├── Stakeholder Advisory Agent: Deterministic rules across 6 groups
 │   ├── Mitigation Action Agent: Grounded playbooks & analog matching
 │   └── Impact Interpretation Agent: Non-causal econometric LLM synthesis
 │
 ▼
[8] Canonical REST API Response (api/server.py)
 │   • Returns unified JSON containing predictions, agent results, coverage, provenance
 │
 ▼
[9] State Dispatch & Cache Synchronization (frontend/src/services/api.ts)
 │   • Stores latest authoritative response in session and memory
 │
 ▼
[10] Frontend Multi-View Rendering:
     ├── DashboardPage.tsx: Top KPI cards, forecast charts, model details
     ├── ImpactCascadePage.tsx: Stage-by-stage cascade flow with status badges
     ├── SupplyChainPage.tsx: Maritime graphs & port dependencies
     ├── VulnerabilityPage.tsx: Spatial district map & top sensitive areas
     ├── StakeholderPage.tsx: Distributional impact across 6 stakeholder tiers
     ├── MitigationPage.tsx: Time-horizon playbooks & grounded historical analogs
     └── ReportPage.tsx: Authoritative executive briefing & econometric tables
```

---

## 2. Invocations & Artifact Traceability Matrix

| Stage | Preserved Champion Artifact | Secondary Registered Model | Statistical Fallback / Sectoral Proxy | Inverse Transformation | Output Metric & Unit |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Model A (1M)** | `model_a_log_value_1m_lgb.joblib` | `model_a_trade.joblib` (XGBoost) | Sectoral Trade Elasticity Proxy ($\epsilon = 1.25$) | $\exp(\hat{y}) - 1.0$; Return % | Trade Flow % Return (1M) |
| **Model A (3M)** | `model_a_log_value_3m_lgb.joblib` | `model_a_trade.joblib` (Scaled) | Sectoral Trade Elasticity Proxy ($\epsilon = 1.50$) | $\exp(\hat{y}) - 1.0$; Return % | Trade Flow % Return (3M) |
| **Model B-1** | `model_b1_national_yield_lgb.joblib` | `model_b_production_yoy.joblib` | Sectoral Production Deflection Baseline | Linear / Identity | National Crop Yield Growth (%) |
| **Model B-2** | N/A (Classifier) | `model_b_production_risk.joblib` | Tuned Random Forest Deficit Classifier | Integer $\to$ Class Map | Deficit Risk (Low/Med/High/Crit) |
| **Model C (1M)** | `model_c_log_price_1m_lgb.joblib` | `model_c_price.joblib` (XGBoost) | Domestic Wholesale Persistence Baseline | $\exp(\hat{p})$; Return % | Domestic Wholesale Price % (1M) |
| **Model C (3M)** | `model_c_log_price_3m_lgb.joblib` | `model_c_price.joblib` (Scaled) | Domestic Wholesale Persistence Baseline | $\exp(\hat{p})$; Return % | Domestic Wholesale Price % (3M) |
| **Model D-1** | `model_d1_quarterly_gva_ridge.joblib`| `model_d_agri_gva.joblib` | MoSPI Quarterly GVA Trend Baseline | StandardScaler inverse | Agricultural GVA Growth (%) |
| **Model D-2** | `model_d2_inflation_change_3m_lgb.joblib`| `model_d_inflation.joblib` | CPI Food Inflation Persistence Baseline | Linear / Identity | Food Inflation Change (pp) |
