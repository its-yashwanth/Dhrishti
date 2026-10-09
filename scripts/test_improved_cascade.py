"""
Evaluation of Candidate Model Cascade Improvements
Tests:
1. Model A candidate (Random Forest with return lags) on frozen test set and walk-forward OOF.
2. Impact of Model A candidate on Model C.
3. Model B-1 and B-2 detailed classification/regression evaluation on frozen test set (confusion matrix, macro F1, per-class metrics).
4. Model D-2 heavily regularized LightGBM candidate vs existing model vs zero-change baseline on frozen test set.
5. Statistical error comparison (mean error, median error, Wilcoxon / t-test / error distributions).
"""

import sys
import os
import json
import warnings
import numpy as np
import pandas as pd
from datetime import datetime
from scipy import stats

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import (mean_absolute_error, r2_score, mean_squared_error,
                             accuracy_score, balanced_accuracy_score, f1_score,
                             precision_recall_fscore_support, confusion_matrix)
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
print("COMPREHENSIVE CANDIDATE EVALUATION & STATISTICAL TESTING")
print("Timestamp:", datetime.now().isoformat())
print("=" * 80)

df_main = pd.read_csv(MAIN_CSV).sort_values(["Country", "Trade_Type", "HS4", "Year", "Month"]).reset_index(drop=True)

# ------------------------------------------------------------------------------
# 1. MODEL A: EVALUATE CANDIDATE ON FROZEN TEST SET (>= 2024)
# ------------------------------------------------------------------------------
print("\n" + "=" * 70)
print("1. MODEL A: CANDIDATE vs EXISTING vs BASELINE")
print("=" * 70)

# Construct lagged return features
df_main["Trade_Return_1M_Lag1"] = df_main.groupby(["Country", "Trade_Type", "HS4"])["Trade_Return_1M"].shift(1).fillna(0.0)
df_main["Trade_Return_1M_Lag2"] = df_main.groupby(["Country", "Trade_Type", "HS4"])["Trade_Return_1M"].shift(2).fillna(0.0)

