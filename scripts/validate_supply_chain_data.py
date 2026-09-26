"""
Drishti — Port Statistics Dataset Validation & Preprocessing
=============================================================
Validates and preprocesses the port statistics dataset:
  data/supply_chain/processed/port_statistics.csv

Known issues flagged at extraction time:
- Some 2023-24 rows picked up year numbers (2022, 2023) as cargo values.
- Kolkata DS / Haldia DC T2 rows from 2024-25 source PDF captured
  percentage shares rather than MT cargo values.
- T5 capacity utilisation for 2023-24 has some mis-parsed values.

This module:
1. Validates each relevant table type.
2. Flags suspect rows without silently repairing them.
3. Returns clean, trust-flagged subsets for downstream use.
4. Preserves source_table and source_page provenance on every row.

Usage
-----
from scripts.validate_supply_chain_data import (
    load_port_data, validate_port_data, get_trusted_port_cargo,
    get_trusted_commodity_cargo, get_trusted_container_traffic,
    get_trusted_state_cargo,
)
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
import json
import logging
import warnings

warnings.filterwarnings("ignore")

BASE_DIR = Path(__file__).resolve().parent.parent
PORT_CSV  = BASE_DIR / "data" / "supply_chain" / "processed" / "port_statistics.csv"
PROC_DIR  = BASE_DIR / "data" / "supply_chain" / "processed"

log = logging.getLogger(__name__)

# Realistic range thresholds for Major Port cargo in Million Tonnes
MT_PORT_MAX  = 900.0   # Deendayal total is highest (~855 MT), allow margin
MT_PORT_MIN  = 0.5     # sub-1 MT is suspicious for a major port
MT_SHARE_MAX = 100.0   # percentage share upper bound
MT_YEAR_LIKE = 2000.0  # values >= 2000 are likely a mis-parsed year

# Known share-row values from 2024-25 Kolkata DS sub-port (%, not MT)
KOLKATA_SHARE_VALUES = {2.63, 0.20, 2.06, 2.33, 0.68, 1.95,
                         7.30, 1.92, 6.05, 6.56, 2.12, 5.53}


def load_port_data(path: Optional[Path] = None) -> pd.DataFrame:
    """Load the port statistics CSV."""
    p = path or PORT_CSV
    if not p.exists():
        raise FileNotFoundError(f"Port statistics CSV not found: {p}")
    df = pd.read_csv(str(p), encoding="utf-8-sig")
    df.columns = [c.strip().lower() for c in df.columns]
    return df


def validate_port_data(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate port statistics dataset and return quality report.
    """
    issues: List[str] = []
    tables = df["traffic_type"].unique().tolist() if "traffic_type" in df.columns else []
    years  = sorted(df["year"].dropna().unique().tolist()) if "year" in df.columns else []

    # --- T2: Port-wise Cargo ---
    t2 = df[df["traffic_type"] == "overseas_coastal"].copy()
    t2_suspect = t2[
        (t2["total_mt"].notna()) & (t2["total_mt"] >= MT_YEAR_LIKE)
    ]
    if len(t2_suspect) > 0:
        issues.append(
            f"T2 Port Cargo: {len(t2_suspect)} rows have total_mt >= {MT_YEAR_LIKE} "
            "(likely year mis-parsed as cargo value). These rows are flagged UNRELIABLE."
        )

    # Rows from 2024-25 PDF for Kolkata/Haldia: overseas_mt is a percentage share
    t2_kol_haldia = t2[
        (t2["source_year_pdf"] == "2024-25") &
        (t2["port"].str.contains("Kolkata|Haldia", case=False, na=False)) &
        (t2["total_mt"].notna())
    ]
    if len(t2_kol_haldia) > 0 and any(t2_kol_haldia["overseas_mt"].isin(KOLKATA_SHARE_VALUES)):
        issues.append(
            "T2 Port Cargo: Kolkata DS / Haldia DC rows from 2024-25 PDF appear to contain "
            "percentage share values rather than MT cargo. Flagged UNRELIABLE."
        )

    # --- T3: Commodity Cargo ---
    t3 = df[(df["traffic_type"] == "commodity") & (df["port"] == "All Major Ports")].copy()
    t3_suspect = t3[t3["total_mt"].notna() & (t3["total_mt"] > 2500)]
    if len(t3_suspect) > 0:
        issues.append(
            f"T3 Commodity Cargo: {len(t3_suspect)} rows with total_mt > 2500 MT (likely noise from "
            "non-major port pages). Flagged UNRELIABLE."
        )

    # --- T4: Container ---
    t4 = df[df["traffic_type"] == "container"].copy()
    # No obvious parsing errors flagged for container data

    # --- T5: Capacity Utilisation ---
    t5 = df[df["traffic_type"] == "capacity"].copy()
    t5_suspect = t5[t5["utilisation_pct"].notna() & (t5["utilisation_pct"] > 100)]
    if len(t5_suspect) > 0:
        issues.append(
            f"T5 Capacity Utilisation: {len(t5_suspect)} rows with utilisation_pct > 100%. "
            "Flagged UNRELIABLE — likely mis-parsed values."
        )

    # --- T6: State-wise ---
    t6 = df[df["traffic_type"] == "state_total"].copy()
    # Check for serial-number contamination (major_port_mt looks like row numbers 1-10)
    t6_suspect = t6[
        t6["major_port_mt"].notna() &
        (t6["major_port_mt"] <= 15) &
        (t6["major_port_mt"] == t6["major_port_mt"].round(0))
    ]
    if len(t6_suspect) > 0:
        issues.append(
            f"T6 State Cargo: {len(t6_suspect)} rows where major_port_mt appears to be a serial "
            "number (1-15 integer). Flagged UNRELIABLE."
        )

    overall_status = "PASS" if not issues else "WARN"

    return {
        "n_rows": len(df),
        "traffic_types": tables,
        "year_range": years,
        "table_row_counts": df.groupby("traffic_type").size().to_dict() if "traffic_type" in df.columns else {},
        "t2_suspect_rows": len(t2_suspect),
        "t3_suspect_rows": len(t3_suspect),
        "t5_suspect_rows": len(t5_suspect),
        "t6_suspect_rows": len(t6_suspect),
        "issues": issues,
        "overall_status": overall_status,
    }


