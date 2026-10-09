"""
Comprehensive Controlled Model Improvement Experiments
Evaluating Models A, B, C, and D strictly on historical validation windows.
"""

import sys
import os
import json
import warnings
import numpy as np
import pandas as pd
from datetime import datetime

# Enable immediate stdout flush
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from sklearn.linear_model import Ridge, ElasticNet, HuberRegressor
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, ExtraTreesRegressor, HistGradientBoostingRegressor, HistGradientBoostingClassifier
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error, accuracy_score, balanced_accuracy_score, f1_score, precision_recall_fscore_support, confusion_matrix
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
print("STARTING CONTROLLED ML MODEL EXPERIMENTATION SUITE")
print("Timestamp:", datetime.now().isoformat())
print("=" * 80)

# ==============================================================================
# EXPERIMENT 1: MODEL A (TRADE IMPACT: Trade_Return_1M)
# ==============================================================================
print("\n" + "=" * 80)
print("SECTION 1: MODEL A EXPERIMENTS (TRADE IMPACT)")
print("=" * 80)

df_main = pd.read_csv(MAIN_CSV).sort_values(["Country", "Trade_Type", "HS4", "Year", "Month"]).reset_index(drop=True)

# 1. Construct candidate features for Model A strictly using lagged or predetermined info
# Target: Trade_Return_1M
# Existing 9 features:
existing_features_a = [
    "Lagged_Effective_Shock_1",
    "Lagged_Effective_Shock_2",
    "Shock_Intensity_Lag1",
    "Shock_Intensity_Lag2",
    "Trade_Share_Lag1",
    "Trade_Share_Lag2",
    "GPR",
    "INR_USD_Rate",
    "Natural_Disaster_Severity_Index",
]

# Engineered candidates:
# 1. Trade_Return_1M_Lag1 (1-month lagged trade return for the same Country, Trade_Type, HS4)
df_main["Trade_Return_1M_Lag1"] = df_main.groupby(["Country", "Trade_Type", "HS4"])["Trade_Return_1M"].shift(1).fillna(0.0)
df_main["Trade_Return_1M_Lag2"] = df_main.groupby(["Country", "Trade_Type", "HS4"])["Trade_Return_1M"].shift(2).fillna(0.0)

# 2. Lagged Trade Volume Log
df_main["Log_Value_USD_Lag1"] = df_main.groupby(["Country", "Trade_Type", "HS4"])["Log_Value_USD"].shift(1).fillna(0.0)

# 3. Shock trend (difference between lag1 and lag2)
df_main["Shock_Intensity_Diff"] = df_main["Shock_Intensity_Lag1"] - df_main["Shock_Intensity_Lag2"]
df_main["Trade_Share_Diff"] = df_main["Trade_Share_Lag1"] - df_main["Trade_Share_Lag2"]

# 4. Lagged Effective shock diff
df_main["Effective_Shock_Diff"] = df_main["Lagged_Effective_Shock_1"] - df_main["Lagged_Effective_Shock_2"]

# 5. Month seasonality
df_main["Month_Sin"] = np.sin(2 * np.pi * df_main["Month"] / 12)
df_main["Month_Cos"] = np.cos(2 * np.pi * df_main["Month"] / 12)

# Fill nulls in existing features
for col in existing_features_a + ["Trade_Return_1M"]:
    df_main[col] = df_main[col].fillna(0.0)

# Split for Model A
# Train <= 2022, Val = 2023, Test >= 2024
train_a = df_main[df_main["Year"] <= 2022].copy()
val_a = df_main[df_main["Year"] == 2023].copy()
test_a = df_main[df_main["Year"] >= 2024].copy()

y_train_a = train_a["Trade_Return_1M"]
y_val_a = val_a["Trade_Return_1M"]
y_test_a = test_a["Trade_Return_1M"]

# Baseline on Val and Test
bl_val_a = mean_absolute_error(y_val_a, val_a["Trade_Return_1M_Lag1"])
bl_val_a_zero = mean_absolute_error(y_val_a, np.zeros(len(y_val_a)))
bl_test_a = mean_absolute_error(y_test_a, test_a["Trade_Return_1M_Lag1"])
print(f"Model A Baselines:")
print(f"  Validation (2023): Persistence MAE = {bl_val_a:.4f} | Zero MAE = {bl_val_a_zero:.4f}")
print(f"  Test (>=2024):    Persistence MAE = {bl_test_a:.4f}")

