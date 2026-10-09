"""
Comprehensive Pipeline Diagnosis Script
Investigates target distributions, baseline behaviors, feature relationships,
and error characteristics across Models A, B, C, and D.
"""

import os
import json
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, r2_score, accuracy_score, classification_report, f1_score, confusion_matrix

import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
DATA_DIR = os.path.join(BASE_DIR, "data")
RESULTS_DIR = os.path.join(BASE_DIR, "results")

MAIN_CSV = os.path.join(DATA_DIR, "Drishti_Cascade_Final_With_EMDAT.csv")
CROP_CSV = os.path.join(DATA_DIR, "Crop_Production_Final.csv")

print("=" * 80)
print("DRISHTI ML PIPELINE DEEP DIAGNOSTIC AUDIT")
print("=" * 80)

df_main = pd.read_csv(MAIN_CSV)
print(f"Main dataset shape: {df_main.shape}")
print(f"Main dataset columns: {len(df_main.columns)}")
print(f"Year distribution:\n{df_main['Year'].value_counts().sort_index()}")

# ----------------------------------------------------
# 1. DIAGNOSE MODEL A (Trade Impact)
# ----------------------------------------------------
print("\n" + "=" * 60)
print("1. MODEL A: Trade_Return_1M DIAGNOSTIC")
print("=" * 60)
t_a = df_main["Trade_Return_1M"]
print(f"Trade_Return_1M summary:\n{t_a.describe()}")
print(f"Trade_Return_1M zero-fraction: {(t_a == 0).mean():.4f}")
print(f"Quantiles (1%, 5%, 50%, 95%, 99%): {np.quantile(t_a.dropna(), [0.01, 0.05, 0.5, 0.95, 0.99])}")

# Check baseline per year
df_sorted = df_main.sort_values(["Country", "Trade_Type", "HS4", "Year", "Month"]).copy()
df_sorted["a_persistence"] = df_sorted.groupby(["Country", "Trade_Type", "HS4"])["Trade_Return_1M"].shift(1).fillna(0)

for yr in sorted(df_sorted["Year"].unique()):
    sub = df_sorted[df_sorted["Year"] == yr]
    mae_pers = mean_absolute_error(sub["Trade_Return_1M"], sub["a_persistence"])
    mae_zero = mean_absolute_error(sub["Trade_Return_1M"], np.zeros(len(sub)))
    mean_val = sub["Trade_Return_1M"].mean()
    std_val = sub["Trade_Return_1M"].std()
    print(f"  Year {yr}: rows={len(sub):,}, mean={mean_val:.4f}, std={std_val:.4f}, persistence MAE={mae_pers:.4f}, zero MAE={mae_zero:.4f}")

# ----------------------------------------------------
# 2. DIAGNOSE MODEL B (Agricultural Impact)
# ----------------------------------------------------
print("\n" + "=" * 60)
print("2. MODEL B: Production_YoY, Yield_YoY, Production_Risk DIAGNOSTIC")
print("=" * 60)

# Load crop dataset and examine
df_crop = pd.read_csv(CROP_CSV)
print(f"Crop dataset shape: {df_crop.shape}")
print(f"Crops ({df_crop['Crop'].nunique()}): {df_crop['Crop'].unique()[:10]}...")
print(f"Crop_Year distribution:\n{df_crop['Crop_Year'].value_counts().sort_index()}")

from scripts.train_model_b_agriculture import build_mapping, aggregate_crop_production, expand_to_monthly, merge_with_main, compute_production_risk

mapping_df = build_mapping()
national_df = aggregate_crop_production(df_crop, mapping_df)
monthly_crop = expand_to_monthly(national_df)
merged_b = merge_with_main(df_main, monthly_crop, mapping_df)
merged_b = compute_production_risk(merged_b)

prod_matched = merged_b[merged_b["Has_Production_Data"]].copy()
print(f"\nMatched agricultural rows: {len(prod_matched):,} / {len(merged_b):,} ({len(prod_matched)/len(merged_b)*100:.2f}%)")

print("\n--- Production_YoY_National Distribution ---")
pyoy = prod_matched["Production_YoY_National"].dropna()
print(f"Count non-null: {len(pyoy)}")
print(f"Raw quantiles: {np.quantile(pyoy, [0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99])}")
print(f"Raw Min: {pyoy.min():.2f}, Max: {pyoy.max():.2f}, Mean: {pyoy.mean():.2f}, Median: {pyoy.median():.2f}")
print(f"Fraction |YoY| > 100%: {(pyoy.abs() > 100).mean():.4f}")
print(f"Fraction |YoY| > 500%: {(pyoy.abs() > 500).mean():.4f}")

# Target by year
print("\nProduction_YoY by Year (Clipped +/-500%):")
for yr in sorted(prod_matched["Year"].unique()):
    sub = prod_matched[prod_matched["Year"] == yr].dropna(subset=["Production_YoY_National"])
    if len(sub) == 0:
        continue
    vals_raw = sub["Production_YoY_National"]
    vals_clipped = vals_raw.clip(-500, 500)
    zero_mae = mean_absolute_error(vals_clipped, np.zeros(len(vals_clipped)))
    median_val = vals_clipped.median()
    mean_val = vals_clipped.mean()
    std_val = vals_clipped.std()
    mae_median = mean_absolute_error(vals_clipped, np.full(len(vals_clipped), median_val))
    print(f"  Year {yr}: n={len(sub):,}, mean={mean_val:.2f}, median={median_val:.2f}, std={std_val:.2f}, Zero-MAE={zero_mae:.2f}, Median-MAE={mae_median:.2f}")