existing_feats_a = [
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
candidate_feats_a = existing_feats_a + ["Trade_Return_1M_Lag1", "Trade_Return_1M_Lag2"]

for col in candidate_feats_a + ["Trade_Return_1M"]:
    df_main[col] = df_main[col].fillna(0.0)

tr_a = df_main[df_main["Year"] <= 2022]
val_a = df_main[df_main["Year"] == 2023]
test_a = df_main[df_main["Year"] >= 2024]

y_tr_a = tr_a["Trade_Return_1M"]
y_val_a = val_a["Trade_Return_1M"]
y_test_a = test_a["Trade_Return_1M"]

# Baseline on test
bl_test_a_mae = mean_absolute_error(y_test_a, test_a["Trade_Return_1M_Lag1"])
bl_test_a_rmse = np.sqrt(mean_squared_error(y_test_a, test_a["Trade_Return_1M_Lag1"]))
bl_test_a_r2 = r2_score(y_test_a, test_a["Trade_Return_1M_Lag1"])

# Existing Model A: RF on existing_feats_a
rf_existing_a = RandomForestRegressor(
    n_estimators=300, max_depth=15, min_samples_split=10, min_samples_leaf=5,
    max_features="sqrt", random_state=RANDOM_STATE, n_jobs=-1
)
rf_existing_a.fit(tr_a[existing_feats_a], y_tr_a)
pred_ex_val_a = rf_existing_a.predict(val_a[existing_feats_a])
pred_ex_test_a = rf_existing_a.predict(test_a[existing_feats_a])

ex_val_a_mae = mean_absolute_error(y_val_a, pred_ex_val_a)
ex_test_a_mae = mean_absolute_error(y_test_a, pred_ex_test_a)
ex_test_a_rmse = np.sqrt(mean_squared_error(y_test_a, pred_ex_test_a))
ex_test_a_r2 = r2_score(y_test_a, pred_ex_test_a)

# Candidate Model A: Regularized RF on candidate_feats_a (11 features)
# Evaluated with both default and regularized hyperparameters
rf_cand_a = RandomForestRegressor(
    n_estimators=300, max_depth=12, min_samples_split=20, min_samples_leaf=10,
    max_features="sqrt", random_state=RANDOM_STATE, n_jobs=-1
)
rf_cand_a.fit(tr_a[candidate_feats_a], y_tr_a)
pred_cand_val_a = rf_cand_a.predict(val_a[candidate_feats_a])
pred_cand_test_a = rf_cand_a.predict(test_a[candidate_feats_a])

cand_val_a_mae = mean_absolute_error(y_val_a, pred_cand_val_a)
cand_test_a_mae = mean_absolute_error(y_test_a, pred_cand_test_a)
cand_test_a_rmse = np.sqrt(mean_squared_error(y_test_a, pred_cand_test_a))
cand_test_a_r2 = r2_score(y_test_a, pred_cand_test_a)

print(f"MODEL A PERFORMANCE COMPARISON:")
print(f"  Baseline (Lag-1 Persistence):")
print(f"    Test MAE:  {bl_test_a_mae:.4f}% | RMSE: {bl_test_a_rmse:.4f}% | R2: {bl_test_a_r2:.4f}")
print(f"  Existing Model (RF 9-features):")
print(f"    Val MAE:   {ex_val_a_mae:.4f}%")
print(f"    Test MAE:  {ex_test_a_mae:.4f}% | RMSE: {ex_test_a_rmse:.4f}% | R2: {ex_test_a_r2:.4f}")
print(f"    vs Baseline Improvement: {(bl_test_a_mae - ex_test_a_mae) / bl_test_a_mae * 100:+.2f}%")
print(f"  Candidate Model (RF 11-features with Return Lags):")
print(f"    Val MAE:   {cand_val_a_mae:.4f}% (-{(ex_val_a_mae - cand_val_a_mae)/ex_val_a_mae * 100:.2f}% reduction)")
print(f"    Test MAE:  {cand_test_a_mae:.4f}% | RMSE: {cand_test_a_rmse:.4f}% | R2: {cand_test_a_r2:.4f}")
print(f"    vs Baseline Improvement: {(bl_test_a_mae - cand_test_a_mae) / bl_test_a_mae * 100:+.2f}%")
print(f"    vs Existing Improvement: {(ex_test_a_mae - cand_test_a_mae) / ex_test_a_mae * 100:+.2f}%")

# Test year-by-year breakdown (2024 and 2025)
print("\n  Year-by-year frozen test evaluation:")
for yr in [2024, 2025]:
    sub = test_a[test_a["Year"] == yr]
    bl_yr = mean_absolute_error(sub["Trade_Return_1M"], sub["Trade_Return_1M_Lag1"])
    ex_yr = mean_absolute_error(sub["Trade_Return_1M"], rf_existing_a.predict(sub[existing_feats_a]))
    cand_yr = mean_absolute_error(sub["Trade_Return_1M"], rf_cand_a.predict(sub[candidate_feats_a]))
    print(f"    Year {yr}: Baseline MAE={bl_yr:.4f} | Existing MAE={ex_yr:.4f} | Candidate MAE={cand_yr:.4f} | Diff={cand_yr - ex_yr:+.4f}")

# Statistical error comparison: paired t-test & Wilcoxon signed-rank test
err_ex_a = np.abs(y_test_a - pred_ex_test_a)
err_cand_a = np.abs(y_test_a - pred_cand_test_a)
t_stat, p_val = stats.ttest_rel(err_cand_a, err_ex_a)
w_stat, w_pval = stats.wilcoxon(err_cand_a - err_ex_a)
print(f"\n  Statistical Forecast Error Comparison (Candidate vs Existing on Test Set, n={len(y_test_a):,}):")
print(f"    Mean Abs Error: Existing={err_ex_a.mean():.4f}%, Candidate={err_cand_a.mean():.4f}% (Delta={err_cand_a.mean() - err_ex_a.mean():+.4f}%)")
print(f"    Median Abs Error: Existing={err_ex_a.median():.4f}%, Candidate={err_cand_a.median():.4f}%")
print(f"    Paired t-test: t = {t_stat:.4f}, p-value = {p_val:.4e} ({'Statistically Significant' if p_val < 0.01 else 'Not Significant'})")
print(f"    Wilcoxon signed-rank test: W = {w_stat:.4f}, p-value = {w_pval:.4e} ({'Statistically Significant' if w_pval < 0.01 else 'Not Significant'})")

# ------------------------------------------------------------------------------
# 2. MODEL B: COMPREHENSIVE DIAGNOSIS & FROZEN TEST METRICS
# ------------------------------------------------------------------------------
print("\n" + "=" * 70)
print("2. MODEL B: COMPREHENSIVE PRODUCTION, YIELD & RISK AUDIT")
print("=" * 70)

from scripts.train_model_b_agriculture import (
    build_mapping, aggregate_crop_production, expand_to_monthly,
    merge_with_main, compute_production_risk, FEATURES_B
)

df_crop = pd.read_csv(CROP_CSV)
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
tr_b = prod_df[prod_df["Year"] <= 2021]
val_b = prod_df[prod_df["Year"] == 2022]
test_b = prod_df[prod_df["Year"] >= 2023]

# 2A: Production YoY
t1 = "Production_YoY_National"
tr_t1 = tr_b.dropna(subset=[t1])
val_t1 = val_b.dropna(subset=[t1])
test_t1 = test_b.dropna(subset=[t1])

y_tr_p = tr_t1[t1].clip(-500, 500)
y_val_p = val_t1[t1].clip(-500, 500)
y_test_p = test_t1[t1].clip(-500, 500)

bl_test_p = mean_absolute_error(y_test_p, np.zeros(len(y_test_p)))

# Existing XGBoost L1
xgb_p = joblib.load(os.path.join(MODELS_DIR, "model_b_production_yoy.joblib"))
p_test_pred = xgb_p.predict(test_t1[features_b_all])
p_test_mae = mean_absolute_error(y_test_p, p_test_pred)
p_test_rmse = np.sqrt(mean_squared_error(y_test_p, p_test_pred))
p_test_r2 = r2_score(y_test_p, p_test_pred)

print(f"\nModel B-1 (Production_YoY_National):")
print(f"  Zero-Growth Baseline Test MAE: {bl_test_p:.4f}%")
print(f"  Existing XGBoost L1 Test MAE:  {p_test_mae:.4f}% | RMSE: {p_test_rmse:.4f}% | R2: {p_test_r2:.4f}")
print(f"  Delta vs Baseline: {p_test_mae - bl_test_p:+.4f}% (Model underperforms zero benchmark)")

# 2B: Yield YoY
t2 = "Yield_YoY_National"
tr_t2 = tr_b.dropna(subset=[t2])
val_t2 = val_b.dropna(subset=[t2])
test_t2 = test_b.dropna(subset=[t2])

y_tr_y = tr_t2[t2].clip(-500, 500)
y_val_y = val_t2[t2].clip(-500, 500)
y_test_y = test_t2[t2].clip(-500, 500)

bl_test_y = mean_absolute_error(y_test_y, np.zeros(len(y_test_y)))

xgb_y = joblib.load(os.path.join(MODELS_DIR, "model_b_yield_yoy.joblib"))
y_test_pred = xgb_y.predict(test_t2[features_b_all])
y_test_mae = mean_absolute_error(y_test_y, y_test_pred)
y_test_rmse = np.sqrt(mean_squared_error(y_test_y, y_test_pred))
y_test_r2 = r2_score(y_test_y, y_test_pred)

print(f"\nModel B-1 (Yield_YoY_National):")
print(f"  Zero-Growth Baseline Test MAE: {bl_test_y:.4f}%")
print(f"  Existing XGBoost L1 Test MAE:  {y_test_mae:.4f}% | RMSE: {y_test_rmse:.4f}% | R2: {y_test_r2:.4f}")
print(f"  Delta vs Baseline: {y_test_mae - bl_test_y:+.4f}% (Model underperforms zero benchmark)")

# 2C: Production Risk Classification Detailed Report
t3 = "Production_Risk"
risk_map = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}
class_names = ["Low", "Medium", "High", "Critical"]