# Define feature sets for ablation
feat_sets_a = {
    "FS1_Reference": existing_features_a,
    "FS2_With_Return_Lags": existing_features_a + ["Trade_Return_1M_Lag1", "Trade_Return_1M_Lag2"],
    "FS3_With_Shock_Dynamics": existing_features_a + ["Shock_Intensity_Diff", "Trade_Share_Diff", "Effective_Shock_Diff"],
    "FS4_With_Seasonality": existing_features_a + ["Month_Sin", "Month_Cos"],
    "FS5_Full_Defensible": existing_features_a + ["Trade_Return_1M_Lag1", "Trade_Return_1M_Lag2", "Shock_Intensity_Diff", "Trade_Share_Diff", "Effective_Shock_Diff", "Month_Sin", "Month_Cos"],
}

print("\n--- Model A Feature Ablation on Validation (2023) using Reference Random Forest ---")
model_a_ablation_results = {}
for fs_name, f_cols in feat_sets_a.items():
    rf = RandomForestRegressor(
        n_estimators=100, max_depth=12, min_samples_split=10, min_samples_leaf=5,
        max_features="sqrt", random_state=RANDOM_STATE, n_jobs=-1
    )
    rf.fit(train_a[f_cols], y_train_a)
    val_pred = rf.predict(val_a[f_cols])
    v_mae = mean_absolute_error(y_val_a, val_pred)
    v_rmse = np.sqrt(mean_squared_error(y_val_a, val_pred))
    v_r2 = r2_score(y_val_a, val_pred)
    print(f"  {fs_name:<25} ({len(f_cols)} feats) -> Val MAE: {v_mae:.4f} | RMSE: {v_rmse:.4f} | R2: {v_r2:.4f}")
    model_a_ablation_results[fs_name] = {"val_mae": v_mae, "val_rmse": v_rmse, "val_r2": v_r2}

# Compare model families on selected feature set
print("\n--- Model A Algorithm Comparison on Validation (2023) ---")
best_fs_a_name = min(model_a_ablation_results.keys(), key=lambda k: model_a_ablation_results[k]["val_mae"])
best_feats_a = feat_sets_a[best_fs_a_name]
print(f"Evaluating candidate algorithms on {best_fs_a_name} ({len(best_feats_a)} features):")

model_a_candidates = {
    "Ridge_alpha1": Ridge(alpha=1.0, random_state=RANDOM_STATE),
    "ElasticNet_alpha01": ElasticNet(alpha=0.1, l1_ratio=0.5, random_state=RANDOM_STATE),
    "RandomForest_Ref": RandomForestRegressor(n_estimators=300, max_depth=15, min_samples_split=10, min_samples_leaf=5, max_features="sqrt", random_state=RANDOM_STATE, n_jobs=-1),
    "RandomForest_Regularized": RandomForestRegressor(n_estimators=300, max_depth=12, min_samples_split=20, min_samples_leaf=10, max_features="sqrt", random_state=RANDOM_STATE, n_jobs=-1),
    "ExtraTrees_Regularized": ExtraTreesRegressor(n_estimators=200, max_depth=12, min_samples_leaf=10, max_features="sqrt", random_state=RANDOM_STATE, n_jobs=-1),
    "LightGBM_Tuned": lgb.LGBMRegressor(n_estimators=250, max_depth=6, learning_rate=0.03, num_leaves=31, subsample=0.8, colsample_bytree=0.8, reg_alpha=0.1, reg_lambda=1.0, random_state=RANDOM_STATE, n_jobs=-1, verbose=-1),
    "XGBoost_Tuned": xgb.XGBRegressor(n_estimators=250, max_depth=5, learning_rate=0.03, subsample=0.8, colsample_bytree=0.8, reg_alpha=0.5, reg_lambda=2.0, random_state=RANDOM_STATE, n_jobs=-1, verbosity=0),
    "HistGradientBoosting": HistGradientBoostingRegressor(max_iter=200, max_depth=6, learning_rate=0.03, l2_regularization=1.0, random_state=RANDOM_STATE),
}

model_a_eval = {}
for m_name, model in model_a_candidates.items():
    model.fit(train_a[best_feats_a], y_train_a)
    tr_pred = model.predict(train_a[best_feats_a])
    val_pred = model.predict(val_a[best_feats_a])
    tr_mae = mean_absolute_error(y_train_a, tr_pred)
    v_mae = mean_absolute_error(y_val_a, val_pred)
    v_rmse = np.sqrt(mean_squared_error(y_val_a, val_pred))
    v_r2 = r2_score(y_val_a, val_pred)
    print(f"  {m_name:<25} -> Val MAE: {v_mae:.4f} | R2: {v_r2:.4f} | Train MAE: {tr_mae:.4f} (Gap: {v_mae - tr_mae:+.4f})")
    model_a_eval[m_name] = {
        "val_mae": v_mae, "val_rmse": v_rmse, "val_r2": v_r2, "train_mae": tr_mae,
        "model_obj": model
    }

