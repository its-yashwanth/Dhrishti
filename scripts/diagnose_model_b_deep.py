"""
Deep Diagnostic Audit of Model B-1 and Model B-2 Data Construction
===================================================================
Investigates:
1. Raw agricultural observations, unique crop-season-year combinations, merge expansions.
2. Number of duplicated targets and pseudo-replication across bilateral trade records.
3. Target formulas, distributions by year, crop, and season, small denominators, clipping.
4. Production risk quantile thresholds (Low, Medium, High, Critical) and test window distribution.
5. Crop-level vs bilateral trade-level aggregation and forecasting unit analysis.
"""

import os
import sys
import json
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
DATA_DIR = os.path.join(BASE_DIR, "data")
RESULTS_DIR = os.path.join(BASE_DIR, "results")

MAIN_CSV = os.path.join(DATA_DIR, "Drishti_Cascade_Final_With_EMDAT.csv")
CROP_CSV = os.path.join(DATA_DIR, "Crop_Production_Final.csv")

print("=" * 80)
print("PHASE 2: DEEP DIAGNOSTIC AUDIT OF MODEL B DATA CONSTRUCTION & TARGETS")
print("=" * 80)

# 1. Raw Crop Production Data
df_crop = pd.read_csv(CROP_CSV)
print(f"\n1. RAW CROP PRODUCTION DATASET:")
print(f"  Total raw rows: {len(df_crop):,}")
print(f"  Districts: {df_crop['District'].nunique()} across {df_crop['State'].nunique()} states")
print(f"  Crops: {df_crop['Crop'].nunique()}")
print(f"  Seasons: {df_crop['Season'].unique().tolist()}")
print(f"  Crop Years: {sorted(df_crop['Crop_Year'].unique().tolist())}")

# 2. Crop Mapping & National Aggregation
from scripts.train_model_b_agriculture import (
    build_mapping, aggregate_crop_production, expand_to_monthly,
    merge_with_main, compute_production_risk, CROP_HS4_MAPPING, EXCLUDED_CROPS
)

mapping_df = build_mapping()
mapped_crops = mapping_df["Crop"].unique()
print(f"\n2. MAPPING AUDIT:")
print(f"  Mapped crops count: {len(mapped_crops)}")
print(f"  Excluded crops count: {len(EXCLUDED_CROPS)}")

crop_mapped = df_crop[df_crop["Crop"].isin(mapped_crops)].dropna(subset=["Production_Tonnes"])
print(f"  Raw rows with mapped crops & non-null production: {len(crop_mapped):,}")

# National aggregation
national = aggregate_crop_production(df_crop, mapping_df)
print(f"\n3. NATIONAL AGGREGATION AUDIT:")
print(f"  National seasonal rows: {len(national)}")
print(f"  Unique crops in national: {national['Crop'].nunique()}")
print(f"  Unique seasons in national: {national['Season'].unique().tolist()}")
print(f"  Unique Crop_Years in national: {sorted(national['Crop_Year'].unique().tolist())}")

# Breakdown by Crop_Year at national level
print("\n  National observations by Crop_Year:")
for cy, grp in national.groupby("Crop_Year"):
    print(f"    Crop_Year {cy}: {len(grp)} seasonal crop records | Unique crops: {grp['Crop'].nunique()}")

# 3. Target Distribution at National Level
print(f"\n4. TARGET DEFINITION & DISTRIBUTION (NATIONAL LEVEL):")
for col in ["Production_YoY_National", "Yield_YoY_National"]:
    s = national[col].dropna()
    print(f"\n  Target: {col} (n={len(s)})")
    print(f"    Min:    {s.min():.2f}%")
    print(f"    q05:    {s.quantile(0.05):.2f}%")
    print(f"    Median: {s.median():.2f}%")
    print(f"    Mean:   {s.mean():.2f}%")
    print(f"    q95:    {s.quantile(0.95):.2f}%")
    print(f"    Max:    {s.max():.2f}%")
    print(f"    Extreme > +100%: {(s > 100).sum()} ({(s > 100).mean()*100:.1f}%)")
    print(f"    Extreme < -50%:  {(s < -50).sum()} ({(s < -50).mean()*100:.1f}%)")
    print(f"    Clipped at +/-500%: {((s >= 500) | (s <= -500)).sum()}")

# Inspect top extreme growth crops at national level
top_prod_growth = national.sort_values("Production_YoY_National", ascending=False).head(10)
print(f"\n  Top 10 Largest Production_YoY_National values (National seasonal level):")
for _, r in top_prod_growth.iterrows():
    print(f"    {r['Crop']:<15} {r['Season']:<10} {r['Crop_Year']:<10} YoY={r['Production_YoY_National']:>8.1f}% | Area={r['Area_Ha_National']:>10.0f} ha | Prod={r['Production_Tonnes_National']:>10.0f} t")

# 4. Monthly Expansion Audit
monthly_crop = expand_to_monthly(national)
print(f"\n5. MONTHLY EXPANSION AUDIT:")
print(f"  Monthly rows: {len(monthly_crop)}")
print(f"  Unique (Crop, Year, Month) cells: {len(monthly_crop[['Crop', 'Year', 'Month']].drop_duplicates())}")
print(f"  Calendar Years covered: {sorted(monthly_crop['Year'].unique().tolist())}")

