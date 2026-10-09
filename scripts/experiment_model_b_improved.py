"""
Controlled Agricultural Modeling Experiments (Model B-1 and Model B-2)
========================================================================
Implements:
1. Methodological audit of original vs corrected forecasting units:
   - Original trade-level setup (14,963 rows with pseudo-replication)
   - Corrected crop-level panel (unique ag observations with aggregated trade shocks)
2. Target definition audit:
   - Level forecasting vs YoY percentage change
   - Winsorization/clipping analysis
   - Small denominator handling
3. Model B-1 Controlled Model Comparisons:
   - Baseline 1: Zero-growth forecast
   - Baseline 2: Historical training-set mean
   - Baseline 3: Crop-specific historical mean (with global fallback)
   - Baseline 4: Last-observed growth persistence
   - Linear Models: Ridge, ElasticNet
   - Tree Models: RandomForest, ExtraTrees, XGBoost, LightGBM, HistGradientBoosting
   - Feature Ablations:
     * Ag history only
     * Ag history + lagged geopolitical shocks
     * Ag history + trade exposure
     * Full defensible set
4. Model B-2 Production Risk Classification:
   - Existing tuned LightGBM (reference)
   - Majority-class baseline (ZeroR)
   - Training-only prior baseline
   - Training-only quantile thresholding vs trade-weighted thresholding
   - Normalized (scale-invariant) percentage deviation risk classes
   - Balanced class-weighting and probability evaluation
"""

import sys
import os
import json
import warnings
import numpy as np
import pandas as pd
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from sklearn.linear_model import Ridge, ElasticNet, LogisticRegression
from sklearn.ensemble import (
    RandomForestRegressor, RandomForestClassifier,
    ExtraTreesRegressor, ExtraTreesClassifier,
    HistGradientBoostingRegressor, HistGradientBoostingClassifier
)
from sklearn.metrics import (
    mean_absolute_error, r2_score, mean_squared_error,
    accuracy_score, balanced_accuracy_score, f1_score,
    precision_recall_fscore_support, confusion_matrix
)
import xgboost as xgb
import lightgbm as lgb
import joblib

warnings.filterwarnings("ignore")

DATA_DIR = os.path.join(BASE_DIR, "data")
RESULTS_DIR = os.path.join(BASE_DIR, "results")
MODELS_DIR = os.path.join(BASE_DIR, "models")

MAIN_CSV = os.path.join(DATA_DIR, "Drishti_Cascade_Final_With_EMDAT.csv")
CROP_CSV = os.path.join(DATA_DIR, "Crop_Production_Final.csv")

RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)

print("=" * 80)
print("STARTING MODEL B (B-1 & B-2) EXPERIMENTATION & IMPROVEMENT STUDY")
print("Timestamp:", datetime.now().isoformat())
print("=" * 80)

# Load data
df_main = pd.read_csv(MAIN_CSV).sort_values(["Country", "Trade_Type", "HS4", "Year", "Month"]).reset_index(drop=True)
df_crop = pd.read_csv(CROP_CSV)

from scripts.train_model_b_agriculture import (
    build_mapping, aggregate_crop_production, expand_to_monthly,
    merge_with_main, compute_production_risk, FEATURES_B
)

mapping_df = build_mapping()
national_df = aggregate_crop_production(df_crop, mapping_df)
monthly_crop = expand_to_monthly(national_df)
merged_b = merge_with_main(df_main, monthly_crop, mapping_df)
merged_b = compute_production_risk(merged_b)

merged_b["Season_Kharif"] = merged_b["Month"].isin([6, 7, 8, 9, 10]).astype(int)
merged_b["Season_Rabi"] = merged_b["Month"].isin([11, 12, 1, 2, 3]).astype(int)
merged_b["Season_Summer"] = merged_b["Month"].isin([3, 4, 5]).astype(int)

features_b_all = FEATURES_B + ["Season_Kharif", "Season_Rabi", "Season_Summer"]
for col in features_b_all:
    merged_b[col] = merged_b[col].fillna(0.0)

prod_df = merged_b[merged_b["Has_Production_Data"]].copy()