best_model_a_name = min(model_a_eval.keys(), key=lambda k: model_a_eval[k]["val_mae"])
print(f"Selected Candidate for Model A: {best_model_a_name} (Val MAE: {model_a_eval[best_model_a_name]['val_mae']:.4f})")

# Also evaluate across multi-period walk forward for Model A
print("\n--- Model A Multi-Period Temporal Walk-Forward Validation (2020..2023) ---")
for eval_yr in [2020, 2021, 2022, 2023]:
    tr = df_main[df_main["Year"] < eval_yr]
    vl = df_main[df_main["Year"] == eval_yr]
    rf_ex = RandomForestRegressor(n_estimators=100, max_depth=15, min_samples_split=10, min_samples_leaf=5, max_features="sqrt", random_state=RANDOM_STATE, n_jobs=-1)
    rf_ex.fit(tr[existing_features_a], tr["Trade_Return_1M"])
    pred_ex = rf_ex.predict(vl[existing_features_a])
    mae_ex = mean_absolute_error(vl["Trade_Return_1M"], pred_ex)

    cand = model_a_candidates[best_model_a_name]
    cand.fit(tr[best_feats_a], tr["Trade_Return_1M"])
    pred_cand = cand.predict(vl[best_feats_a])
    mae_cand = mean_absolute_error(vl["Trade_Return_1M"], pred_cand)

    bl_mae = mean_absolute_error(vl["Trade_Return_1M"], vl["Trade_Return_1M_Lag1"])
    print(f"  Year {eval_yr}: Baseline={bl_mae:.4f} | Existing={mae_ex:.4f} | Candidate={mae_cand:.4f} | Diff={mae_cand - mae_ex:+.4f}")

# ==============================================================================
# EXPERIMENT 2: MODEL B (AGRICULTURAL IMPACT: Production_YoY, Yield_YoY, Production_Risk)
# ==============================================================================
print("\n" + "=" * 80)
print("SECTION 2: MODEL B EXPERIMENTS (AGRICULTURAL IMPACT)")
print("=" * 80)

from scripts.train_model_b_agriculture import build_mapping, aggregate_crop_production, expand_to_monthly, merge_with_main, compute_production_risk, FEATURES_B, TARGET_CLIP_LIMIT

df_crop = pd.read_csv(CROP_CSV)
mapping_df = build_mapping()
national_df = aggregate_crop_production(df_crop, mapping_df)

# Construct strictly lagged agricultural features from previous crop cycle
# Sort national by (Crop, Season, Crop_Year)
national_df = national_df.sort_values(["Crop", "Season", "Crop_Year"]).reset_index(drop=True)
grp = national_df.groupby(["Crop", "Season"])

# Lagged national agricultural indicators (t-1 cycle)
national_df["Lagged_Production_YoY_National"] = grp["Production_YoY_National"].shift(1)
national_df["Lagged_Yield_YoY_National"] = grp["Yield_YoY_National"].shift(1)
national_df["Lagged_Production_Tonnes"] = grp["Production_Tonnes_National"].shift(1)
national_df["Lagged_Yield_National"] = grp["Yield_National"].shift(1)
national_df["Lagged_Area_Ha_National"] = grp["Area_Ha_National"].shift(1)
national_df["Lagged_Area_YoY_National"] = grp["Area_Ha_National"].pct_change().shift(1) * 100

monthly_crop = expand_to_monthly(national_df)
# Add lagged crop features into monthly_crop
lag_cols = ["Lagged_Production_YoY_National", "Lagged_Yield_YoY_National", "Lagged_Production_Tonnes", "Lagged_Yield_National", "Lagged_Area_Ha_National", "Lagged_Area_YoY_National"]
# Merge with main
merged_b = merge_with_main(df_main, monthly_crop, mapping_df)
merged_b = compute_production_risk(merged_b)

# Season features
merged_b["Season_Kharif"] = merged_b["Month"].isin([6, 7, 8, 9, 10]).astype(int)
merged_b["Season_Rabi"] = merged_b["Month"].isin([11, 12, 1, 2, 3]).astype(int)
merged_b["Season_Summer"] = merged_b["Month"].isin([3, 4, 5]).astype(int)

season_features = ["Season_Kharif", "Season_Rabi", "Season_Summer"]
existing_features_b = FEATURES_B + season_features

prod_df = merged_b[merged_b["Has_Production_Data"]].copy()

# Fill nulls
for col in existing_features_b:
    prod_df[col] = prod_df[col].fillna(0.0)

# Splits for Model B: Train <= 2021, Val = 2022, Test >= 2023
train_b = prod_df[prod_df["Year"] <= 2021].copy()
val_b = prod_df[prod_df["Year"] == 2022].copy()
test_b = prod_df[prod_df["Year"] >= 2023].copy()