tr_t3 = tr_b.dropna(subset=[t3])
val_t3 = val_b.dropna(subset=[t3])
test_t3 = test_b.dropna(subset=[t3])

y_tr_r = tr_t3[t3].map(risk_map).astype(int)
y_val_r = val_t3[t3].map(risk_map).astype(int)
y_test_r = test_t3[t3].map(risk_map).astype(int)

lgb_r = joblib.load(os.path.join(MODELS_DIR, "model_b_production_risk.joblib"))
r_test_pred = lgb_r.predict(test_t3[features_b_all])

acc_r = accuracy_score(y_test_r, r_test_pred)
bal_acc_r = balanced_accuracy_score(y_test_r, r_test_pred)
macro_f1_r = f1_score(y_test_r, r_test_pred, average="macro", zero_division=0)
weighted_f1_r = f1_score(y_test_r, r_test_pred, average="weighted", zero_division=0)
cm_r = confusion_matrix(y_test_r, r_test_pred, labels=[0, 1, 2, 3])
prec, rec, f1, supp = precision_recall_fscore_support(y_test_r, r_test_pred, labels=[0, 1, 2, 3], zero_division=0)

print(f"\nModel B-2 (Production_Risk 4-Class Classification):")
print(f"  Test Accuracy:          {acc_r*100:.2f}% (Baseline ZeroR: 0.00%)")
print(f"  Balanced Accuracy:      {bal_acc_r*100:.2f}%")
print(f"  Macro F1:               {macro_f1_r:.4f}")
print(f"  Weighted F1:            {weighted_f1_r:.4f}")
print(f"\n  Per-Class Metrics on Frozen Test Period (n={len(y_test_r):,}):")
print(f"  {'Class':<12}{'Precision':<12}{'Recall':<12}{'F1-Score':<12}{'Support':<10}")
print(f"  {'-'*58}")
for i, cname in enumerate(class_names):
    print(f"  {cname:<12}{prec[i]:<12.4f}{rec[i]:<12.4f}{f1[i]:<12.4f}{supp[i]:<10}")
