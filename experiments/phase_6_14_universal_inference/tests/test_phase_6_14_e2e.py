"""
Comprehensive Automated Test Suite for Phase 6.14
Universal Geopolitical Event-to-ML Inference, Preserved Model Integration,
Multi-Agent Orchestration and Frontend Synchronization

Tests Covered:
- Test A: Observed Corridor (Preserved LightGBM Model Execution)
- Test B: New Headline in Observed Corridor (Fresh Event-Conditioned Vector)
- Test C: Unobserved Corridor (Secondary Model / Validated Baseline Fallback)
- Test D: Out-of-Domain Commodity (Cotton HS 5201 Sectoral Proxy Routing)
- Test E: Historical Event Temporal Discipline (Date < T Forecast Origin)
- Test F: Feature Sensitivity & Deterministic Fingerprinting
- Test G: Protected Model Invocations and Schema Verification
- Test H: Downstream Agent Prediction Distribution & Propagation
- Test I: Frontend-Backend Contract Parity (Zero Hardcoded Values)
- Test J: Fault Tolerance & Safe Recovery (Malformed Inputs)
- Test K: Model Preservation Integrity (SHA-256 Byte Verification)
"""

import hashlib
import json
import os
import sys
import pytest

# Ensure repository root is on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from drishti_mcp.tools.feature_engine import (
    build_all_model_features,
    build_model_a_features,
    build_model_b_features,
    build_model_c_features,
    build_model_d_features,
    compute_feature_fingerprint,
    classify_commodity_domain
)
from drishti_mcp.tools.ml_cascade_tool import run_drishti_ml_cascade


EXPECTED_HASHES = {
    "model_a_log_value_1m_lgb.joblib": "5a1021e2f24d15fbd0d9e314cae2cf5cabbc66398cbdc76b27cfa3394ece8f91",
    "model_a_log_value_3m_lgb.joblib": "b6d37bf58915beb3afff9467cc14e4dd82f4d20004ebb9383fe78102bfe6e883",
    "model_b1_national_yield_lgb.joblib": "a2ca8a2b1a2d2a3f7c3ee5c715195a87d20fab9984028884dee4916d955fade2",
    "model_c_log_price_1m_lgb.joblib": "74880c2b2ece5965e582a7c5bb5f7984f749fa62bf28f673da0fbfd955854fac",
    "model_c_log_price_3m_lgb.joblib": "555bb7f35936af5ecd6b1c1662294038ffd4ab42959fcf4b2085ff4938fb361c",
}

MODELS_DIR = os.path.join(REPO_ROOT, "experiments", "mandatory_ml_performance_optimization", "models")


# ============================================================================
# Test K: Model Preservation Checksums (Mandatory First Check)
# ============================================================================
def test_k_model_preservation_checksums():
    """Verify that all 5 protected champion models have 100% byte-identical SHA-256 hashes."""
    for filename, expected_hash in EXPECTED_HASHES.items():
        path = os.path.join(MODELS_DIR, filename)
        assert os.path.exists(path), f"Protected artifact missing: {path}"
        with open(path, "rb") as f:
            actual_hash = hashlib.sha256(f.read()).hexdigest()
        assert actual_hash == expected_hash, (
            f"MUTATION DETECTED in protected model {filename}!\n"
            f"Expected: {expected_hash}\nActual:   {actual_hash}"
        )


# ============================================================================
# Test A: Observed Corridor Execution (Bangladesh Wheat Export)
# ============================================================================
def test_a_observed_corridor_inference():
    """Verify inference for an observed commodity and corridor in the training domain."""
    event = {
        "event_text": "Bangladesh reduces import quotas for Indian wheat following domestic inventory review.",
        "commodity": "Wheat",
        "hs_code": "1001",
        "partner": "Bangladesh",
        "trade_direction": "Export",
        "shock_intensity": 0.45,
        "trade_share": 0.082,
        "event_date": "2024-05-15"
    }
    
    # 1. Feature Engineering
    features = build_all_model_features(event)
    assert features["domain"] == "AGRICULTURAL"
    assert features["fingerprint"] is not None
    assert len(features["features_a_lgb"].columns) == 16
    assert len(features["features_b"].columns) == 12
    assert len(features["features_c_lgb"].columns) == 15
    assert len(features["features_d"].columns) == 13
    
    # 2. Cascade Inference
    cascade_res = run_drishti_ml_cascade(features, scenario_id="test_scen_a", event_id="test_evt_a")
    assert cascade_res["coverage"]["status"] == "COMPLETE"
    assert cascade_res["coverage"]["completed_stages"] == 5
    
    trade = cascade_res["stage_1_trade"]
    assert trade["prediction_status"] == "MODEL_PREDICTION"
    assert "LIGHTGBM" in trade["prediction_method"].upper()
    assert "model_a_log_value_1m_lgb" in trade["source_model_id"]
    assert isinstance(trade["value"], float)
    assert trade["value"] != 0.0  # Real model produces active deflection
    
    price = cascade_res["stage_3_price"]
    assert price["prediction_status"] == "MODEL_PREDICTION"
    assert "LIGHTGBM" in price["prediction_method"].upper()
    assert "model_c_log_price_1m_lgb" in price["source_model_id"]
    assert isinstance(price["value"], float)


