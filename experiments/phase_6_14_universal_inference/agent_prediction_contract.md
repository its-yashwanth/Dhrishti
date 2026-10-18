# Phase 6.14 — Standard Agent Prediction Contract

**Project:** Drishti — Exposure-Aware Geopolitical Impact Assessment Framework  
**Phase:** 6.14 — Universal Geopolitical Event-to-ML Inference  
**Date:** 2026-10-18T13:42:00+05:30  
**Status:** Canonical Data Contract  

---

## 1. Purpose and Authority

The **Standard Prediction Contract** establishes a strictly typed, authoritative schema for all quantitative predictions produced by the econometric inference engine and consumed across downstream agents (`SupplyChainAgent`, `VulnerabilityAgent`, `StakeholderAdvisoryAgent`, `MitigationActionAgent`, `ImpactInterpretationAgent`, `Orchestrator`), the FastAPI backend, and the React frontend.

Every model prediction—whether derived from a preserved LightGBM champion, an alternative registered model, a statistical fallback, or a sectoral proxy—must adhere to this contract.

---

## 2. JSON Schema Definition

```typescript
export type PredictionStatus = 
  | 'MODEL_PREDICTION' 
  | 'FALLBACK_ESTIMATE' 
  | 'PROXY_ESTIMATE'
  | 'UNAVAILABLE';

export interface StandardPredictionObject {
  scenario_id: string;                      // Unique UUID for current scenario
  event_id: string;                         // Hash / identifier of the input event
  model_id: string;                         // e.g., "model_a_1m", "model_b_prod", "model_c_1m", "model_d_gva"
  model_version: string;                    // Human-readable version (e.g. "LightGBM 1M Preserved Champion")
  source_model_id: string;                  // Exact artifact filename or fallback identifier
  value: number;                            // Finite numerical prediction (e.g. -14.25)
  unit: string;                             // e.g., "percent_return", "tonnes_per_ha", "growth_percent", "pp"
  forecast_horizon: string;                 // e.g., "1_MONTH", "3_MONTH", "ANNUAL", "1_QUARTER"
  prediction_method: string;                // e.g., "LIGHTGBM_INFERENCE", "EXPOSURE_XGBOOST", "PERSISTENCE_BASELINE"
  prediction_status: PredictionStatus;      // 'MODEL_PREDICTION' | 'FALLBACK_ESTIMATE' | 'PROXY_ESTIMATE'
  input_feature_fingerprint: string;        // SHA-256 hash of input feature values
  feature_coverage: string;                 // e.g., "16/16 features observed" or "Exposure-only features"
  data_provenance: string;                  // e.g., "[PRESERVED ML MODEL OUTPUT]" or "[VALIDATED STATISTICAL FALLBACK]"
  uncertainty: {
    confidence_interval_95_low: number;     // 95% CI Lower Bound
    confidence_interval_95_high: number;    // 95% CI Upper Bound
    mae_estimate: number;                   // Validation MAE of the underlying estimator
  };
  warnings: string[];                       // Operational / domain warnings (e.g. "Out-of-domain commodity")
  generated_at: string;                     // ISO-8601 Timestamp
}
```

---

## 3. Standard Field Specifications

| Field Name | Type | Description | Mandatory Example |
| :--- | :---: | :--- | :--- |
| `scenario_id` | `string` | Unique scenario session UUID | `"scen-20261018-b8a92f"` |
| `event_id` | `string` | Deterministic SHA-256 fingerprint of event parameters | `"evt-1001-russia-export"` |
| `model_id` | `string` | Canonical model identifier in Drishti cascade | `"model_a_1m"` |
| `model_version` | `string` | Explanatory title including freeze and track status | `"Model A LightGBM 1M (Preserved Champion)"` |
| `source_model_id` | `string` | Relative path to artifact or registered estimator | `"experiments/.../model_a_log_value_1m_lgb.joblib"` |
| `value` | `number` | **Always finite float**. Never `null` when status is valid. | `+18372.97` |
| `unit` | `string` | Standardized unit string | `"% return"` or `"% YoY"` or `"pp"` |
| `forecast_horizon` | `string` | Time horizon of the prediction | `"1_MONTH"` |
| `prediction_method` | `string` | Algorithmic execution mechanism | `"LIGHTGBM_INVERSE_LOG"` |
| `prediction_status` | `enum` | Provenance tier (`MODEL_PREDICTION`, `FALLBACK_ESTIMATE`, `PROXY_ESTIMATE`) | `"MODEL_PREDICTION"` |
| `input_feature_fingerprint` | `string` | Hex digest of feature dictionary | `"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"` |
| `feature_coverage` | `string` | Ratio / coverage summary | `"16/16 observed historical features"` |
| `data_provenance` | `string` | Human-facing provenance label | `"[PRESERVED ML MODEL OUTPUT]"` |
| `uncertainty` | `object` | CI-95 bounds and historical validation MAE | `{"ci_low": -12.4, "ci_high": -8.1, "mae": 0.855}` |
| `warnings` | `array` | Non-fatal diagnostic notes | `["Unobserved corridor: routed to exposure fallback"]` |
| `generated_at` | `string` | Execution timestamp | `"2026-10-18T13:42:00.000Z"` |

---

## 4. Downstream Consumption Rules

1. **Supply Chain Agent (`agents/supply_chain_agent.py`):**
   - Consumes `model_a_1m.value` and `model_a_1m.prediction_status`.
   - If `prediction_status === 'FALLBACK_ESTIMATE'`, applies wider sensitivity bands in network bottleneck simulation.
2. **Vulnerability Agent (`agents/vulnerability_agent.py`):**
   - Consumes `model_b_yield.value` and `model_b_deficit.value`.
   - Incorporates model uncertainty into district-level RAVS vulnerability scores.
3. **Stakeholder Advisory Agent (`agents/stakeholder_advisory_agent.py`):**
   - Consumes `value`, `unit`, and `prediction_status` for Models A, B, C, D across all 6 stakeholder group rules.
   - Explicitly cites `prediction_method` in advisory disclosures.
4. **Mitigation Action Agent (`agents/mitigation_action_agent.py`):**
   - Uses `value` and `uncertainty.mae_estimate` to calibrate emergency buffer stock releases and market diversification timelines.
5. **Impact Interpretation Agent & Frontend:**
   - Renders exact `value` with corresponding status badge.
   - Eliminates all hardcoded fallback values (`?? -2.18`, etc.).