# ------------------------------------------------------------------------------
# 2A: Production_YoY_National Experiments
# ------------------------------------------------------------------------------
print("\n--- 2A: Production_YoY_National Experiments ---")
target_p = "Production_YoY_National"
train_t1 = train_b.dropna(subset=[target_p]).copy()
val_t1 = val_b.dropna(subset=[target_p]).copy()
test_t1 = test_b.dropna(subset=[target_p]).copy()

y_train_p = train_t1[target_p].clip(-500, 500)
y_val_p = val_t1[target_p].clip(-500, 500)
y_test_p = test_t1[target_p].clip(-500, 500)

bl_val_p = mean_absolute_error(y_val_p, np.zeros(len(y_val_p)))
bl_test_p = mean_absolute_error(y_test_p, np.zeros(len(y_test_p)))
print(f"Production_YoY Zero-Growth Baseline: Val MAE = {bl_val_p:.4f} | Test MAE = {bl_test_p:.4f}")

# Test reference model: XGBoost_L1 (existing selected model)
xgb_ref_p = xgb.XGBRegressor(
    objective="reg:absoluteerror", n_estimators=200, max_depth=5, learning_rate=0.03,
    reg_alpha=1.0, reg_lambda=2.0, random_state=RANDOM_STATE, n_jobs=-1, verbosity=0
)
xgb_ref_p.fit(train_t1[existing_features_b], y_train_p)
ref_val_p_pred = xgb_ref_p.predict(val_t1[existing_features_b])
ref_val_p_mae = mean_absolute_error(y_val_p, ref_val_p_pred)
ref_test_p_pred = xgb_ref_p.predict(test_t1[existing_features_b])
ref_test_p_mae = mean_absolute_error(y_test_p, ref_test_p_pred)
print(f"Existing Model (XGBoost_L1): Val MAE = {ref_val_p_mae:.4f} (Baseline: {bl_val_p:.4f}) | Test MAE = {ref_test_p_mae:.4f} (Baseline: {bl_test_p:.4f})")

# Test candidate interventions for Production_YoY:
# 1. Linear models with L1/L2 shrinkage (Ridge / Lasso / Huber)
# 2. Strong regularized shrinkage tree models
# 3. Sample-weighted tree models (to downweight pseudo-replication)
# 4. Target transformation (shrinkage towards 0 prior)

candidates_p = {
    "Ridge_alpha10": Ridge(alpha=10.0, random_state=RANDOM_STATE),
    "ElasticNet_alpha1": ElasticNet(alpha=1.0, l1_ratio=0.5, random_state=RANDOM_STATE),
    "LightGBM_L1_conservative": lgb.LGBMRegressor(
        objective="regression_l1", n_estimators=100, max_depth=3, learning_rate=0.01,
        min_child_samples=50, reg_alpha=5.0, reg_lambda=5.0, random_state=RANDOM_STATE, n_jobs=-1, verbose=-1
    ),
    "XGBoost_L1_high_reg": xgb.XGBRegressor(
        objective="reg:absoluteerror", n_estimators=100, max_depth=3, learning_rate=0.01,
        reg_alpha=5.0, reg_lambda=10.0, subsample=0.7, random_state=RANDOM_STATE, n_jobs=-1, verbosity=0
    ),
    "HistGradient_L1": HistGradientBoostingRegressor(
        loss="absolute_error", max_iter=100, max_depth=3, learning_rate=0.01,
        l2_regularization=5.0, min_samples_leaf=50, random_state=RANDOM_STATE
    ),
}

results_p = {}
for name, cand in candidates_p.items():
    cand.fit(train_t1[existing_features_b], y_train_p)
    p_val = cand.predict(val_t1[existing_features_b])
    c_val_mae = mean_absolute_error(y_val_p, p_val)
    beats_bl = c_val_mae < bl_val_p
    beats_ref = c_val_mae < ref_val_p_mae
    print(f"  {name:<25} -> Val MAE: {c_val_mae:.4f} | Beats Baseline: {beats_bl} | Beats Ref: {beats_ref}")
    results_p[name] = {"val_mae": c_val_mae, "beats_bl": beats_bl, "beats_ref": beats_ref, "model": cand}

# ------------------------------------------------------------------------------
# 2B: Yield_YoY_National Experiments
# ------------------------------------------------------------------------------
print("\n--- 2B: Yield_YoY_National Experiments ---")
target_y = "Yield_YoY_National"
train_t2 = train_b.dropna(subset=[target_y]).copy()
val_t2 = val_b.dropna(subset=[target_y]).copy()
test_t2 = test_b.dropna(subset=[target_y]).copy()