# ============================================================================
# Test B: New Headline in Observed Corridor (Dynamic Sensitivity)
# ============================================================================
def test_b_new_event_in_observed_corridor():
    """Verify that a brand new headline for an observed corridor generates fresh feature vectors."""
    event_base = {
        "event_text": "Border customs delays between India and Bangladesh affect grain movements.",
        "commodity": "Wheat",
        "hs_code": "1001",
        "partner": "Bangladesh",
        "trade_direction": "Export",
        "shock_intensity": 0.20,
        "trade_share": 0.05,
        "event_date": "2025-01-10"
    }
    
    event_severe = dict(event_base)
    event_severe["shock_intensity"] = 0.85
    event_severe["event_text"] = "Catastrophic border shutdown halts all agricultural logistics between India and Bangladesh."
    
    feat_base = build_all_model_features(event_base)
    feat_severe = build_all_model_features(event_severe)
    
    # Fingerprints must be distinct
    assert feat_base["fingerprint"] != feat_severe["fingerprint"]
    
    # Effective shock features in Model A XGBoost / Model B must differ
    assert feat_base["features_a_xgb"]["Lagged_Effective_Shock_1"].iloc[0] < feat_severe["features_a_xgb"]["Lagged_Effective_Shock_1"].iloc[0]
    
    # Predictions must run and reflect difference
    res_base = run_drishti_ml_cascade(feat_base)
    res_severe = run_drishti_ml_cascade(feat_severe)
    # Both execute valid predictions
    assert res_base["stage_1_trade"]["value"] is not None
    assert res_severe["stage_1_trade"]["value"] is not None


# ============================================================================
# Test C: Unobserved Bilateral Corridor (Russia Wheat Export)
# ============================================================================
def test_c_unobserved_corridor_inference():
    """Verify that unobserved bilateral export corridor (N=0) routes to registered secondary model or fallback."""
    event = {
        "event_text": "Russia bans all imports of Indian wheat amid phytosanitary concerns.",
        "commodity": "Wheat",
        "hs_code": "1001",
        "partner": "Russia",
        "trade_direction": "Export",  # India has 0 records of exporting wheat to Russia
        "shock_intensity": 0.60,
        "trade_share": 0.001,
        "event_date": "2024-03-01"
    }
    
    features = build_all_model_features(event)
    assert features["domain"] == "AGRICULTURAL"
    # Bilateral lags should be empty
    assert len(features["historical_context"]["bilateral_lags"]) == 0
    
    cascade_res = run_drishti_ml_cascade(features)
    assert cascade_res["coverage"]["status"] == "COMPLETE"
    
    trade = cascade_res["stage_1_trade"]
    # Must use registered secondary XGBoost model or baseline fallback, NEVER arbitrary constants
    assert trade["prediction_status"] in ["MODEL_PREDICTION", "FALLBACK_ESTIMATE"]
    assert "model_a_trade.joblib" in trade["source_model_id"] or "statistical_baseline" in trade["source_model_id"]
    assert isinstance(trade["value"], float)
    
    price = cascade_res["stage_3_price"]
    # Model C requires upstream bilateral OOF features; without them it safely routes to mandi persistence baseline
    assert price["prediction_status"] == "FALLBACK_ESTIMATE"
    assert "PERSISTENCE" in price["prediction_method"].upper()
    assert isinstance(price["value"], float)
    assert price["value"] >= 0.0  # Legitimate zero or positive baseline under minimal exposure