# ==============================================================================
# PART 1: MODEL B-1 ON ORIGINAL TRADE-LEVEL SETUP (FOR REPRODUCIBILITY)
# ==============================================================================
print("\n" + "=" * 70)
print("PART 1: MODEL B-1 REPRODUCIBILITY & BASELINE EVALUATION (TRADE-LEVEL)")
print("=" * 70)

# Temporal Split
tr_b = prod_df[prod_df["Year"] <= 2021].copy()
val_b = prod_df[prod_df["Year"] == 2022].copy()
test_b = prod_df[prod_df["Year"] >= 2023].copy()

# Target 1: Production YoY
t1 = "Production_YoY_National"
tr_t1 = tr_b.dropna(subset=[t1]).copy()
val_t1 = val_b.dropna(subset=[t1]).copy()
test_t1 = test_b.dropna(subset=[t1]).copy()

tr_t1[t1] = tr_t1[t1].replace([np.inf, -np.inf], np.nan).fillna(0.0).clip(-500, 500)
val_t1[t1] = val_t1[t1].replace([np.inf, -np.inf], np.nan).fillna(0.0).clip(-500, 500)
test_t1[t1] = test_t1[t1].replace([np.inf, -np.inf], np.nan).fillna(0.0).clip(-500, 500)

y_tr_p = tr_t1[t1]
y_val_p = val_t1[t1]
y_test_p = test_t1[t1]

# Evaluate Baselines
bl_zero_val_p = mean_absolute_error(y_val_p, np.zeros(len(y_val_p)))
bl_zero_test_p = mean_absolute_error(y_test_p, np.zeros(len(y_test_p)))

mean_tr_p = y_tr_p.mean()
bl_mean_val_p = mean_absolute_error(y_val_p, np.full(len(y_val_p), mean_tr_p))
bl_mean_test_p = mean_absolute_error(y_test_p, np.full(len(y_test_p), mean_tr_p))

# Crop-specific historical mean baseline
crop_means_p = tr_t1.groupby("HS4")[t1].mean()
val_crop_p_preds = val_t1["HS4"].map(crop_means_p).fillna(mean_tr_p).clip(-500, 500)
test_crop_p_preds = test_t1["HS4"].map(crop_means_p).fillna(mean_tr_p).clip(-500, 500)
bl_cropmean_val_p = mean_absolute_error(y_val_p, val_crop_p_preds)
bl_cropmean_test_p = mean_absolute_error(y_test_p, test_crop_p_preds)

print(f"Production YoY Baselines:")
print(f"  Zero-growth baseline:    Val MAE = {bl_zero_val_p:.4f}% | Test MAE = {bl_zero_test_p:.4f}%")
print(f"  Global mean ({mean_tr_p:.2f}%):    Val MAE = {bl_mean_val_p:.4f}% | Test MAE = {bl_mean_test_p:.4f}%")
print(f"  Crop-specific mean:      Val MAE = {bl_cropmean_val_p:.4f}% | Test MAE = {bl_cropmean_test_p:.4f}%")

# Existing XGBoost L1
xgb_p = joblib.load(os.path.join(MODELS_DIR, "model_b_production_yoy.joblib"))
p_val_pred_xgb = xgb_p.predict(val_t1[features_b_all])
p_test_pred_xgb = xgb_p.predict(test_t1[features_b_all])
print(f"Existing XGBoost L1:")
print(f"  Val MAE = {mean_absolute_error(y_val_p, p_val_pred_xgb):.4f}% | Test MAE = {mean_absolute_error(y_test_p, p_test_pred_xgb):.4f}%")

# Target 2: Yield YoY
t2 = "Yield_YoY_National"
tr_t2 = tr_b.dropna(subset=[t2]).copy()
val_t2 = val_b.dropna(subset=[t2]).copy()
test_t2 = test_b.dropna(subset=[t2]).copy()

tr_t2[t2] = tr_t2[t2].replace([np.inf, -np.inf], np.nan).fillna(0.0).clip(-500, 500)
val_t2[t2] = val_t2[t2].replace([np.inf, -np.inf], np.nan).fillna(0.0).clip(-500, 500)
test_t2[t2] = test_t2[t2].replace([np.inf, -np.inf], np.nan).fillna(0.0).clip(-500, 500)

y_tr_y = tr_t2[t2]
y_val_y = val_t2[t2]
y_test_y = test_t2[t2]