y_train_y = train_t2[target_y].clip(-500, 500)
y_val_y = val_t2[target_y].clip(-500, 500)
y_test_y = test_t2[target_y].clip(-500, 500)

bl_val_y = mean_absolute_error(y_val_y, np.zeros(len(y_val_y)))
bl_test_y = mean_absolute_error(y_test_y, np.zeros(len(y_test_y)))
print(f"Yield_YoY Zero-Growth Baseline: Val MAE = {bl_val_y:.4f} | Test MAE = {bl_test_y:.4f}")

xgb_ref_y = xgb.XGBRegressor(
    objective="reg:absoluteerror", n_estimators=200, max_depth=4, learning_rate=0.03,
    reg_alpha=2.0, reg_lambda=2.0, random_state=RANDOM_STATE, n_jobs=-1, verbosity=0
)
xgb_ref_y.fit(train_t2[existing_features_b], y_train_y)
ref_val_y_pred = xgb_ref_y.predict(val_t2[existing_features_b])
ref_val_y_mae = mean_absolute_error(y_val_y, ref_val_y_pred)
ref_test_y_pred = xgb_ref_y.predict(test_t2[existing_features_b])
ref_test_y_mae = mean_absolute_error(y_test_y, ref_test_y_pred)
print(f"Existing Model (XGBoost_L1): Val MAE = {ref_val_y_mae:.4f} (Baseline: {bl_val_y:.4f}) | Test MAE = {ref_test_y_mae:.4f} (Baseline: {bl_test_y:.4f})")

candidates_y = {
    "Ridge_alpha10": Ridge(alpha=10.0, random_state=RANDOM_STATE),
    "ElasticNet_alpha1": ElasticNet(alpha=1.0, l1_ratio=0.5, random_state=RANDOM_STATE),
    "LightGBM_L1_conservative": lgb.LGBMRegressor(
        objective="regression_l1", n_estimators=100, max_depth=3, learning_rate=0.01,
        min_child_samples=50, reg_alpha=5.0, reg_lambda=5.0, random_state=RANDOM_STATE, n_jobs=-1, verbose=-1
    ),
    "XGBoost_L1_high_reg": xgb.XGBRegressor(
        objective="reg:absoluteerror", n_estimators=100, max_depth=3, learning_rate=0.01,
        reg_alpha=5.0, reg_lambda=10.0, subsample=0.7, random_state=RANDOM_STATE, n_jobs=-1, verbosity=0
    ),
    "HistGradient_L1": HistGradientBoostingRegressor(
        loss="absolute_error", max_iter=100, max_depth=3, learning_rate=0.01,
        l2_regularization=5.0, min_samples_leaf=50, random_state=RANDOM_STATE
    ),
}

results_y = {}
for name, cand in candidates_y.items():
    cand.fit(train_t2[existing_features_b], y_train_y)
    p_val = cand.predict(val_t2[existing_features_b])
    c_val_mae = mean_absolute_error(y_val_y, p_val)
    beats_bl = c_val_mae < bl_val_y
    beats_ref = c_val_mae < ref_val_y_mae
    print(f"  {name:<25} -> Val MAE: {c_val_mae:.4f} | Beats Baseline: {beats_bl} | Beats Ref: {beats_ref}")
    results_y[name] = {"val_mae": c_val_mae, "beats_bl": beats_bl, "beats_ref": beats_ref, "model": cand}

# ------------------------------------------------------------------------------
# 2C: Production_Risk Classification Experiments
# ------------------------------------------------------------------------------
print("\n--- 2C: Production_Risk Classification Experiments ---")
target_r = "Production_Risk"
risk_map = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}

train_t3 = train_b.dropna(subset=[target_r]).copy()
val_t3 = val_b.dropna(subset=[target_r]).copy()
test_t3 = test_b.dropna(subset=[target_r]).copy()

y_train_r = train_t3[target_r].map(risk_map).astype(int)
y_val_r = val_t3[target_r].map(risk_map).astype(int)
y_test_r = test_t3[target_r].map(risk_map).astype(int)

# ZeroR baseline
most_freq = y_train_r.mode()[0]
bl_acc_val_r = accuracy_score(y_val_r, np.full(len(y_val_r), most_freq))
print(f"Production_Risk Baseline (Mode={most_freq}): Val Acc = {bl_acc_val_r:.4f}")