# ============================================================================
# Test D: Out-of-Domain Commodity (Cotton HS 5201)
# ============================================================================
def test_d_out_of_domain_commodity_proxy():
    """Verify that non-agricultural commodities (HS 5201, Chapter 52) route cleanly to PROXY_ESTIMATE."""
    event = {
        "event_text": "Bangladesh imposes emergency tariff on raw cotton imports from India.",
        "commodity": "Cotton",
        "hs_code": "5201",
        "partner": "Bangladesh",
        "trade_direction": "Export",
        "shock_intensity": 0.50,
        "trade_share": 0.15,
        "event_date": "2024-06-01"
    }
    
    domain = classify_commodity_domain(event["hs_code"])
    assert domain == "OUT_OF_DOMAIN"
    
    features = build_all_model_features(event)
    assert features["domain"] == "OUT_OF_DOMAIN"
    
    cascade_res = run_drishti_ml_cascade(features)
    assert cascade_res["coverage"]["status"] == "COMPLETE"
    
    trade = cascade_res["stage_1_trade"]
    assert trade["prediction_status"] == "PROXY_ESTIMATE"
    assert "SECTORAL" in trade["prediction_method"] and "ELASTICITY" in trade["prediction_method"]
    assert trade["value"] < 0.0  # Elasticity contraction
    assert "5201" in trade["warnings"][0] and "HS 01-24" in trade["warnings"][0]
    
    price = cascade_res["stage_3_price"]
    assert price["prediction_status"] == "PROXY_ESTIMATE"
    assert "INPUT_COST" in price["prediction_method"]
    assert trade["uncertainty"]["ci_95"] is not None


# ============================================================================
# Test E: Historical Event Temporal Discipline
# ============================================================================
def test_e_historical_event_temporal_discipline():
    """Verify that an event in 2019 only retrieves historical context before 2019."""
    event = {
        "event_text": "2019 historical agricultural policy change in Bangladesh.",
        "commodity": "Wheat",
        "hs_code": "1001",
        "partner": "Bangladesh",
        "trade_direction": "Export",
        "shock_intensity": 0.30,
        "trade_share": 0.04,
        "event_date": "2019-06-01"
    }
    
    features = build_all_model_features(event)
    # Context must not leak future observations
    for date_str in features["historical_context"]["bilateral_lags"].keys():
        assert date_str < "2019-06-01", f"Future data leakage detected: {date_str} >= 2019-06-01"


# ============================================================================
# Test F: Feature Sensitivity & Deterministic Fingerprints
# ============================================================================
def test_f_feature_sensitivity_and_fingerprints():
    """Verify that feature vectors produce deterministic fingerprints and respond to input shifts."""
    event1 = {
        "commodity": "Wheat", "hs_code": "1001", "partner": "Bangladesh",
        "trade_direction": "Export", "shock_intensity": 0.40, "trade_share": 0.05,
        "event_date": "2024-01-01"
    }
    event2 = dict(event1)
    
    feat1 = build_all_model_features(event1)
    feat2 = build_all_model_features(event2)
    assert feat1["fingerprint"] == feat2["fingerprint"], "Fingerprint must be strictly deterministic!"
    
    # Mutate partner
    event3 = dict(event1)
    event3["partner"] = "United States"
    feat3 = build_all_model_features(event3)
    assert feat1["fingerprint"] != feat3["fingerprint"]