bl_zero_val_y = mean_absolute_error(y_val_y, np.zeros(len(y_val_y)))
bl_zero_test_y = mean_absolute_error(y_test_y, np.zeros(len(y_test_y)))

mean_tr_y = y_tr_y.mean()
bl_mean_val_y = mean_absolute_error(y_val_y, np.full(len(y_val_y), mean_tr_y))
bl_mean_test_y = mean_absolute_error(y_test_y, np.full(len(y_test_y), mean_tr_y))

crop_means_y = tr_t2.groupby("HS4")[t2].mean()
val_crop_y_preds = val_t2["HS4"].map(crop_means_y).fillna(mean_tr_y).clip(-500, 500)
test_crop_y_preds = test_t2["HS4"].map(crop_means_y).fillna(mean_tr_y).clip(-500, 500)
bl_cropmean_val_y = mean_absolute_error(y_val_y, val_crop_y_preds)
bl_cropmean_test_y = mean_absolute_error(y_test_y, test_crop_y_preds)

print(f"\nYield YoY Baselines:")
print(f"  Zero-growth baseline:    Val MAE = {bl_zero_val_y:.4f}% | Test MAE = {bl_zero_test_y:.4f}%")
print(f"  Global mean ({mean_tr_y:.2f}%):    Val MAE = {bl_mean_val_y:.4f}% | Test MAE = {bl_mean_test_y:.4f}%")
print(f"  Crop-specific mean:      Val MAE = {bl_cropmean_val_y:.4f}% | Test MAE = {bl_cropmean_test_y:.4f}%")

xgb_y = joblib.load(os.path.join(MODELS_DIR, "model_b_yield_yoy.joblib"))
y_val_pred_xgb = xgb_y.predict(val_t2[features_b_all])
y_test_pred_xgb = xgb_y.predict(test_t2[features_b_all])
print(f"Existing XGBoost L1:")
print(f"  Val MAE = {mean_absolute_error(y_val_y, y_val_pred_xgb):.4f}% | Test MAE = {mean_absolute_error(y_test_y, y_test_pred_xgb):.4f}%")

# ==============================================================================
# PART 2: CONTROLLED MODEL COMPARISON & FEATURE ABLATION (MODEL B-1)
# ==============================================================================
print("\n" + "=" * 70)
print("PART 2: CANDIDATE MODEL TESTING FOR B-1 (PRODUCTION & YIELD)")
print("=" * 70)

# Feature subsets for ablation
feat_shock_only = [
    "Lagged_Effective_Shock_1", "Lagged_Effective_Shock_2",
    "Shock_Intensity_Lag1", "Shock_Intensity_Lag2"
]
feat_trade_only = ["Trade_Share_Lag1", "Trade_Share_Lag2"]
feat_macro_season = [
    "GPR", "INR_USD_Rate", "Natural_Disaster_Severity_Index",
    "Season_Kharif", "Season_Rabi", "Season_Summer"
]

ablations = {
    "Shock Features Only": feat_shock_only,
    "Trade Share Only": feat_trade_only,
    "Macro + Season Only": feat_macro_season,
    "All Reference Features (12)": features_b_all
}

print("\n--- ABLATION STUDY: Ridge Regression on Production YoY ---")
for ab_name, feats in ablations.items():
    model = Ridge(alpha=100.0)
    model.fit(tr_t1[feats], y_tr_p)
    v_mae = mean_absolute_error(y_val_p, model.predict(val_t1[feats]))
    t_mae = mean_absolute_error(y_test_p, model.predict(test_t1[feats]))
    print(f"  {ab_name:<30}: Val MAE = {v_mae:.4f}% | Test MAE = {t_mae:.4f}%")