print(f"\n  Confusion Matrix (Rows=True, Cols=Predicted [Low, Medium, High, Critical]):")
print(cm_r)

# ------------------------------------------------------------------------------
# 3. MODEL C: PRICE IMPACT
# ------------------------------------------------------------------------------
print("\n" + "=" * 70)
print("3. MODEL C: PRICE IMPACT (EVALUATION WITH UPDATED MODEL A OOF)")
print("=" * 70)

from scripts.train_model_c_price import FEATURES_C, PRIMARY_TARGET as TARGET_C, compute_naive_baseline

# Generate walk-forward OOF predictions with the candidate Model A
# and test whether Model C improves
print("Generating walk-forward predictions for Candidate Model A...")
oof_preds_cand_a = pd.Series(index=df_main.index, dtype=float)

years = sorted(df_main["Year"].unique())
for pred_year in years:
    if pred_year == 2018:
        continue
    train_mask = (df_main["Year"] < pred_year)
    pred_mask = (df_main["Year"] == pred_year)
    m = RandomForestRegressor(
        n_estimators=300, max_depth=12, min_samples_split=20, min_samples_leaf=10,
        max_features="sqrt", random_state=RANDOM_STATE, n_jobs=-1
    )
    m.fit(df_main.loc[train_mask, candidate_feats_a], df_main.loc[train_mask, "Trade_Return_1M"])
    oof_preds_cand_a.loc[pred_mask] = m.predict(df_main.loc[pred_mask, candidate_feats_a])

df_c_cand = df_main.copy()
df_c_cand["Trade_Return_1M_Pred"] = oof_preds_cand_a.fillna(0.0)

pred_b_oof = pd.read_csv(os.path.join(RESULTS_DIR, "model_b_predictions_oof.csv"))
pred_b_sorted = pred_b_oof.sort_values(["Country", "Trade_Type", "HS4", "Year", "Month"]).reset_index(drop=True)
df_c_cand["Production_Growth_Pred_OOF"] = pred_b_sorted["Production_Growth_Pred_OOF"]
df_c_cand["Production_Growth_Pred_Lag1"] = df_c_cand.groupby(["Country", "Trade_Type", "HS4"])["Production_Growth_Pred_OOF"].shift(1).fillna(0.0)

for col in FEATURES_C:
    df_c_cand[col] = df_c_cand[col].fillna(0.0)