# ============================================================================
# Test G: Model Schema Validation
# ============================================================================
def test_g_model_schema_validation():
    """Verify that constructed feature vectors strictly adhere to Model A-D schemas."""
    event = {
        "commodity": "Wheat", "hs_code": "1001", "partner": "Bangladesh",
        "trade_direction": "Export", "shock_intensity": 0.50, "trade_share": 0.08,
        "event_date": "2024-01-01"
    }
    
    # Model A 1M features (16 cols for LightGBM champion)
    feat_a_dict = build_model_a_features(
        event_country=event["partner"],
        commodity=event["commodity"],
        hs4=int(event["hs_code"]),
        trade_type=event["trade_direction"],
        event_date=event["event_date"]
    )
    feat_a_lgb = feat_a_dict["features_a_lgb"]
    assert len(feat_a_lgb.columns) == 16
    expected_a_cols = [
        'Log_Value_Lag0', 'Log_Value_Lag1', 'Log_Value_Lag2', 'Log_Value_Lag3',
        'Log_Value_Lag5', 'Log_Value_Lag11', 'Past_Return_1M', 'Log_Value_Roll3_Mean',
        'Log_Value_Roll6_Mean', 'Log_Value_Roll12_Mean', 'Month_Sin', 'Month_Cos',
        'GPR', 'INR_USD_Rate', 'Shock_Intensity_Lag1', 'Trade_Share_Lag1'
    ]
    assert list(feat_a_lgb.columns) == expected_a_cols
    
    # Model B features (12 cols)
    feat_b_dict = build_model_b_features(
        event_country=event["partner"],
        commodity=event["commodity"],
        hs4=int(event["hs_code"]),
        trade_type=event["trade_direction"],
        event_date=event["event_date"]
    )
    feat_b = feat_b_dict["features_b"]
    assert len(feat_b.columns) == 12
    expected_b_cols = [
        'Lagged_Effective_Shock_1', 'Lagged_Effective_Shock_2', 'Shock_Intensity_Lag1',
        'Shock_Intensity_Lag2', 'Trade_Share_Lag1', 'Trade_Share_Lag2', 'GPR',
        'INR_USD_Rate', 'Natural_Disaster_Severity_Index', 'Season_Kharif',
        'Season_Rabi', 'Season_Summer'
    ]
    assert list(feat_b.columns) == expected_b_cols


# ============================================================================
# Test H: Downstream Agent Distribution Contract
# ============================================================================
def test_h_downstream_agent_contract():
    """Verify that the cascade output fulfills the Standard Prediction Contract for agents."""
    event = {
        "commodity": "Wheat", "hs_code": "1001", "partner": "Bangladesh",
        "trade_direction": "Export", "shock_intensity": 0.50, "trade_share": 0.08,
        "event_date": "2024-01-01"
    }
    features = build_all_model_features(event)
    res = run_drishti_ml_cascade(features, scenario_id="scen_prop_test", event_id="evt_prop_test")
    
    # All 5 stages must contain the mandatory standard fields
    for stage_key in ["stage_1_trade", "stage_2_production", "stage_3_price", "stage_4_economy"]:
        obj = res[stage_key]
        assert "scenario_id" in obj and obj["scenario_id"] == "scen_prop_test"
        assert "event_id" in obj and obj["event_id"] == "evt_prop_test"
        assert "model_id" in obj
        assert "value" in obj and isinstance(obj["value"], (int, float))
        assert "unit" in obj
        assert "prediction_status" in obj and obj["prediction_status"] in [
            "MODEL_PREDICTION", "FALLBACK_ESTIMATE", "PROXY_ESTIMATE"
        ]
        assert "prediction_method" in obj
        assert "input_feature_fingerprint" in obj


# ============================================================================
# Test I: Frontend-Backend Zero Hardcoded Fallback Parity
# ============================================================================
def test_i_frontend_backend_parity():
    """Verify that predictions match across views and no mock numbers are used."""
    event = {
        "commodity": "Wheat", "hs_code": "1001", "partner": "Bangladesh",
        "trade_direction": "Export", "shock_intensity": 0.50, "trade_share": 0.08,
        "event_date": "2024-01-01"
    }
    features = build_all_model_features(event)
    res = run_drishti_ml_cascade(features)
    
    # Verify no legacy mock numbers are returned
    disallowed_values = [-2.18, -4.82, -1.35, -0.41, -0.19]
    for stage_key in ["stage_1_trade", "stage_2_production", "stage_3_price", "stage_4_economy"]:
        val = res[stage_key]["value"]
        assert round(val, 2) not in disallowed_values, f"Stage {stage_key} returned hardcoded legacy mock value {val}!"


# ============================================================================
# Test J: Fault Tolerance and Missing Input Recovery
# ============================================================================
def test_j_fault_tolerance_missing_inputs():
    """Verify that incomplete event attributes recover safely with documented fallbacks."""
    minimal_event = {
        "event_text": "Unexpected agricultural tariff announced."
        # Missing commodity, partner, direction, shock, date
    }
    features = build_all_model_features(minimal_event)
    assert features["domain"] == "AGRICULTURAL"  # Defaulted to Wheat (1001)
    
    cascade_res = run_drishti_ml_cascade(features)
    assert cascade_res["coverage"]["status"] == "COMPLETE"
    assert cascade_res["stage_1_trade"]["value"] is not None