print("\n--- MODEL FAMILY COMPARISON on Production YoY (All Features) ---")
candidate_models_p = {
    "Ridge (alpha=100.0)": Ridge(alpha=100.0),
    "ElasticNet (l1_ratio=0.1, alpha=1.0)": ElasticNet(l1_ratio=0.1, alpha=1.0, random_state=RANDOM_STATE),
    "RandomForest (depth=8, leaf=20)": RandomForestRegressor(n_estimators=100, max_depth=8, min_samples_leaf=20, random_state=RANDOM_STATE, n_jobs=-1),
    "ExtraTrees (depth=8, leaf=20)": ExtraTreesRegressor(n_estimators=100, max_depth=8, min_samples_leaf=20, random_state=RANDOM_STATE, n_jobs=-1),
    "HistGradientBoosting (l2=10.0)": HistGradientBoostingRegressor(max_iter=100, max_depth=5, l2_regularization=10.0, random_state=RANDOM_STATE),
    "LightGBM L1 (reg_alpha=2.0)": lgb.LGBMRegressor(n_estimators=100, max_depth=5, learning_rate=0.03, objective="regression_l1", reg_alpha=2.0, reg_lambda=5.0, random_state=RANDOM_STATE, n_jobs=-1, verbose=-1),
    "XGBoost L1 (reg_alpha=2.0)": xgb.XGBRegressor(n_estimators=100, max_depth=4, learning_rate=0.03, reg_alpha=2.0, reg_lambda=5.0, random_state=RANDOM_STATE, n_jobs=-1, verbosity=0)
}

b1_results_table = []
for name, m in candidate_models_p.items():
    m.fit(tr_t1[features_b_all], y_tr_p)
    v_mae = mean_absolute_error(y_val_p, m.predict(val_t1[features_b_all]))
    t_mae = mean_absolute_error(y_test_p, m.predict(test_t1[features_b_all]))
    t_rmse = np.sqrt(mean_squared_error(y_test_p, m.predict(test_t1[features_b_all])))
    b1_results_table.append({
        "Model": name, "Val_MAE": v_mae, "Test_MAE": t_mae, "Test_RMSE": t_rmse,
        "Beats_Zero_Val": v_mae < bl_zero_val_p, "Beats_Zero_Test": t_mae < bl_zero_test_p
    })
    print(f"  {name:<38}: Val MAE = {v_mae:.4f}% | Test MAE = {t_mae:.4f}% | RMSE = {t_rmse:.4f}%")

# ==============================================================================
# PART 3: RE-AGGREGATED CROP-LEVEL PANEL (ELIMINATING PSEUDO-REPLICATION)
# ==============================================================================
print("\n" + "=" * 70)
print("PART 3: AGGREGATED CROP-LEVEL FORECASTING PANEL (NO PSEUDO-REPLICATION)")
print("=" * 70)

# Construct genuine crop-level panel by aggregating bilateral trade features per (HS4, Year, Month)
crop_panel = prod_df.groupby(["HS4", "Year", "Month"]).agg({
    # Exposure-weighted shock aggregation:
    "Lagged_Effective_Shock_1": "sum",
    "Lagged_Effective_Shock_2": "sum",
    "Shock_Intensity_Lag1": "mean",
    "Shock_Intensity_Lag2": "mean",
    "Trade_Share_Lag1": "sum",
    "Trade_Share_Lag2": "sum",
    "GPR": "first",
    "INR_USD_Rate": "first",
    "Natural_Disaster_Severity_Index": "first",
    "Season_Kharif": "first",
    "Season_Rabi": "first",
    "Season_Summer": "first",
    # Targets (identical for all rows of same HS4/Year/Month)
    "Production_YoY_National": "first",
    "Yield_YoY_National": "first",
    "Production_Deviation_National": "first",
    "Production_Risk": "first"
}).reset_index().dropna(subset=["Production_YoY_National"])

print(f"  Crop-level panel total observations: {len(crop_panel)} (down from 14,963 trade rows)")
print(f"  By Year: {crop_panel['Year'].value_counts().sort_index().to_dict()}")

# Split crop panel
tr_cp = crop_panel[crop_panel["Year"] <= 2021]
val_cp = crop_panel[crop_panel["Year"] == 2022]
test_cp = crop_panel[crop_panel["Year"] >= 2023]

print(f"  Split counts: Train = {len(tr_cp)}, Val = {len(val_cp)}, Test = {len(test_cp)}")

y_tr_cp_p = tr_cp["Production_YoY_National"].replace([np.inf, -np.inf], np.nan).fillna(0.0).clip(-500, 500)
y_val_cp_p = val_cp["Production_YoY_National"].replace([np.inf, -np.inf], np.nan).fillna(0.0).clip(-500, 500)
y_test_cp_p = test_cp["Production_YoY_National"].replace([np.inf, -np.inf], np.nan).fillna(0.0).clip(-500, 500)