# ---------------------------------------------------------------------------
# Trusted subset getters
# ---------------------------------------------------------------------------

def get_trusted_port_cargo(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return T2 port-wise cargo rows that are NOT flagged as unreliable.
    Unreliable = total_mt >= 2000 (year mis-parsed) OR Kolkata/Haldia share rows.

    Preferred source: 2024-25 PDF (most recent, covers both 2023-24 and 2024-25).
    Falls back to 2023-24 PDF for ports missing in 2024-25 source.
    """
    t2 = df[df["traffic_type"] == "overseas_coastal"].copy()

    # Exclude rows with year-like cargo values
    t2 = t2[~(t2["total_mt"].notna() & (t2["total_mt"] >= MT_YEAR_LIKE))]

    # Exclude Kolkata DS / Haldia DC from 2024-25 PDF (share contamination)
    kolkata_mask = (
        (t2["source_year_pdf"] == "2024-25") &
        (t2["port"].str.contains("Kolkata|Haldia", case=False, na=False))
    )
    t2 = t2[~kolkata_mask]

    # Prefer 2024-25 PDF rows; supplement with 2023-24 for missing ports
    t2_24 = t2[t2["source_year_pdf"] == "2024-25"]
    ports_in_24 = set(t2_24["port"].unique())
    t2_23_extra = t2[(t2["source_year_pdf"] == "2023-24") & ~(t2["port"].isin(ports_in_24))]
    trusted = pd.concat([t2_24, t2_23_extra], ignore_index=True)

    trusted["data_quality"] = "TRUSTED"
    trusted["quality_note"]  = "[PORT DATA] Verified MT values; year-like and share-like rows excluded"
    return trusted.reset_index(drop=True)


def get_trusted_commodity_cargo(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return T3 commodity-wise cargo at Major Ports.
    Only 'All Major Ports' rows; exclude noise rows (total_mt > 2500 or < 0.1).
    Use 2024-25 source PDF for current data; 2023-24 for historical years not covered.
    """
    t3 = df[
        (df["traffic_type"] == "commodity") &
        (df["port"] == "All Major Ports")
    ].copy()

    # Exclude noise
    t3 = t3[t3["total_mt"].notna() & (t3["total_mt"] > 0.1) & (t3["total_mt"] <= 2500)]

    # Prefer 2024-25 source; use 2023-24 only for years not covered by 2024-25
    t3_24 = t3[t3["source_year_pdf"] == "2024-25"]
    years_in_24 = set(t3_24["year"].unique())
    t3_23_extra = t3[(t3["source_year_pdf"] == "2023-24") & ~(t3["year"].isin(years_in_24))]
    trusted = pd.concat([t3_24, t3_23_extra], ignore_index=True)

    trusted["data_quality"] = "TRUSTED"
    trusted["quality_note"]  = "[PORT DATA] Commodity MT from All Major Ports; noise rows excluded"
    return trusted.reset_index(drop=True)


def get_trusted_container_traffic(df: pd.DataFrame) -> pd.DataFrame:
    """Return T4 container traffic rows."""
    t4 = df[df["traffic_type"] == "container"].copy()
    t4 = t4[t4["container_tonnes_mt"].notna() | t4["container_teus_000"].notna()]
    t4["data_quality"] = "TRUSTED"
    t4["quality_note"]  = "[PORT DATA] Container traffic (MT and 000 TEUs)"
    return t4.reset_index(drop=True)


def get_trusted_state_cargo(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return T6 state-wise cargo rows that have valid major_port_mt values.
    Excludes rows where major_port_mt looks like a serial number (1-15 integer).
    """
    t6 = df[df["traffic_type"] == "state_total"].copy()
    t6 = t6[t6["major_port_mt"].notna()]
    # Filter out serial-number contamination
    t6 = t6[~(
        (t6["major_port_mt"] <= 15) &
        (t6["major_port_mt"] == t6["major_port_mt"].round(0))
    )]
    t6["data_quality"] = "TRUSTED"
    t6["quality_note"]  = "[PORT DATA] State-wise cargo; serial-number rows excluded"
    return t6.reset_index(drop=True)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)-5s %(message)s")
    print("=" * 60)
    print("PORT STATISTICS DATASET VALIDATION REPORT")
    print("=" * 60)

    df = load_port_data()
    report = validate_port_data(df)

    print(f"\nDataset: {PORT_CSV}")
    print(f"Total rows      : {report['n_rows']}")
    print(f"Year range      : {report['year_range']}")
    print(f"Traffic types   : {report['traffic_types']}")
    print(f"\nRows by type:")
    for k, v in report["table_row_counts"].items():
        print(f"  {k:<25}: {v}")

    print(f"\nSuspect rows:")
    print(f"  T2 Port Cargo suspicious    : {report['t2_suspect_rows']}")
    print(f"  T3 Commodity suspicious     : {report['t3_suspect_rows']}")
    print(f"  T5 Capacity suspicious      : {report['t5_suspect_rows']}")
    print(f"  T6 State cargo suspicious   : {report['t6_suspect_rows']}")

    print(f"\nOverall status  : {report['overall_status']}")
    if report["issues"]:
        print("\nIssues:")
        for i, iss in enumerate(report["issues"], 1):
            print(f"  {i}. {iss}")

    out = PROC_DIR / "validation_report_port.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\nReport saved: {out}")

    # Trusted subsets
    t2 = get_trusted_port_cargo(df)
    t3 = get_trusted_commodity_cargo(df)
    t4 = get_trusted_container_traffic(df)
    t6 = get_trusted_state_cargo(df)

    print(f"\nTrusted subsets:")
    print(f"  T2 Port Cargo  : {len(t2)} rows")
    print(f"  T3 Commodity   : {len(t3)} rows")
    print(f"  T4 Container   : {len(t4)} rows")
    print(f"  T6 State Cargo : {len(t6)} rows")


if __name__ == "__main__":
    main()