# Existing reference model: LightGBM_tuned
lgb_ref_r = lgb.LGBMClassifier(
    n_estimators=300, max_depth=6, learning_rate=0.03, num_leaves=31,
    subsample=0.8, colsample_bytree=0.8, random_state=RANDOM_STATE, n_jobs=-1, verbose=-1
)
lgb_ref_r.fit(train_t3[existing_features_b], y_train_r)
ref_pred_val_r = lgb_ref_r.predict(val_t3[existing_features_b])
ref_val_acc_r = accuracy_score(y_val_r, ref_pred_val_r)
ref_val_bal_acc_r = balanced_accuracy_score(y_val_r, ref_pred_val_r)
ref_val_macro_f1_r = f1_score(y_val_r, ref_pred_val_r, average="macro", zero_division=0)
ref_val_weighted_f1_r = f1_score(y_val_r, ref_pred_val_r, average="weighted", zero_division=0)

print(f"Existing Reference (LightGBM_tuned):")
print(f"  Val Acc: {ref_val_acc_r:.4f} | Balanced Acc: {ref_val_bal_acc_r:.4f} | Macro F1: {ref_val_macro_f1_r:.4f} | Weighted F1: {ref_val_weighted_f1_r:.4f}")

# Candidate classifiers:
# 1. Balanced class weights
# 2. ExtraTrees / Regularized Random Forest
# 3. Tuned LightGBM with balanced weights and depth 5
# 4. HistGradientBoosting with class weights

candidates_r = {
    "LightGBM_Balanced": lgb.LGBMClassifier(
        n_estimators=250, max_depth=5, learning_rate=0.03, class_weight="balanced",
        subsample=0.8, colsample_bytree=0.8, random_state=RANDOM_STATE, n_jobs=-1, verbose=-1
    ),
    "RandomForest_Balanced": RandomForestClassifier(
        n_estimators=300, max_depth=10, min_samples_leaf=5, class_weight="balanced",
        random_state=RANDOM_STATE, n_jobs=-1
    ),
    "XGBoost_Regularized": xgb.XGBClassifier(
        n_estimators=200, max_depth=4, learning_rate=0.03, reg_alpha=1.0, reg_lambda=2.0,
        subsample=0.8, random_state=RANDOM_STATE, n_jobs=-1, verbosity=0
    ),
    "HistGradient_ClassWeighted": HistGradientBoostingClassifier(
        max_iter=200, max_depth=5, learning_rate=0.03, class_weight="balanced",
        l2_regularization=2.0, random_state=RANDOM_STATE
    ),
}

results_r = {}
for name, cand in candidates_r.items():
    cand.fit(train_t3[existing_features_b], y_train_r)
    p_val = cand.predict(val_t3[existing_features_b])
    c_acc = accuracy_score(y_val_r, p_val)
    c_bal = balanced_accuracy_score(y_val_r, p_val)
    c_mf1 = f1_score(y_val_r, p_val, average="macro", zero_division=0)
    c_wf1 = f1_score(y_val_r, p_val, average="weighted", zero_division=0)
    print(f"  {name:<25} -> Acc: {c_acc:.4f} | BalAcc: {c_bal:.4f} | MacroF1: {c_mf1:.4f} | WeightedF1: {c_wf1:.4f}")
    results_r[name] = {"acc": c_acc, "bal_acc": c_bal, "macro_f1": c_mf1, "weighted_f1": c_wf1, "model": cand}

# ==============================================================================
# EXPERIMENT 3: MODEL C (PRICE IMPACT: Price_Return_1M)
# ==============================================================================
print("\n" + "=" * 80)
print("SECTION 3: MODEL C EXPERIMENTS (DOMESTIC PRICE IMPACT)")
print("=" * 80)

from scripts.train_model_c_price import FEATURES_C, PRIMARY_TARGET as TARGET_C, compute_naive_baseline

# Align upstream OOF predictions
pred_a_oof = pd.read_csv(os.path.join(RESULTS_DIR, "model_a_predictions_oof.csv"))
pred_b_oof = pd.read_csv(os.path.join(RESULTS_DIR, "model_b_predictions_oof.csv"))

key_cols = ["Country", "Trade_Type", "HS4", "Year", "Month"]
df_c = df_main.sort_values(key_cols).reset_index(drop=True)
pred_a_sorted = pred_a_oof.sort_values(key_cols).reset_index(drop=True)
pred_b_sorted = pred_b_oof.sort_values(key_cols).reset_index(drop=True)

df_c["Trade_Return_1M_Pred"] = pred_a_sorted["Trade_Return_1M_Pred_OOF"].fillna(0.0)
df_c["Production_Growth_Pred_OOF"] = pred_b_sorted["Production_Growth_Pred_OOF"]
df_c["Production_Growth_Pred_Lag1"] = df_c.groupby(["Country", "Trade_Type", "HS4"])["Production_Growth_Pred_OOF"].shift(1).fillna(0.0)