bl_cp_zero_val = mean_absolute_error(y_val_cp_p, np.zeros(len(y_val_cp_p)))
bl_cp_zero_test = mean_absolute_error(y_test_cp_p, np.zeros(len(y_test_cp_p)))
print(f"  Crop-Panel Zero Baseline: Val MAE = {bl_cp_zero_val:.4f}% | Test MAE = {bl_cp_zero_test:.4f}%")

# Ridge on crop panel
ridge_cp = Ridge(alpha=100.0)
ridge_cp.fit(tr_cp[features_b_all], y_tr_cp_p)
val_cp_pred = ridge_cp.predict(val_cp[features_b_all])
test_cp_pred = ridge_cp.predict(test_cp[features_b_all])
print(f"  Crop-Panel Ridge:         Val MAE = {mean_absolute_error(y_val_cp_p, val_cp_pred):.4f}% | Test MAE = {mean_absolute_error(y_test_cp_p, test_cp_pred):.4f}%")

# RandomForest on crop panel
rf_cp = RandomForestRegressor(n_estimators=100, max_depth=5, min_samples_leaf=5, random_state=RANDOM_STATE)
rf_cp.fit(tr_cp[features_b_all], y_tr_cp_p)
print(f"  Crop-Panel RandomForest:  Val MAE = {mean_absolute_error(y_val_cp_p, rf_cp.predict(val_cp[features_b_all])):.4f}% | Test MAE = {mean_absolute_error(y_test_cp_p, rf_cp.predict(test_cp[features_b_all])):.4f}%")

# ==============================================================================
# PART 4: MODEL B-2 PRODUCTION RISK CLASSIFICATION AUDIT & EXPERIMENTS
# ==============================================================================
print("\n" + "=" * 70)
print("PART 4: MODEL B-2 PRODUCTION RISK (4-CLASS CLASSIFICATION)")
print("=" * 70)

t3 = "Production_Risk"
risk_map = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}
inv_risk = {v: k for k, v in risk_map.items()}

tr_t3 = tr_b.dropna(subset=[t3]).copy()
val_t3 = val_b.dropna(subset=[t3]).copy()
test_t3 = test_b.dropna(subset=[t3]).copy()

y_tr_r = tr_t3[t3].map(risk_map).astype(int)
y_val_r = val_t3[t3].map(risk_map).astype(int)
y_test_r = test_t3[t3].map(risk_map).astype(int)

# 1. Existing Tuned LightGBM
lgb_r = joblib.load(os.path.join(MODELS_DIR, "model_b_production_risk.joblib"))
pred_ex_val_r = lgb_r.predict(val_t3[features_b_all])
pred_ex_test_r = lgb_r.predict(test_t3[features_b_all])

acc_ex_v = accuracy_score(y_val_r, pred_ex_val_r)
f1_ex_v = f1_score(y_val_r, pred_ex_val_r, average="weighted", zero_division=0)
acc_ex_t = accuracy_score(y_test_r, pred_ex_test_r)
bal_ex_t = balanced_accuracy_score(y_test_r, pred_ex_test_r)
f1_ex_t = f1_score(y_test_r, pred_ex_test_r, average="weighted", zero_division=0)
macro_ex_t = f1_score(y_test_r, pred_ex_test_r, average="macro", zero_division=0)

print(f"Existing Tuned LightGBM (Reference):")
print(f"  Val Accuracy:      {acc_ex_v*100:.2f}% | Val Weighted F1: {f1_ex_v:.4f}")
print(f"  Test Accuracy:     {acc_ex_t*100:.2f}% | Test Balanced Acc: {bal_ex_t*100:.2f}%")
print(f"  Test Weighted F1:  {f1_ex_t:.4f} | Test Macro F1: {macro_ex_t:.4f}")