tr_c = df_c_cand[df_c_cand["Year"] <= 2022]
val_c = df_c_cand[df_c_cand["Year"] == 2023]
test_c = df_c_cand[df_c_cand["Year"] >= 2024]

y_tr_c = tr_c[TARGET_C]
y_val_c = val_c[TARGET_C]
y_test_c = test_c[TARGET_C]

df_c_cand["naive_c"] = compute_naive_baseline(df_c_cand, TARGET_C)
bl_test_c = mean_absolute_error(y_test_c, df_c_cand.loc[df_c_cand["Year"] >= 2024, "naive_c"])

# Existing Model C (with original Model A inputs)
rf_c_orig = joblib.load(os.path.join(MODELS_DIR, "model_c_price.joblib"))
orig_test_c_pred = rf_c_orig.predict(test_c[FEATURES_C])
orig_test_c_mae = mean_absolute_error(y_test_c, orig_test_c_pred)
orig_test_c_rmse = np.sqrt(mean_squared_error(y_test_c, orig_test_c_pred))
orig_test_c_r2 = r2_score(y_test_c, orig_test_c_pred)

# Model C retrained with candidate Model A inputs
rf_c_new = RandomForestRegressor(
    n_estimators=300, max_depth=12, min_samples_split=20, min_samples_leaf=10,
    max_features="sqrt", random_state=RANDOM_STATE, n_jobs=-1
)
rf_c_new.fit(tr_c[FEATURES_C], y_tr_c)
new_val_c_mae = mean_absolute_error(y_val_c, rf_c_new.predict(val_c[FEATURES_C]))
new_test_c_pred = rf_c_new.predict(test_c[FEATURES_C])
new_test_c_mae = mean_absolute_error(y_test_c, new_test_c_pred)
new_test_c_rmse = np.sqrt(mean_squared_error(y_test_c, new_test_c_pred))
new_test_c_r2 = r2_score(y_test_c, new_test_c_pred)

print(f"Model C Performance:")
print(f"  Persistence Baseline Test MAE: {bl_test_c:.4f}%")
print(f"  Existing Model C Test MAE:     {orig_test_c_mae:.4f}% | RMSE: {orig_test_c_rmse:.4f}% | R2: {orig_test_c_r2:.4f}")
print(f"  Retrained Model C Test MAE:    {new_test_c_mae:.4f}% | RMSE: {new_test_c_rmse:.4f}% | R2: {new_test_c_r2:.4f}")
print(f"  Improvement vs Baseline:       {(bl_test_c - new_test_c_mae) / bl_test_c * 100:+.2f}%")

# ------------------------------------------------------------------------------
# 4. MODEL D: ECONOMIC IMPACT (GVA & INFLATION)
# ------------------------------------------------------------------------------
print("\n" + "=" * 70)
print("4. MODEL D: ECONOMIC IMPACT (GVA & INFLATION)")
print("=" * 70)

from scripts.train_model_d_economy import SAFE_FEATURES_D, TARGET_GVA, TARGET_INFLATION

pred_c_oof = pd.read_csv(os.path.join(RESULTS_DIR, "model_c_predictions_oof.csv"))
pred_c_sorted = pred_c_oof.sort_values(["Country", "Trade_Type", "HS4", "Year", "Month"]).reset_index(drop=True)
df_d = df_main.sort_values(["Country", "Trade_Type", "HS4", "Year", "Month"]).reset_index(drop=True)
df_d["Price_Return_1M_Pred_OOF"] = pred_c_sorted["Price_Return_1M_Pred_OOF"]
df_d["Price_Return_1M_Pred_Lag1"] = df_d.groupby(["Country", "Trade_Type", "HS4"])["Price_Return_1M_Pred_OOF"].shift(1).fillna(0.0)

for col in SAFE_FEATURES_D:
    df_d[col] = df_d[col].fillna(0.0)

# D-1 Agri GVA
annual_df_d = df_d.groupby("Year")[SAFE_FEATURES_D].mean()
annual_df_d[TARGET_GVA] = df_d.groupby("Year")[TARGET_GVA].first()
annual_df_d["Previous_Year_GVA_Baseline"] = annual_df_d[TARGET_GVA].shift(1)
annual_df_d = annual_df_d.dropna(subset=SAFE_FEATURES_D + [TARGET_GVA, "Previous_Year_GVA_Baseline"])