for col in FEATURES_C:
    df_c[col] = df_c[col].fillna(0.0)

train_c = df_c[df_c["Year"] <= 2022].copy()
val_c = df_c[df_c["Year"] == 2023].copy()
test_c = df_c[df_c["Year"] >= 2024].copy()

y_train_c = train_c[TARGET_C]
y_val_c = val_c[TARGET_C]
y_test_c = test_c[TARGET_C]

val_c["naive_c"] = compute_naive_baseline(df_c, TARGET_C)[df_c["Year"] == 2023]
bl_val_c = mean_absolute_error(y_val_c, val_c["naive_c"])
print(f"Model C Baseline Val MAE: {bl_val_c:.4f}")

# Reference model: RF_regularized
rf_ref_c = RandomForestRegressor(
    n_estimators=300, max_depth=12, min_samples_split=20, min_samples_leaf=10,
    max_features="sqrt", random_state=RANDOM_STATE, n_jobs=-1
)
rf_ref_c.fit(train_c[FEATURES_C], y_train_c)
ref_val_c_pred = rf_ref_c.predict(val_c[FEATURES_C])
ref_val_c_mae = mean_absolute_error(y_val_c, ref_val_c_pred)
ref_val_c_r2 = r2_score(y_val_c, ref_val_c_pred)
print(f"Reference Model C (RF_regularized): Val MAE = {ref_val_c_mae:.4f} | R2 = {ref_val_c_r2:.4f}")

candidates_c = {
    "Ridge_alpha1": Ridge(alpha=1.0, random_state=RANDOM_STATE),
    "RF_tuned_deep": RandomForestRegressor(n_estimators=400, max_depth=14, min_samples_split=15, min_samples_leaf=8, max_features="sqrt", random_state=RANDOM_STATE, n_jobs=-1),
    "LightGBM_tuned": lgb.LGBMRegressor(n_estimators=250, max_depth=6, learning_rate=0.03, num_leaves=31, subsample=0.8, colsample_bytree=0.8, reg_alpha=0.1, reg_lambda=1.0, random_state=RANDOM_STATE, n_jobs=-1, verbose=-1),
    "XGBoost_regularized": xgb.XGBRegressor(n_estimators=250, max_depth=5, learning_rate=0.03, subsample=0.8, reg_alpha=0.1, reg_lambda=1.0, random_state=RANDOM_STATE, n_jobs=-1, verbosity=0),
    "ExtraTrees_regularized": ExtraTreesRegressor(n_estimators=250, max_depth=12, min_samples_leaf=10, max_features="sqrt", random_state=RANDOM_STATE, n_jobs=-1),
}

results_c = {}
for name, cand in candidates_c.items():
    cand.fit(train_c[FEATURES_C], y_train_c)
    p_val = cand.predict(val_c[FEATURES_C])
    c_val_mae = mean_absolute_error(y_val_c, p_val)
    c_val_r2 = r2_score(y_val_c, p_val)
    beats_ref = c_val_mae < ref_val_c_mae
    print(f"  {name:<25} -> Val MAE: {c_val_mae:.4f} | R2: {c_val_r2:.4f} | Beats Ref: {beats_ref}")
    results_c[name] = {"val_mae": c_val_mae, "val_r2": c_val_r2, "beats_ref": beats_ref, "model": cand}

# ==============================================================================
# EXPERIMENT 4: MODEL D (ECONOMIC IMPACT: Agri_GVA_Growth & Inflation_Change)
# ==============================================================================
print("\n" + "=" * 80)
print("SECTION 4: MODEL D EXPERIMENTS (ECONOMIC IMPACT)")
print("=" * 80)

from scripts.train_model_d_economy import SAFE_FEATURES_D, TARGET_GVA, TARGET_INFLATION

pred_c_oof = pd.read_csv(os.path.join(RESULTS_DIR, "model_c_predictions_oof.csv"))
pred_c_sorted = pred_c_oof.sort_values(key_cols).reset_index(drop=True)
df_d = df_main.sort_values(key_cols).reset_index(drop=True)
df_d["Price_Return_1M_Pred_OOF"] = pred_c_sorted["Price_Return_1M_Pred_OOF"]
df_d["Price_Return_1M_Pred_Lag1"] = df_d.groupby(["Country", "Trade_Type", "HS4"])["Price_Return_1M_Pred_OOF"].shift(1).fillna(0.0)

for col in SAFE_FEATURES_D:
    df_d[col] = df_d[col].fillna(0.0)