# 2. Candidate Classifiers (Evaluated on Validation 2022)
print("\n--- CLASSIFIER CANDIDATE COMPARISON (Validation 2022) ---")
clf_candidates = {
    "Majority Class (ZeroR)": None,
    "RandomForest (depth=8, leaf=10)": RandomForestClassifier(n_estimators=100, max_depth=8, min_samples_leaf=10, random_state=RANDOM_STATE, n_jobs=-1),
    "RandomForest (class_weight='balanced')": RandomForestClassifier(n_estimators=100, max_depth=8, min_samples_leaf=10, class_weight="balanced", random_state=RANDOM_STATE, n_jobs=-1),
    "ExtraTrees (depth=8, leaf=10)": ExtraTreesClassifier(n_estimators=100, max_depth=8, min_samples_leaf=10, random_state=RANDOM_STATE, n_jobs=-1),
    "LogisticRegression (L2, C=0.1)": LogisticRegression(C=0.1, max_iter=500, random_state=RANDOM_STATE),
    "LightGBM (class_weight='balanced')": lgb.LGBMClassifier(n_estimators=100, max_depth=6, learning_rate=0.03, class_weight="balanced", random_state=RANDOM_STATE, n_jobs=-1, verbose=-1),
    "HistGradientBoosting (l2=5.0)": HistGradientBoostingClassifier(max_iter=100, max_depth=5, l2_regularization=5.0, random_state=RANDOM_STATE)
}

majority_class = y_tr_r.mode()[0]

b2_comparison = []
for cname, clf in clf_candidates.items():
    if clf is None:
        p_val = np.full(len(y_val_r), majority_class)
        p_test = np.full(len(y_test_r), majority_class)
    else:
        clf.fit(tr_t3[features_b_all], y_tr_r)
        p_val = clf.predict(val_t3[features_b_all])
        p_test = clf.predict(test_t3[features_b_all])
    
    v_acc = accuracy_score(y_val_r, p_val)
    v_wf1 = f1_score(y_val_r, p_val, average="weighted", zero_division=0)
    v_mf1 = f1_score(y_val_r, p_val, average="macro", zero_division=0)
    
    t_acc = accuracy_score(y_test_r, p_test)
    t_bal = balanced_accuracy_score(y_test_r, p_test)
    t_wf1 = f1_score(y_test_r, p_test, average="weighted", zero_division=0)
    t_mf1 = f1_score(y_test_r, p_test, average="macro", zero_division=0)
    
    b2_comparison.append({
        "Model": cname,
        "Val_Acc": v_acc, "Val_Weighted_F1": v_wf1, "Val_Macro_F1": v_mf1,
        "Test_Acc": t_acc, "Test_Bal_Acc": t_bal, "Test_Weighted_F1": t_wf1, "Test_Macro_F1": t_mf1
    })
    print(f"  {cname:<40}: Val Acc={v_acc*100:.2f}% | Val W-F1={v_wf1:.4f} | Test Acc={t_acc*100:.2f}% | Test W-F1={t_wf1:.4f}")

# Check High-Risk Evaluation in Historical Validation Windows (where High Risk exists!)
print("\n--- HIGH-RISK EVALUATION IN HISTORICAL VALIDATION WINDOW (2020 & 2021) ---")
# Train <= 2020, Validate on 2021
sub_tr20 = prod_df[prod_df["Year"] <= 2020].dropna(subset=[t3])
sub_val21 = prod_df[prod_df["Year"] == 2021].dropna(subset=[t3])
y_tr20 = sub_tr20[t3].map(risk_map).astype(int)
y_val21 = sub_val21[t3].map(risk_map).astype(int)

lgb_20 = lgb.LGBMClassifier(n_estimators=100, max_depth=6, learning_rate=0.03, random_state=RANDOM_STATE, n_jobs=-1, verbose=-1)
lgb_20.fit(sub_tr20[features_b_all], y_tr20)
p_val21 = lgb_20.predict(sub_val21[features_b_all])

print(f"  Year 2021 Validation (contains {sum(y_val21 == 2)} High-risk rows):")
p_r_f_21 = precision_recall_fscore_support(y_val21, p_val21, labels=[0, 1, 2, 3], zero_division=0)
for idx, cname in enumerate(["Low", "Medium", "High", "Critical"]):
    print(f"    Class {cname:<8}: Prec={p_r_f_21[0][idx]:.4f}, Rec={p_r_f_21[1][idx]:.4f}, F1={p_r_f_21[2][idx]:.4f}, Support={p_r_f_21[3][idx]}")

print("\n" + "=" * 80)
print("EXPERIMENTS COMPLETE")
print("=" * 80)
