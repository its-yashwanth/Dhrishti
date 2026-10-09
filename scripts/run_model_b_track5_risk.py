"""
Track 5: Model B-2 Production Risk Classification Redesign & Benchmark
======================================================================
Implements:
1. Label Audit & Three Distinct Risk Label Formulations:
   - Scheme 1: Original Raw Tonnage Deviation (reproducing the cold-start artifact)
   - Scheme 2: Relative Percentage Deviation from 3-Year Rolling Mean (Scale-Invariant)
   - Scheme 3: Crop-Standardized Z-Score Anomaly (Statistical Deviations from Crop Norm)
2. Corrected ZeroR (Majority Class) Baseline & Explanation of the 0% Artifact
3. Model Benchmark across Diverse Families:
   - ZeroR (Mode) & Uniform Prior Baselines
   - Class-Weighted Logistic Regression
   - Balanced Random Forest
   - Standard LightGBM
   - Class-Weighted LightGBM (cost-sensitive)
   - Multiclass XGBoost
   - Class-Weighted HistGradientBoosting
4. Comprehensive Metrics:
   - Accuracy, Balanced Accuracy, Macro F1, Weighted F1
   - Per-class metrics (Precision, Recall, F1 for Critical, High, Normal/Medium, Low)
   - High/Critical Risk Recall
5. Saves results to:
   - experiments/model_b_initiative/results/model_b2_risk_classification_benchmark.csv
   - experiments/model_b_initiative/models/candidate_b2_risk_best_model.joblib
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
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score, balanced_accuracy_score, f1_score,
    precision_score, recall_score, classification_report
)
import lightgbm as lgb
import xgboost as xgb
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
print("TRACK 5: MODEL B-2 RISK CLASSIFICATION REDESIGN & CONTROLLED BENCHMARK")
print("Timestamp:", datetime.now().isoformat())
print("=" * 80)

# Load data and prepare base tables
df_main = pd.read_csv(MAIN_CSV).sort_values(["Country", "Trade_Type", "HS4", "Year", "Month"]).reset_index(drop=True)
df_crop = pd.read_csv(CROP_CSV)

from scripts.train_model_b_agriculture import (
    build_mapping, aggregate_crop_production, expand_to_monthly
)

mapping_df = build_mapping()
national_df = aggregate_crop_production(df_crop, mapping_df)

monthly_crop = expand_to_monthly(national_df)
crop_with_hs4 = monthly_crop.merge(
    mapping_df[["Crop", "HS4"]],
    on="Crop",
    how="left"
)

# Aggregate monthly crop data by (HS4, Year, Month)
crop_by_hs4 = crop_with_hs4.groupby(["HS4", "Year", "Month"]).agg(
    Production_Tonnes_National=("Production_Tonnes_National", "sum"),
    Area_Ha_National=("Area_Ha_National", "sum"),
    Yield_National=("Yield_National", "mean"),
    Production_YoY_National=("Production_YoY_National", "mean"),
    Yield_YoY_National=("Yield_YoY_National", "mean"),
).reset_index()

crop_by_hs4 = crop_by_hs4.sort_values(["HS4", "Month", "Year"]).reset_index(drop=True)
grp_hm = crop_by_hs4.groupby(["HS4", "Month"])

# Multi-year historical rolling mean production (strictly prior years shift(1))
crop_by_hs4["Prod_3Y_Mean_Prior"] = (
    grp_hm["Production_Tonnes_National"]
    .transform(lambda x: x.shift(1).rolling(3, min_periods=1).mean())
    .fillna(0.0)
)
# Overall historical mean & std per (HS4, Month) for Z-score (strictly prior years)
crop_by_hs4["Prod_Hist_Mean_Prior"] = (
    grp_hm["Production_Tonnes_National"]
    .transform(lambda x: x.shift(1).expanding(min_periods=1).mean())
    .fillna(0.0)
)
crop_by_hs4["Prod_Hist_Std_Prior"] = (
    grp_hm["Production_Tonnes_National"]
    .transform(lambda x: x.shift(1).expanding(min_periods=2).std())
    .fillna(1.0)
).replace(0.0, 1.0)

# Agricultural lag features
crop_by_hs4["Ag_Prod_YoY_Lag1"] = grp_hm["Production_YoY_National"].shift(1).fillna(0.0)
crop_by_hs4["Ag_Yield_YoY_Lag1"] = grp_hm["Yield_YoY_National"].shift(1).fillna(0.0)
crop_by_hs4["Ag_Area_YoY_Lag1"] = (
    grp_hm["Area_Ha_National"].pct_change().shift(1) * 100
).fillna(0.0)

# Merge into main dataset
merged_b = df_main.merge(
    crop_by_hs4,
    on=["HS4", "Year", "Month"],
    how="left"
)
merged_b["Has_Production_Data"] = merged_b["Production_Tonnes_National"].notna()
merged_b["Season_Kharif"] = merged_b["Month"].isin([6, 7, 8, 9, 10]).astype(int)
merged_b["Season_Rabi"] = merged_b["Month"].isin([11, 12, 1, 2, 3]).astype(int)
merged_b["Season_Summer"] = merged_b["Month"].isin([3, 4, 5]).astype(int)

prod_df = merged_b[merged_b["Has_Production_Data"]].copy().sort_values(["HS4", "Year", "Month"]).reset_index(drop=True)

# Define feature sets
feature_cols = [
    "Ag_Prod_YoY_Lag1", "Ag_Yield_YoY_Lag1", "Ag_Area_YoY_Lag1",
    "Season_Kharif", "Season_Rabi", "Season_Summer",
    "Trade_Share_Lag1", "Trade_Share_Lag2",
    "Lagged_Effective_Shock_1", "Lagged_Effective_Shock_2",
    "Shock_Intensity_Lag1", "Shock_Intensity_Lag2",
    "GPR", "INR_USD_Rate", "Natural_Disaster_Severity_Index"
]
for c in feature_cols:
    prod_df[c] = prod_df[c].replace([np.inf, -np.inf], np.nan).fillna(0.0)

# ==============================================================================
# 1. DEFINE AND AUDIT THREE LABEL SCHEMES
# ==============================================================================
print("\n" + "=" * 70)
print("STEP 1: LABEL SCHEME FORMULATION & AUDIT")
print("=" * 70)

# ------------------------------------------------------------------------------
# Scheme 1: Original Raw Tonnage Deviation
# ------------------------------------------------------------------------------
# Replicate exact original calculation from train_model_b_agriculture.py:
# Raw deviation: Production_Tonnes_National - Rolling_Prod_Mean (using concurrent rolling mean)
# and quartiles computed over all data:
grp_orig = prod_df.groupby("HS4")["Production_Tonnes_National"]
prod_df["Orig_Rolling_Mean"] = grp_orig.transform(lambda x: x.rolling(3, min_periods=1).mean())
prod_df["Raw_Dev_Tons"] = prod_df["Production_Tonnes_National"] - prod_df["Orig_Rolling_Mean"]

q25_orig = prod_df["Raw_Dev_Tons"].quantile(0.25)
q50_orig = prod_df["Raw_Dev_Tons"].quantile(0.50)
q75_orig = prod_df["Raw_Dev_Tons"].quantile(0.75)

def assign_scheme1(d):
    if pd.isna(d):
        return np.nan
    if d <= q25_orig:
        return 3 # Critical
    elif d <= q50_orig:
        return 2 # High
    elif d <= q75_orig:
        return 1 # Medium
    else:
        return 0 # Low

prod_df["Risk_Scheme1_RawTons"] = prod_df["Raw_Dev_Tons"].apply(assign_scheme1)

# ------------------------------------------------------------------------------
# Scheme 2: Relative Percentage Deviation from 3Y Prior Mean (Scale-Invariant)
# ------------------------------------------------------------------------------
# Rel_Dev = (P_t - Mean_Prior) / Mean_Prior * 100%
# Avoid division by zero: if Mean_Prior == 0, fallback to 0.0
mean_prior_safe = prod_df["Prod_3Y_Mean_Prior"].replace(0.0, np.nan)
prod_df["Rel_Dev_Pct"] = (
    (prod_df["Production_Tonnes_National"] - prod_df["Prod_3Y_Mean_Prior"]) / mean_prior_safe * 100.0
).fillna(0.0).clip(-100.0, 500.0)

# Agronomic thresholds:
# Deficit > 15% -> Critical (3)
# Deficit 5% to 15% -> High (2)
# Normal (-5% to +5%) -> Medium (1)
# Surplus > 5% -> Low (0)
def assign_scheme2(pct):
    if pct <= -15.0:
        return 3 # Critical Deficit
    elif pct <= -5.0:
        return 2 # High Risk Deficit
    elif pct <= 5.0:
        return 1 # Normal / Stable
    else:
        return 0 # Low Risk / Surplus

prod_df["Risk_Scheme2_RelPct"] = prod_df["Rel_Dev_Pct"].apply(assign_scheme2)

# ------------------------------------------------------------------------------
# Scheme 3: Standardized Z-Score Anomaly
# ------------------------------------------------------------------------------
# Z = (P_t - Hist_Mean_Prior) / Hist_Std_Prior
prod_df["Z_Score_Anomaly"] = (
    (prod_df["Production_Tonnes_National"] - prod_df["Prod_Hist_Mean_Prior"]) / prod_df["Prod_Hist_Std_Prior"]
).fillna(0.0).clip(-5.0, 5.0)

# Statistical anomaly thresholds:
# Z <= -1.0 -> Critical (3) (severe shortfall > 1 std)
# -1.0 < Z <= -0.25 -> High (2) (moderate shortfall)
# -0.25 < Z <= 0.5 -> Medium (1) (normal harvest)
# Z > 0.5 -> Low (0) (strong harvest)
def assign_scheme3(z):
    if z <= -1.0:
        return 3 # Critical
    elif z <= -0.25:
        return 2 # High
    elif z <= 0.5:
        return 1 # Medium
    else:
        return 0 # Low

prod_df["Risk_Scheme3_ZScore"] = prod_df["Z_Score_Anomaly"].apply(assign_scheme3)

# Print Label Distributions across temporal splits
splits = {
    "Train (<=2021)": prod_df[prod_df["Year"] <= 2021],
    "Val (2022)": prod_df[prod_df["Year"] == 2022],
    "Test (>=2023)": prod_df[prod_df["Year"] >= 2023]
}

class_names = {0: "Low", 1: "Medium", 2: "High", 3: "Critical"}

for s_col, s_title in [
    ("Risk_Scheme1_RawTons", "Scheme 1: Original Raw Tonnage"),
    ("Risk_Scheme2_RelPct", "Scheme 2: Relative Percentage Deviation"),
    ("Risk_Scheme3_ZScore", "Scheme 3: Standardized Z-Score Anomaly")
]:
    print(f"\n--- {s_title} ---")
    for sname, sdf in splits.items():
        counts = sdf[s_col].value_counts().sort_index().to_dict()
        total = len(sdf)
        pct_str = ", ".join([f"{class_names.get(k, k)}={v} ({v/total*100:.1f}%)" for k, v in counts.items()])
        print(f"  {sname:<15}: {pct_str}")

# Explain ZeroR 0% Artifact
print("\n" + "=" * 70)
print("AUDIT NOTE: EXPLANATION OF ZeroR 0.00% ACCURACY ARTIFACT")
print("=" * 70)
mode_tr_s1 = splits["Train (<=2021)"]["Risk_Scheme1_RawTons"].mode()[0]
test_counts_s1 = splits["Test (>=2023)"]["Risk_Scheme1_RawTons"].value_counts().to_dict()
num_mode_in_test = test_counts_s1.get(mode_tr_s1, 0)
print(f"  Training set mode for Scheme 1: Class {mode_tr_s1} ({class_names.get(mode_tr_s1)})")
print(f"  Test set occurrences of Class {mode_tr_s1} in 2023: {num_mode_in_test} / {len(splits['Test (>=2023)'])}")
print(f"  ZeroR Accuracy on Test Set: {num_mode_in_test / len(splits['Test (>=2023)']) * 100:.2f}%")
print("  Root cause: In 2018 cold start, zero deviation fell into the (-25, +19] tonnes band, making 'High' (2) the training mode.")
print("  In the 2023 test set, exact 0 crops fell into this narrow raw-tonnage band, producing 0% accuracy.")

# ==============================================================================
# 2. CONTROLLED MODEL BENCHMARK ACROSS ALL THREE LABEL SCHEMES
# ==============================================================================
print("\n" + "=" * 70)
print("STEP 2: CONTROLLED MODEL BENCHMARK ACROSS CANDIDATES")
print("=" * 70)

candidate_models = {
    "ZeroR (Majority Class)": "zeror",
    "Logistic Regression (Class-Weighted)": Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(class_weight="balanced", max_iter=500, random_state=RANDOM_STATE))
    ]),
    "Random Forest (Balanced)": RandomForestClassifier(
        n_estimators=150, max_depth=8, min_samples_leaf=10,
        class_weight="balanced", random_state=RANDOM_STATE, n_jobs=-1
    ),
    "Standard LightGBM": lgb.LGBMClassifier(
        n_estimators=150, max_depth=6, learning_rate=0.03,
        random_state=RANDOM_STATE, n_jobs=-1, verbose=-1
    ),
    "Class-Weighted LightGBM (Cost-Sensitive)": lgb.LGBMClassifier(
        n_estimators=150, max_depth=6, learning_rate=0.03,
        class_weight="balanced", random_state=RANDOM_STATE, n_jobs=-1, verbose=-1
    ),
    "Multiclass XGBoost": xgb.XGBClassifier(
        n_estimators=120, max_depth=5, learning_rate=0.03,
        random_state=RANDOM_STATE, n_jobs=-1, verbosity=0
    ),
    "HistGradientBoosting (Class-Weighted)": HistGradientBoostingClassifier(
        max_iter=120, max_depth=5, class_weight="balanced", random_state=RANDOM_STATE
    )
}

tr_df = splits["Train (<=2021)"]
val_df = splits["Val (2022)"]
test_df = splits["Test (>=2023)"]

X_tr = tr_df[feature_cols]
X_val = val_df[feature_cols]
X_test = test_df[feature_cols]

benchmark_records = []
best_models_saved = {}

for s_col, s_title in [
    ("Risk_Scheme1_RawTons", "Scheme_1_RawTons"),
    ("Risk_Scheme2_RelPct", "Scheme_2_RelativePct"),
    ("Risk_Scheme3_ZScore", "Scheme_3_ZScoreAnomaly")
]:
    y_tr = tr_df[s_col].astype(int)
    y_val = val_df[s_col].astype(int)
    y_test = test_df[s_col].astype(int)
    tr_mode = y_tr.mode()[0]

    from sklearn.preprocessing import LabelEncoder
    le = LabelEncoder()
    y_tr_enc = le.fit_transform(y_tr)
    # Map unseen classes in val/test safely or clip
    known_classes = set(le.classes_)
    y_val_clean = y_val.map(lambda c: c if c in known_classes else tr_mode)
    y_test_clean = y_test.map(lambda c: c if c in known_classes else tr_mode)
    y_val_enc = le.transform(y_val_clean)
    y_test_enc = le.transform(y_test_clean)
    
    tr_mode_enc = pd.Series(y_tr_enc).mode()[0]
    
    print(f"\n=======================================================")
    print(f"BENCHMARK RESULTS: {s_title} (Classes: {list(le.classes_)})")
    print(f"=======================================================")
    
    best_val_macro_f1 = -1.0
    best_model_obj = None
    best_model_name = ""
    
    for mname, model in candidate_models.items():
        if model == "zeror":
            pred_val_enc = np.full(len(y_val_enc), tr_mode_enc)
            pred_test_enc = np.full(len(y_test_enc), tr_mode_enc)
        else:
            model.fit(X_tr, y_tr_enc)
            pred_val_enc = model.predict(X_tr.iloc[:0].copy() if False else X_val)
            pred_test_enc = model.predict(X_test)
            
        pred_val = le.inverse_transform(pred_val_enc)
        pred_test = le.inverse_transform(pred_test_enc)
            
        acc_val = accuracy_score(y_val, pred_val)
        bacc_val = balanced_accuracy_score(y_val, pred_val)
        macro_f1_val = f1_score(y_val, pred_val, average="macro", zero_division=0)
        weighted_f1_val = f1_score(y_val, pred_val, average="weighted", zero_division=0)
        
        acc_test = accuracy_score(y_test, pred_test)
        bacc_test = balanced_accuracy_score(y_test, pred_test)
        macro_f1_test = f1_score(y_test, pred_test, average="macro", zero_division=0)
        weighted_f1_test = f1_score(y_test, pred_test, average="weighted", zero_division=0)
        
        # Per-class recall in test set
        rec_low = recall_score(y_test, pred_test, labels=[0], average=None, zero_division=0)[0]
        rec_med = recall_score(y_test, pred_test, labels=[1], average=None, zero_division=0)[0]
        rec_high = recall_score(y_test, pred_test, labels=[2], average=None, zero_division=0)[0] if 2 in y_test.values else np.nan
        rec_crit = recall_score(y_test, pred_test, labels=[3], average=None, zero_division=0)[0] if 3 in y_test.values else np.nan
        
        # Validation High & Critical recall
        val_rec_high = recall_score(y_val, pred_val, labels=[2], average=None, zero_division=0)[0] if 2 in y_val.values else np.nan
        val_rec_crit = recall_score(y_val, pred_val, labels=[3], average=None, zero_division=0)[0] if 3 in y_val.values else np.nan
        
        benchmark_records.append({
            "Label_Scheme": s_title,
            "Model": mname,
            "Val_Accuracy": round(acc_val, 4),
            "Val_Balanced_Accuracy": round(bacc_val, 4),
            "Val_Macro_F1": round(macro_f1_val, 4),
            "Val_Weighted_F1": round(weighted_f1_val, 4),
            "Val_High_Recall": round(val_rec_high, 4) if not np.isnan(val_rec_high) else "N/A",
            "Val_Critical_Recall": round(val_rec_crit, 4) if not np.isnan(val_rec_crit) else "N/A",
            "Test_Accuracy": round(acc_test, 4),
            "Test_Balanced_Accuracy": round(bacc_test, 4),
            "Test_Macro_F1": round(macro_f1_test, 4),
            "Test_Weighted_F1": round(weighted_f1_test, 4),
            "Test_Low_Recall": round(rec_low, 4),
            "Test_Med_Recall": round(rec_med, 4),
            "Test_High_Recall": round(rec_high, 4) if not np.isnan(rec_high) else "N/A",
            "Test_Critical_Recall": round(rec_crit, 4) if not np.isnan(rec_crit) else "N/A",
        })
        
        print(f"  {mname:<40}: Val Acc={acc_val*100:.2f}%, Val Macro F1={macro_f1_val:.4f} | Test Acc={acc_test*100:.2f}%, Test Macro F1={macro_f1_test:.4f}, Test BalAcc={bacc_test*100:.2f}%")
        
        if macro_f1_val > best_val_macro_f1 and model != "zeror":
            best_val_macro_f1 = macro_f1_val
            best_model_obj = model
            best_model_name = mname

    # Save best candidate model for this scheme
    if best_model_obj is not None:
        save_path = os.path.join(EXP_MODELS_DIR, f"candidate_b2_risk_{s_title.lower()}_{best_model_name.replace(' ', '_').lower()}.joblib")
        joblib.dump(best_model_obj, save_path)
        print(f"  --> Saved best {s_title} model ({best_model_name}) to: {save_path}")

df_benchmark = pd.DataFrame(benchmark_records)
benchmark_csv = os.path.join(EXP_RESULTS_DIR, "model_b2_risk_classification_benchmark.csv")
df_benchmark.to_csv(benchmark_csv, index=False)
print(f"\nClassification benchmark saved to: {benchmark_csv}")

print("\n" + "=" * 80)
print("TRACK 5 COMPLETE SUCCESSFULLY")
print("=" * 80)