# D-1 Agri GVA (annual)
annual_df_d = df_d.groupby("Year")[SAFE_FEATURES_D].mean()
annual_df_d[TARGET_GVA] = df_d.groupby("Year")[TARGET_GVA].first()
annual_df_d["Previous_Year_GVA_Baseline"] = annual_df_d[TARGET_GVA].shift(1)
annual_df_d = annual_df_d.dropna(subset=SAFE_FEATURES_D + [TARGET_GVA, "Previous_Year_GVA_Baseline"])

tr_gva = annual_df_d[annual_df_d.index <= 2022]
val_gva = annual_df_d[annual_df_d.index == 2023]
bl_val_gva = mean_absolute_error(val_gva[TARGET_GVA], val_gva["Previous_Year_GVA_Baseline"])

ref_xgb_gva = xgb.XGBRegressor(n_estimators=100, max_depth=3, learning_rate=0.05, reg_alpha=0.5, random_state=RANDOM_STATE, n_jobs=-1, verbosity=0)
ref_xgb_gva.fit(tr_gva[SAFE_FEATURES_D], tr_gva[TARGET_GVA])
ref_val_gva_mae = mean_absolute_error(val_gva[TARGET_GVA], ref_xgb_gva.predict(val_gva[SAFE_FEATURES_D]))
print(f"Model D-1 GVA: Baseline Val MAE = {bl_val_gva:.4f} | Existing XGB Val MAE = {ref_val_gva_mae:.4f}")

candidates_d1 = {
    "Ridge_alpha1": Ridge(alpha=1.0, random_state=RANDOM_STATE),
    "Huber_reg": HuberRegressor(max_iter=300),
    "RandomForest_reg": RandomForestRegressor(n_estimators=200, max_depth=4, random_state=RANDOM_STATE, n_jobs=-1),
    "ElasticNet": ElasticNet(alpha=0.1, l1_ratio=0.5, random_state=RANDOM_STATE),
}

for name, cand in candidates_d1.items():
    cand.fit(tr_gva[SAFE_FEATURES_D], tr_gva[TARGET_GVA])
    p_val = cand.predict(val_gva[SAFE_FEATURES_D])
    c_val_mae = mean_absolute_error(val_gva[TARGET_GVA], p_val)
    print(f"  {name:<25} -> Val MAE: {c_val_mae:.4f} | Beats Ref: {c_val_mae < ref_val_gva_mae}")

# D-2 Inflation (monthly)
tr_infl = df_d[df_d["Year"] <= 2022]
val_infl = df_d[df_d["Year"] == 2023]
bl_val_infl = mean_absolute_error(val_infl[TARGET_INFLATION], np.zeros(len(val_infl)))

ref_xgb_infl = xgb.XGBRegressor(n_estimators=200, max_depth=5, learning_rate=0.03, reg_alpha=0.5, reg_lambda=1.0, subsample=0.8, random_state=RANDOM_STATE, n_jobs=-1, verbosity=0)
ref_xgb_infl.fit(tr_infl[SAFE_FEATURES_D], tr_infl[TARGET_INFLATION])
ref_val_infl_mae = mean_absolute_error(val_infl[TARGET_INFLATION], ref_xgb_infl.predict(val_infl[SAFE_FEATURES_D]))
print(f"\nModel D-2 Inflation: Baseline Val MAE = {bl_val_infl:.4f} | Existing XGB Val MAE = {ref_val_infl_mae:.4f}")

candidates_d2 = {
    "Zero_Change_Baseline": None,
    "Ridge_alpha10": Ridge(alpha=10.0, random_state=RANDOM_STATE),
    "ElasticNet_shrink": ElasticNet(alpha=0.5, l1_ratio=0.5, random_state=RANDOM_STATE),
    "Ridge_alpha100": Ridge(alpha=100.0, random_state=RANDOM_STATE),
    "LightGBM_heavily_reg": lgb.LGBMRegressor(n_estimators=100, max_depth=3, learning_rate=0.01, reg_alpha=2.0, reg_lambda=5.0, subsample=0.7, random_state=RANDOM_STATE, n_jobs=-1, verbose=-1),
}

for name, cand in candidates_d2.items():
    if cand is None:
        print(f"  {name:<25} -> Val MAE: {bl_val_infl:.4f} (Benchmark)")
        continue
    cand.fit(tr_infl[SAFE_FEATURES_D], tr_infl[TARGET_INFLATION])
    p_val = cand.predict(val_infl[SAFE_FEATURES_D])
    c_val_mae = mean_absolute_error(val_infl[TARGET_INFLATION], p_val)
    print(f"  {name:<25} -> Val MAE: {c_val_mae:.4f} | Beats Baseline: {c_val_mae < bl_val_infl} | Beats Ref: {c_val_mae < ref_val_infl_mae}")

print("\n" + "=" * 80)
print("EXPERIMENTATION SUITE COMPLETE")
print("=" * 80)