# 5. Merge with Main Trade Dataset
df_main = pd.read_csv(MAIN_CSV)
merged = merge_with_main(df_main, monthly_crop, mapping_df)
merged = compute_production_risk(merged)

has_prod = merged[merged["Has_Production_Data"]].copy()
print(f"\n6. MERGED DATASET PSEUDO-REPLICATION AUDIT:")
print(f"  Total trade rows in main dataset: {len(df_main):,}")
print(f"  Crop-matched trade rows: {len(has_prod):,} ({len(has_prod)/len(df_main)*100:.2f}%)")

# Check unique agricultural cells vs trade rows
cells_hs4_ym = has_prod[["HS4", "Year", "Month"]].drop_duplicates()
print(f"  Unique (HS4, Year, Month) agricultural cells: {len(cells_hs4_ym):,}")
print(f"  Average repetition ratio: {len(has_prod) / len(cells_hs4_ym):.2f} trade rows per agricultural cell")

# Distribution of repetitions
rep_counts = has_prod.groupby(["HS4", "Year", "Month"]).size()
print(f"  Max repetition: {rep_counts.max()} trade rows for a single (HS4, Year, Month)")
print(f"  Median repetition: {rep_counts.median():.0f} trade rows")

# Breakdown of repetition by HS4
print("\n  Repetition by HS4 commodity:")
hs4_rep = has_prod.groupby("HS4").agg(
    Trade_Rows=("Country", "count"),
    Unique_YM=("Year", lambda x: len(has_prod.loc[x.index, ["Year", "Month"]].drop_duplicates())),
    Unique_Countries=("Country", "nunique")
).reset_index()
hs4_rep["Repetition_Ratio"] = (hs4_rep["Trade_Rows"] / hs4_rep["Unique_YM"]).round(1)
print(hs4_rep.sort_values("Trade_Rows", ascending=False).to_string(index=False))

# 6. Year-by-Year Sample & Independence Breakdown
print(f"\n7. YEAR-BY-YEAR DATA SPLIT AUDIT (TRADE ROWS vs INDEPENDENT AG CELLS):")
for yr in sorted(has_prod["Year"].unique()):
    sub = has_prod[has_prod["Year"] == yr]
    n_trade = len(sub)
    n_unique_ag = len(sub[["HS4", "Month"]].drop_duplicates())
    print(f"  Year {yr}: {n_trade:>6} trade rows | {n_unique_ag:>4} unique (HS4, Month) ag cells | Ratio: {n_trade/max(1,n_unique_ag):>5.1f}x")

# Check test set (Year 2023)
sub_2023 = has_prod[has_prod["Year"] == 2023]
print(f"\n  Test Set (Year >= 2023) Detail:")
print(f"    Trade rows: {len(sub_2023)}")
print(f"    Months present: {sorted(sub_2023['Month'].unique().tolist())}")
print(f"    Unique HS4s present: {sub_2023['HS4'].unique().tolist()}")
print(f"    Unique (HS4, Month) cells: {len(sub_2023[['HS4', 'Month']].drop_duplicates())}")

# 7. Production Risk Quantile Analysis
print(f"\n8. PRODUCTION RISK CLASS DISTRIBUTION AUDIT:")
print("  Quantile computation details:")
dev_all = has_prod["Production_Deviation_National"]
q25_all, q50_all, q75_all = dev_all.quantile([0.25, 0.50, 0.75])
print(f"    Trade-weighted quantiles (all years): q25={q25_all:.1f}, q50={q50_all:.1f}, q75={q75_all:.1f}")

# Quantiles on unique seasonal national data (not trade-replicated!)
dev_unique = national["Production_Deviation_National"].dropna()
q25_nat, q50_nat, q75_nat = dev_unique.quantile([0.25, 0.50, 0.75])
print(f"    Unique National quantiles (un-replicated): q25={q25_nat:.1f}, q50={q50_nat:.1f}, q75={q75_nat:.1f}")

# Quantiles on training-only data (<= 2021)
tr_prod = has_prod[has_prod["Year"] <= 2021]
q25_tr, q50_tr, q75_tr = tr_prod["Production_Deviation_National"].quantile([0.25, 0.50, 0.75])
print(f"    Training-only trade quantiles (<= 2021): q25={q25_tr:.1f}, q50={q50_tr:.1f}, q75={q75_tr:.1f}")

print("\n  Class distribution by Year in Merged Dataset:")
c_tab = pd.crosstab(has_prod["Year"], has_prod["Production_Risk"], margins=True)
print(c_tab)

print("\n  Class distribution in Unique National Seasonal Dataset (re-bucketed by national quantiles):")
def assign_nat_risk(d):
    if pd.isna(d): return np.nan
    if d <= q25_nat: return "Critical"
    elif d <= q50_nat: return "High"
    elif d <= q75_nat: return "Medium"
    else: return "Low"
national["Risk_National_Unique"] = national["Production_Deviation_National"].apply(assign_nat_risk)
c_tab_nat = pd.crosstab(national["Crop_Year"], national["Risk_National_Unique"], margins=True)
print(c_tab_nat)

print("\n" + "=" * 80)
print("AUDIT COMPLETE")
print("=" * 80)