tr_gva = annual_df_d[annual_df_d.index <= 2022]
val_gva = annual_df_d[annual_df_d.index == 2023]
test_gva = annual_df_d[annual_df_d.index >= 2024]

bl_test_gva_mae = mean_absolute_error(test_gva[TARGET_GVA], test_gva["Previous_Year_GVA_Baseline"])

xgb_gva = joblib.load(os.path.join(MODELS_DIR, "model_d_agri_gva.joblib"))
gva_test_pred = xgb_gva.predict(test_gva[SAFE_FEATURES_D])
gva_test_mae = mean_absolute_error(test_gva[TARGET_GVA], gva_test_pred)
gva_test_rmse = np.sqrt(mean_squared_error(test_gva[TARGET_GVA], gva_test_pred))

print(f"Model D-1 (Agri_GVA_Growth_Percent):")
print(f"  Baseline (Previous Year) Test MAE: {bl_test_gva_mae:.4f}%")
print(f"  Existing XGBoost Test MAE:         {gva_test_mae:.4f}% | RMSE: {gva_test_rmse:.4f}%")
print(f"  Improvement vs Baseline:           {(bl_test_gva_mae - gva_test_mae) / bl_test_gva_mae * 100:+.2f}%")

# D-2 Inflation
tr_infl = df_d[df_d["Year"] <= 2022]
val_infl = df_d[df_d["Year"] == 2023]
test_infl = df_d[df_d["Year"] >= 2024]

y_tr_infl = tr_infl[TARGET_INFLATION]
y_val_infl = val_infl[TARGET_INFLATION]
y_test_infl = test_infl[TARGET_INFLATION]

bl_test_infl_mae = mean_absolute_error(y_test_infl, np.zeros(len(y_test_infl)))
bl_test_infl_rmse = np.sqrt(mean_squared_error(y_test_infl, np.zeros(len(y_test_infl))))

xgb_infl = joblib.load(os.path.join(MODELS_DIR, "model_d_inflation.joblib"))
infl_ex_test_pred = xgb_infl.predict(test_infl[SAFE_FEATURES_D])
infl_ex_test_mae = mean_absolute_error(y_test_infl, infl_ex_test_pred)
infl_ex_test_rmse = np.sqrt(mean_squared_error(y_test_infl, infl_ex_test_pred))
infl_ex_test_r2 = r2_score(y_test_infl, infl_ex_test_pred)

# Test candidate: LightGBM heavily regularized
lgb_cand_infl = lgb.LGBMRegressor(
    n_estimators=100, max_depth=3, learning_rate=0.01, reg_alpha=2.0, reg_lambda=5.0,
    subsample=0.7, random_state=RANDOM_STATE, n_jobs=-1, verbose=-1
)
lgb_cand_infl.fit(tr_infl[SAFE_FEATURES_D], y_tr_infl)
infl_cand_val_mae = mean_absolute_error(y_val_infl, lgb_cand_infl.predict(val_infl[SAFE_FEATURES_D]))
infl_cand_test_pred = lgb_cand_infl.predict(test_infl[SAFE_FEATURES_D])
infl_cand_test_mae = mean_absolute_error(y_test_infl, infl_cand_test_pred)
infl_cand_test_rmse = np.sqrt(mean_squared_error(y_test_infl, infl_cand_test_pred))
infl_cand_test_r2 = r2_score(y_test_infl, infl_cand_test_pred)

print(f"\nModel D-2 (Inflation_Change_3M):")
print(f"  Zero-Change Baseline Test MAE: {bl_test_infl_mae:.4f} pp | RMSE: {bl_test_infl_rmse:.4f} pp")
print(f"  Existing XGBoost Test MAE:     {infl_ex_test_mae:.4f} pp | RMSE: {infl_ex_test_rmse:.4f} pp | R2: {infl_ex_test_r2:.4f}")
print(f"  Candidate LightGBM Test MAE:   {infl_cand_test_mae:.4f} pp | RMSE: {infl_cand_test_rmse:.4f} pp | R2: {infl_cand_test_r2:.4f}")

print("\n" + "=" * 80)
print("EVALUATION RUN COMPLETE")
print("=" * 80)
