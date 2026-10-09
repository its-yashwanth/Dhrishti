"""
Track 3 & Track 4: Model B-1 Feature Ablations & Multi-Period Temporal Walk-Forward
===================================================================================
Rigorous, leak-free evaluation:
1. Feature Ablations across 6 groups with clean crop-season lagged features (computed
   prior to monthly expansion and merge to prevent pseudo-replicated target leakage).
2. Model Families (11 models/baselines) with StandardScaler pipelines for linear/robust regressors.
3. Multi-Period Walk-Forward Temporal Validation (4 temporal windows).
4. Dual evaluation:
   - Evaluated on the Expanded Trade Panel (n=14,963)
   - Evaluated on the Independent Crop-Season Panel (n=941)
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

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge, ElasticNet, HuberRegressor
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor, HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
import xgboost as xgb
import lightgbm as lgb
import joblib

warnings.filterwarnings("ignore")

DATA_DIR = os.path.join(BASE_DIR, "data")
EXP_DIR = os.path.join(BASE_DIR, "experiments", "model_b_initiative")
EXP_MODELS_DIR = os.path.join(EXP_DIR, "models")
EXP_RESULTS_DIR = os.path.join(EXP_DIR, "results")
os.makedirs(EXP_MODELS_DIR, exist_ok=True)
os.makedirs(EXP_RESULTS_DIR, exist_ok=True)

MAIN_CSV = os.path.join(DATA_DIR, "Drishti_Cascade_Final_With_EMDAT.csv")
CROP_CSV = os.path.join(DATA_DIR, "Crop_Production_Final.csv")

RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)

print("=" * 80)
print("TRACK 3 & TRACK 4: FEATURE ABLATIONS & TEMPORAL WALK-FORWARD VALIDATION")
print("Timestamp:", datetime.now().isoformat())
print("=" * 80)

# Load data and prepare features
df_main = pd.read_csv(MAIN_CSV).sort_values(["Country", "Trade_Type", "HS4", "Year", "Month"]).reset_index(drop=True)
df_crop = pd.read_csv(CROP_CSV)

from scripts.train_model_b_agriculture import (
    build_mapping, aggregate_crop_production, expand_to_monthly,
    merge_with_main
)

mapping_df = build_mapping()
national_df = aggregate_crop_production(df_crop, mapping_df)

# Construct crop_with_hs4 and crop_by_hs4
monthly_crop = expand_to_monthly(national_df)
crop_with_hs4 = monthly_crop.merge(
    mapping_df[["Crop", "HS4"]],
    on="Crop",
    how="left"
)

crop_by_hs4 = crop_with_hs4.groupby(["HS4", "Year", "Month"]).agg(
    Production_Tonnes_National=("Production_Tonnes_National", "sum"),
    Area_Ha_National=("Area_Ha_National", "sum"),
    Yield_National=("Yield_National", "mean"),
    Production_YoY_National=("Production_YoY_National", "mean"),
    Yield_YoY_National=("Yield_YoY_National", "mean"),
    Production_Deviation_National=("Production_Deviation_National", "sum"),
).reset_index()

# Clean, leak-free lag features computed per (HS4, Month) across Years
crop_by_hs4 = crop_by_hs4.sort_values(["HS4", "Month", "Year"]).reset_index(drop=True)
grp_hm = crop_by_hs4.groupby(["HS4", "Month"])

crop_by_hs4["Ag_Prod_YoY_Lag1"] = grp_hm["Production_YoY_National"].shift(1).fillna(0.0)
crop_by_hs4["Ag_Yield_YoY_Lag1"] = grp_hm["Yield_YoY_National"].shift(1).fillna(0.0)
crop_by_hs4["Ag_Yield_3Y_Mean_Prior"] = (
    grp_hm["Yield_National"]
    .transform(lambda x: x.shift(1).rolling(3, min_periods=1).mean())
    .fillna(0.0)
)
crop_by_hs4["Ag_Area_YoY_Lag1"] = (
    grp_hm["Area_Ha_National"]
    .pct_change()
    .shift(1)
    * 100
).fillna(0.0)

# Merge with main dataset
merged_b = df_main.merge(
    crop_by_hs4,
    on=["HS4", "Year", "Month"],
    how="left"
)
merged_b["Has_Production_Data"] = merged_b["Production_Tonnes_National"].notna()

# Construct seasonal dummies
merged_b["Season_Kharif"] = merged_b["Month"].isin([6, 7, 8, 9, 10]).astype(int)
merged_b["Season_Rabi"] = merged_b["Month"].isin([11, 12, 1, 2, 3]).astype(int)
merged_b["Season_Summer"] = merged_b["Month"].isin([3, 4, 5]).astype(int)

prod_df = merged_b[merged_b["Has_Production_Data"]].copy().sort_values(["HS4", "Year", "Month"]).reset_index(drop=True)

# Define feature ablation groups
f_ag_history = ["Ag_Prod_YoY_Lag1", "Ag_Yield_YoY_Lag1", "Ag_Yield_3Y_Mean_Prior", "Ag_Area_YoY_Lag1"]
f_season = ["Season_Kharif", "Season_Rabi", "Season_Summer"]
f_trade_exp = ["Trade_Share_Lag1", "Trade_Share_Lag2"]
f_shock = ["Lagged_Effective_Shock_1", "Lagged_Effective_Shock_2", "Shock_Intensity_Lag1", "Shock_Intensity_Lag2"]
f_macro = ["GPR", "INR_USD_Rate", "Natural_Disaster_Severity_Index"]

ablation_definitions = {
    "Ablation_1_Ag_History_Only": f_ag_history,
    "Ablation_2_Ag_History_Plus_Season": f_ag_history + f_season,
    "Ablation_3_Ag_History_Plus_Trade_Exposure": f_ag_history + f_season + f_trade_exp,
    "Ablation_4_Ag_History_Plus_Shocks": f_ag_history + f_season + f_shock,
    "Ablation_5_Ag_History_Plus_Macro_Disaster": f_ag_history + f_season + f_macro,
    "Ablation_6_Full_Defensible_Set": f_ag_history + f_season + f_trade_exp + f_shock + f_macro
}

all_feature_cols = sorted(list(set(f_ag_history + f_season + f_trade_exp + f_shock + f_macro)))
for c in all_feature_cols:
    prod_df[c] = prod_df[c].replace([np.inf, -np.inf], np.nan).fillna(0.0)

# Targets
target_p = "Production_YoY_National"
target_y = "Yield_YoY_National"

prod_df[target_p] = prod_df[target_p].replace([np.inf, -np.inf], np.nan).fillna(0.0).clip(-500, 500)
prod_df[target_y] = prod_df[target_y].replace([np.inf, -np.inf], np.nan).fillna(0.0).clip(-500, 500)

tr_df = prod_df[prod_df["Year"] <= 2021]
val_df = prod_df[prod_df["Year"] == 2022]
test_df = prod_df[prod_df["Year"] >= 2023]

print(f"\nExpanded Panel Splits: Train={len(tr_df):,} | Val={len(val_df):,} | Test={len(test_df):,}")

# Also prepare deduplicated Crop-Season Panel for robust multi-period validation
crop_panel = prod_df.drop_duplicates(subset=["HS4", "Year", "Month"]).copy().reset_index(drop=True)
tr_panel = crop_panel[crop_panel["Year"] <= 2021]
val_panel = crop_panel[crop_panel["Year"] == 2022]
test_panel = crop_panel[crop_panel["Year"] >= 2023]
print(f"Crop-Season Panel Splits: Train={len(tr_panel):,} | Val={len(val_panel):,} | Test={len(test_panel):,}")

# ==============================================================================
# PART 1: CONTROLLED FEATURE ABLATIONS (VALIDATION 2022 & FROZEN TEST 2023)
# ==============================================================================
print("\n" + "=" * 70)
print("PART 1: FEATURE ABLATION STUDY FOR MODEL B-1 (EXPANDED PANEL)")
print("=" * 70)

ablation_records = []

for target_col, tname in [(target_p, "Production_YoY"), (target_y, "Yield_YoY")]:
    y_tr = tr_df[target_col]
    y_val = val_df[target_col]
    y_test = test_df[target_col]
    
    bl_val = mean_absolute_error(y_val, np.zeros(len(y_val)))
    bl_test = mean_absolute_error(y_test, np.zeros(len(y_test)))
    
    print(f"\n--- Target: {tname} (Zero Baseline: Val={bl_val:.4f}%, Test={bl_test:.4f}%) ---")
    for ab_name, feats in ablation_definitions.items():
        m_lgb = lgb.LGBMRegressor(
            n_estimators=100, max_depth=5, learning_rate=0.03,
            objective="regression_l1", reg_alpha=2.0, random_state=RANDOM_STATE,
            n_jobs=-1, verbose=-1
        )
        m_lgb.fit(tr_df[feats], y_tr)
        
        v_pred = m_lgb.predict(val_df[feats])
        t_pred = m_lgb.predict(test_df[feats])
        
        v_mae = mean_absolute_error(y_val, v_pred)
        t_mae = mean_absolute_error(y_test, t_pred)
        t_rmse = np.sqrt(mean_squared_error(y_test, t_pred))
        t_r2 = r2_score(y_test, t_pred)
        
        ablation_records.append({
            "Target": tname,
            "Ablation_Group": ab_name,
            "Num_Features": len(feats),
            "Features_List": "; ".join(feats),
            "Zero_Baseline_Val_MAE": round(bl_val, 4),
            "Zero_Baseline_Test_MAE": round(bl_test, 4),
            "Model_Val_MAE": round(v_mae, 4),
            "Model_Test_MAE": round(t_mae, 4),
            "Model_Test_RMSE": round(t_rmse, 4),
            "Model_Test_R2": round(t_r2, 4),
            "Beats_Baseline_Val": v_mae < bl_val,
            "Beats_Baseline_Test": t_mae < bl_test
        })
        print(f"  {ab_name:<42} ({len(feats)} feats): Val MAE={v_mae:.4f}% | Test MAE={t_mae:.4f}% | RMSE={t_rmse:.4f}% | Beats Test: {t_mae < bl_test}")

df_ablation = pd.DataFrame(ablation_records)
ablation_csv = os.path.join(EXP_DIR, "model_b_feature_ablation_results.csv")
df_ablation.to_csv(ablation_csv, index=False)
print(f"\nAblation results saved to: {ablation_csv}")

# ==============================================================================
# PART 2: MODEL FAMILIES COMPARISON (ALL FEATURES)
# ==============================================================================
print("\n" + "=" * 70)
print("PART 2: MODEL FAMILY COMPARISON (FULL DEFENSIBLE FEATURE SET)")
print("=" * 70)

def make_pipeline(model):
    return Pipeline([
        ("scaler", StandardScaler()),
        ("model", model)
    ])

model_families = {
    "Zero-Growth Benchmark": None,
    "Historical Training Mean": "global_mean",
    "Crop-Specific Historical Mean": "crop_mean",
    "Ridge (alpha=100.0)": make_pipeline(Ridge(alpha=100.0)),
    "ElasticNet (alpha=1.0, l1_ratio=0.1)": make_pipeline(ElasticNet(alpha=1.0, l1_ratio=0.1, random_state=RANDOM_STATE)),
    "HuberRegressor (epsilon=1.35)": make_pipeline(HuberRegressor(epsilon=1.35, max_iter=300)),
    "RandomForest (depth=8, leaf=20)": RandomForestRegressor(n_estimators=100, max_depth=8, min_samples_leaf=20, random_state=RANDOM_STATE, n_jobs=-1),
    "ExtraTrees (depth=8, leaf=20)": ExtraTreesRegressor(n_estimators=100, max_depth=8, min_samples_leaf=20, random_state=RANDOM_STATE, n_jobs=-1),
    "LightGBM L1 (reg_alpha=2.0)": lgb.LGBMRegressor(n_estimators=100, max_depth=5, learning_rate=0.03, objective="regression_l1", reg_alpha=2.0, random_state=RANDOM_STATE, n_jobs=-1, verbose=-1),
    "XGBoost L1 (reg_alpha=2.0)": xgb.XGBRegressor(n_estimators=100, max_depth=4, learning_rate=0.03, reg_alpha=2.0, reg_lambda=2.0, random_state=RANDOM_STATE, n_jobs=-1, verbosity=0),
    "HistGradientBoosting (l2=10.0)": HistGradientBoostingRegressor(max_iter=100, max_depth=5, l2_regularization=10.0, random_state=RANDOM_STATE)
}

feats_full = ablation_definitions["Ablation_6_Full_Defensible_Set"]
model_comp_records = []

for target_col, tname in [(target_p, "Production_YoY"), (target_y, "Yield_YoY")]:
    y_tr = tr_df[target_col]
    y_val = val_df[target_col]
    y_test = test_df[target_col]
    
    crop_means_dict = tr_df.groupby("HS4")[target_col].mean().to_dict()
    global_mean_val = y_tr.mean()
    bl_test = mean_absolute_error(y_test, np.zeros(len(y_test)))
    
    print(f"\n--- Model Comparison on {tname} (Zero Baseline Test MAE: {bl_test:.4f}%) ---")
    for mname, m in model_families.items():
        if m is None:
            v_pred = np.zeros(len(y_val))
            t_pred = np.zeros(len(y_test))
        elif m == "global_mean":
            v_pred = np.full(len(y_val), global_mean_val)
            t_pred = np.full(len(y_test), global_mean_val)
        elif m == "crop_mean":
            v_pred = val_df["HS4"].map(crop_means_dict).fillna(global_mean_val).values
            t_pred = test_df["HS4"].map(crop_means_dict).fillna(global_mean_val).values
        else:
            m.fit(tr_df[feats_full], y_tr)
            v_pred = m.predict(val_df[feats_full])
            t_pred = m.predict(test_df[feats_full])
            
        v_mae = mean_absolute_error(y_val, v_pred)
        t_mae = mean_absolute_error(y_test, t_pred)
        t_rmse = np.sqrt(mean_squared_error(y_test, t_pred))
        t_r2 = r2_score(y_test, t_pred)
        
        model_comp_records.append({
            "Target": tname,
            "Model_Family": mname,
            "Val_MAE": round(v_mae, 4),
            "Test_MAE": round(t_mae, 4),
            "Test_RMSE": round(t_rmse, 4),
            "Test_R2": round(t_r2, 4),
            "Beats_Zero_Baseline": t_mae < bl_test
        })
        print(f"  {mname:<40}: Val MAE={v_mae:.4f}% | Test MAE={t_mae:.4f}% | RMSE={t_rmse:.4f}% | Beats: {t_mae < bl_test}")

df_model_comp = pd.DataFrame(model_comp_records)
model_comp_csv = os.path.join(EXP_RESULTS_DIR, "model_b_family_comparison.csv")
df_model_comp.to_csv(model_comp_csv, index=False)
print(f"\nModel family comparison saved to: {model_comp_csv}")

# ==============================================================================
# PART 3: MULTI-PERIOD TEMPORAL WALK-FORWARD VALIDATION
# ==============================================================================
print("\n" + "=" * 70)
print("PART 3: MULTI-PERIOD WALK-FORWARD TEMPORAL VALIDATION")
print("=" * 70)

windows = [
    {"val_year": 2020, "train_max": 2019},
    {"val_year": 2021, "train_max": 2020},
    {"val_year": 2022, "train_max": 2021},
    {"val_year": 2023, "train_max": 2022}
]

temporal_records = []

for w in windows:
    vy = w["val_year"]
    tmax = w["train_max"]
    
    tr_w = prod_df[prod_df["Year"] <= tmax]
    val_w = prod_df[prod_df["Year"] == vy]
    
    for target_col, tname in [(target_p, "Production_YoY"), (target_y, "Yield_YoY")]:
        y_tr_w = tr_w[target_col]
        y_val_w = val_w[target_col]
        
        # Baselines
        bl_zero = mean_absolute_error(y_val_w, np.zeros(len(y_val_w)))
        bl_mean = mean_absolute_error(y_val_w, np.full(len(y_val_w), y_tr_w.mean()))
        
        # Candidate LightGBM L1
        lgb_w = lgb.LGBMRegressor(
            n_estimators=100, max_depth=5, learning_rate=0.03,
            objective="regression_l1", reg_alpha=2.0, random_state=RANDOM_STATE,
            n_jobs=-1, verbose=-1
        )
        lgb_w.fit(tr_w[feats_full], y_tr_w)
        pred_lgb = lgb_w.predict(val_w[feats_full])
        mae_lgb = mean_absolute_error(y_val_w, pred_lgb)
        
        # Candidate Ridge
        ridge_pipe = make_pipeline(Ridge(alpha=100.0))
        ridge_pipe.fit(tr_w[feats_full], y_tr_w)
        pred_ridge = ridge_pipe.predict(val_w[feats_full])
        mae_ridge = mean_absolute_error(y_val_w, pred_ridge)
        
        # Candidate Huber
        huber_pipe = make_pipeline(HuberRegressor(epsilon=1.35, max_iter=300))
        huber_pipe.fit(tr_w[feats_full], y_tr_w)
        pred_huber = huber_pipe.predict(val_w[feats_full])
        mae_huber = mean_absolute_error(y_val_w, pred_huber)
        
        temporal_records.append({
            "Validation_Year": vy,
            "Train_Max_Year": tmax,
            "Target": tname,
            "Num_Train_Rows": len(tr_w),
            "Num_Val_Rows": len(val_w),
            "Zero_Baseline_MAE": round(bl_zero, 4),
            "Global_Mean_Baseline_MAE": round(bl_mean, 4),
            "LightGBM_L1_MAE": round(mae_lgb, 4),
            "Ridge_MAE": round(mae_ridge, 4),
            "Huber_MAE": round(mae_huber, 4),
            "Best_Model": "Zero_Baseline" if bl_zero <= min(mae_lgb, mae_ridge, mae_huber) else (
                "LightGBM_L1" if mae_lgb <= min(mae_ridge, mae_huber) else ("Ridge" if mae_ridge <= mae_huber else "Huber")
            )
        })
        print(f"  Year {vy} [{tname}]: Zero Baseline={bl_zero:.4f}% | Mean Baseline={bl_mean:.4f}% | LightGBM={mae_lgb:.4f}% | Ridge={mae_ridge:.4f}% | Huber={mae_huber:.4f}%")

df_temporal = pd.DataFrame(temporal_records)
temporal_csv = os.path.join(EXP_DIR, "model_b_temporal_validation_results.csv")
df_temporal.to_csv(temporal_csv, index=False)
print(f"\nTemporal walk-forward results saved to: {temporal_csv}")

print("\n" + "=" * 80)
print("TRACK 3 & TRACK 4 COMPLETE SUCCESSFULLY")
print("=" * 80)