print("\n--- Yield_YoY_National Distribution ---")
yyoy = prod_matched["Yield_YoY_National"].dropna()
print(f"Count non-null: {len(yyoy)}")
print(f"Raw quantiles: {np.quantile(yyoy, [0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99])}")
print(f"Raw Min: {yyoy.min():.2f}, Max: {yyoy.max():.2f}, Mean: {yyoy.mean():.2f}, Median: {yyoy.median():.2f}")

print("\nYield_YoY by Year (Clipped +/-500%):")
for yr in sorted(prod_matched["Year"].unique()):
    sub = prod_matched[prod_matched["Year"] == yr].dropna(subset=["Yield_YoY_National"])
    if len(sub) == 0:
        continue
    vals_raw = sub["Yield_YoY_National"]
    vals_clipped = vals_raw.clip(-500, 500)
    zero_mae = mean_absolute_error(vals_clipped, np.zeros(len(vals_clipped)))
    median_val = vals_clipped.median()
    mean_val = vals_clipped.mean()
    std_val = vals_clipped.std()
    mae_median = mean_absolute_error(vals_clipped, np.full(len(vals_clipped), median_val))
    print(f"  Year {yr}: n={len(sub):,}, mean={mean_val:.2f}, median={median_val:.2f}, std={std_val:.2f}, Zero-MAE={zero_mae:.2f}, Median-MAE={mae_median:.2f}")

print("\n--- Production_Risk Distribution (Train vs Val vs Test) ---")
for split_name, yr_filter in [("Train (<=2021)", prod_matched["Year"] <= 2021),
                              ("Val (2022)", prod_matched["Year"] == 2022),
                              ("Test (>=2023)", prod_matched["Year"] >= 2023)]:
    sub = prod_matched[yr_filter]
    print(f"  {split_name} (n={len(sub):,}):")
    dist = sub["Production_Risk"].value_counts(dropna=False)
    pcts = sub["Production_Risk"].value_counts(normalize=True, dropna=False) * 100
    for k in dist.index:
        print(f"    {k}: {dist[k]} ({pcts[k]:.1f}%)")

# ----------------------------------------------------
# 3. DIAGNOSE MODEL C (Price Impact)
# ----------------------------------------------------
print("\n" + "=" * 60)
print("3. MODEL C: Price_Return_1M DIAGNOSTIC")
print("=" * 60)
t_c = df_main["Price_Return_1M"]
print(f"Price_Return_1M summary:\n{t_c.describe()}")
print(f"Zero fraction: {(t_c == 0).mean():.4f}")
print(f"Quantiles (1%, 5%, 50%, 95%, 99%): {np.quantile(t_c.dropna(), [0.01, 0.05, 0.5, 0.95, 0.99])}")

df_sorted["c_persistence"] = df_sorted.groupby(["Country", "Trade_Type", "HS4"])["Price_Return_1M"].shift(1).fillna(0)
for yr in sorted(df_sorted["Year"].unique()):
    sub = df_sorted[df_sorted["Year"] == yr]
    mae_pers = mean_absolute_error(sub["Price_Return_1M"], sub["c_persistence"])
    mae_zero = mean_absolute_error(sub["Price_Return_1M"], np.zeros(len(sub)))
    mean_val = sub["Price_Return_1M"].mean()
    std_val = sub["Price_Return_1M"].std()
    print(f"  Year {yr}: rows={len(sub):,}, mean={mean_val:.4f}, std={std_val:.4f}, persistence MAE={mae_pers:.4f}, zero MAE={mae_zero:.4f}")

# ----------------------------------------------------
# 4. DIAGNOSE MODEL D (Economic Impact)
# ----------------------------------------------------
print("\n" + "=" * 60)
print("4. MODEL D: Agri_GVA_Growth_Percent & Inflation_Change_3M DIAGNOSTIC")
print("=" * 60)

annual_gva = df_main.groupby("Year")["Agri_GVA_Growth_Percent"].first()
print(f"Annual Agri_GVA_Growth_Percent:\n{annual_gva}")

infl = df_main["Inflation_Change_3M"]
print(f"\nInflation_Change_3M summary:\n{infl.describe()}")
for yr in sorted(df_main["Year"].unique()):
    sub = df_main[df_main["Year"] == yr]
    mae_zero = mean_absolute_error(sub["Inflation_Change_3M"], np.zeros(len(sub)))
    mean_val = sub["Inflation_Change_3M"].mean()
    std_val = sub["Inflation_Change_3M"].std()
    print(f"  Year {yr}: rows={len(sub):,}, mean={mean_val:.4f}, std={std_val:.4f}, Zero MAE={mae_zero:.4f}")

print("\n" + "=" * 80)
print("DIAGNOSTIC COMPLETE")
# End of diagnostic script
