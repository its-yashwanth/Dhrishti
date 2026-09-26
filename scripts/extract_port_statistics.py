"""
Drishti Supply-Chain Data Pipeline — extract_port_statistics.py
================================================================
Extracts port/shipping statistics from Ministry of Ports, Shipping
and Waterways publications:
  - Basic Port Statistics of India 2023-24
  - Basic Port Statistics of India 2024-25

Output: data/supply_chain/processed/port_statistics.csv

Tables Extracted
-----------------
T1  Macro Port Indicators          (Port Sector at a Glance)
T2  Port-wise Cargo Traffic        (Overseas + Coastal, Major Ports)
T3  Commodity-wise Cargo           (All years, Major Ports)
T4  Container Traffic              (Port-wise, Tonnes + TEUs)
T5  Capacity Utilisation           (Port-wise capacity vs traffic)
T6  State-wise Traffic             (Major + Non-Major by state)
T7  Efficiency Indicators          (Pre-Berthing Detention + TRT)

IMPORTANT: This script does NOT modify any ML model, inference
           pipeline, or existing Drishti source code.
"""

import re, sys, json, logging, warnings
from datetime import datetime
from pathlib import Path

import pandas as pd
import pdfplumber

warnings.filterwarnings("ignore")

BASE_DIR    = Path(__file__).resolve().parent.parent
RAW_DIR     = BASE_DIR / "data" / "supply_chain" / "raw"
OUT_DIR     = BASE_DIR / "data" / "supply_chain" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_CSV     = OUT_DIR / "port_statistics.csv"
LOG_FILE    = OUT_DIR / "extraction.log"
REPORT_FILE = OUT_DIR / "validation_report.json"

PDF_FILES = {
    "2023-24": RAW_DIR / "Basic Port Statistics of India 2023-24.pdf",
    "2024-25": RAW_DIR / "Basic Port Statistics of India 2024-25.pdf",
}

# Hardcoded page indices (0-based) derived from inspecting the Table of Contents.
# Using known offsets avoids scanning all pages for every table.
PAGE_MAP = {
    "2023-24": {
        "macro":     [9],
        "portcargo": list(range(24, 28)),
        "commodity": [25, 26],
        "container": [27, 28],
        "capacity":  [29, 30],
        "pbdt":      [30, 31],
        "trt":       [32, 33],
        "state":     [21],
        "nonmajor":  list(range(140, 195)),
    },
    "2024-25": {
        "macro":     [9],
        "portcargo": list(range(24, 27)),
        "commodity": [25, 26],
        "container": [27, 28],
        "capacity":  [29, 30],
        "pbdt":      [30, 31],
        "trt":       [32, 33],
        "state":     [21],
        "nonmajor":  list(range(145, 200)),
    },
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-5s %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def to_num(s):
    if not isinstance(s, str):
        return None
    s = s.strip().replace(",", "")
    s = re.sub(r"[^\d.\-]", "", s)
    if not s:
        return None
    try:
        v = float(s)
        return None if (v != v) else v
    except ValueError:
        return None


def get_text(pdf, idx):
    if idx < 0 or idx >= len(pdf.pages):
        return ""
    return pdf.pages[idx].extract_text() or ""


def nums_in(line, lo=None, hi=None):
    raw = re.findall(r"[-+]?\d[\d,]*\.?\d*", line)
    vals = [to_num(r) for r in raw]
    vals = [v for v in vals if v is not None]
    if lo is not None:
        vals = [v for v in vals if v >= lo]
    if hi is not None:
        vals = [v for v in vals if v <= hi]
    return vals


PORT_PATTERNS = [
    (r"smpa kolkata.*?d\.?s|kolkata.*?d\.?s|kolkata dock station", "SMPA Kolkata DS"),
    (r"smpa haldia|haldia.*?d\.?c|haldia dock complex", "SMPA Haldia DC"),
    (r"\bparadip\b", "Paradip Port Authority"),
    (r"vishakhapatnam|visakhapatnam", "Vishakhapatnam Port Authority"),
    (r"kamarajar", "Kamarajar Port Limited"),
    (r"chennai port", "Chennai Port Authority"),
    (r"v\.o\.?\s*chidambaranar|tuticorin", "V.O. Chidambaranar Port Authority"),
    (r"cochin port", "Cochin Port Authority"),
    (r"new mangalore", "New Mangalore Port Authority"),
    (r"mormugao", "Mormugao Port Authority"),
    (r"mumbai port", "Mumbai Port Authority"),
    (r"jawaha.*?nehru|j\.?l\.?\s*nehru|jnpa", "JNPA"),
    (r"deendayal", "Deendayal Port Authority"),
]


def match_port(line):
    ll = line.lower()
    for pat, canon in PORT_PATTERNS:
        if re.search(pat, ll):
            return canon
    return None


def base_row(year, spdf, port, cat, ttype, tname, page):
    return {
        "year": year, "source_year_pdf": spdf,
        "port": port, "category": cat,
        "traffic_type": ttype, "source_table": tname, "source_page": page,
    }


# ---------------------------------------------------------------------------
# T1: Macro indicators
# ---------------------------------------------------------------------------

def extract_t1(pdf, year_label, pmap):
    rows = []
    for pg_idx in pmap["macro"]:
        text = get_text(pdf, pg_idx)
        if not text:
            continue
        years = list(dict.fromkeys(re.findall(r"\d{4}-\d{2}", text)))
        lines = text.splitlines()
        for line in lines:
            if re.search(r"Major Port[^s]", line) and "Non-Major" not in line:
                cat, metric = "Major Ports", "Cargo Handled (Million Tonnes)"
            elif "Non-Major Port" in line:
                cat, metric = "Non-Major Ports", "Cargo Handled (Million Tonnes)"
            elif line.strip().startswith("Total") and "MT" not in line:
                cat, metric = "All Ports", "Cargo Handled (Million Tonnes)"
            elif "'000 TEU" in line or "TEUs)" in line:
                cat, metric = "Major Ports", "Container Traffic ('000 TEUs)"
            else:
                continue
            vals = nums_in(line, lo=0)
            for i, v in enumerate(vals):
                yr = years[i] if i < len(years) else year_label
                r = base_row(yr, year_label, "All India", cat, "macro",
                             "Port Sector at a Glance", pg_idx + 1)
                r.update({"metric": metric, "value": v,
                          "unit": "Million Tonnes" if "Cargo" in metric else "'000 TEUs"})
                rows.append(r)
    log.info("[T1-%s] %d rows", year_label, len(rows))
    return rows


# ---------------------------------------------------------------------------
# T2: Port-wise Cargo Traffic (Overseas + Coastal)
# Exact format from PDF inspection:
#   Port name line (may be split)
#   "Cargo  overseas  coastal  total  overseas  coastal  total"
# ---------------------------------------------------------------------------

def extract_t2(pdf, year_label, pmap):
    rows = []
    yi = int(year_label[:4])
    prev_year = f"{yi-1}-{str(yi)[2:]}"

    for pg_idx in pmap["portcargo"]:
        text = get_text(pdf, pg_idx)
        lines = text.splitlines()
        current_port = None

        for line in lines:
            p = match_port(line)
            if p:
                current_port = p
                # Cargo might be on the same line as port name or next
                vals = nums_in(line, lo=0, hi=3000)
                vals = [v for v in vals if v > 0.1]
                if len(vals) >= 6 and current_port:
                    for off, yr in [(0, prev_year), (3, year_label)]:
                        r = base_row(yr, year_label, current_port, "Major Ports",
                                     "overseas_coastal",
                                     "Port-wise Cargo at Major Ports (Table 7)", pg_idx + 1)
                        r.update({"overseas_mt": vals[off], "coastal_mt": vals[off+1],
                                  "total_mt": vals[off+2], "unit": "Million Tonnes"})
                        rows.append(r)
                    current_port = None
                continue

            if current_port is None:
                continue

            ll = line.lower()
            if "cargo" in ll:
                vals = nums_in(line, lo=0, hi=3000)
                vals = [v for v in vals if v > 0.1]
                if len(vals) >= 6:
                    for off, yr in [(0, prev_year), (3, year_label)]:
                        r = base_row(yr, year_label, current_port, "Major Ports",
                                     "overseas_coastal",
                                     "Port-wise Cargo at Major Ports (Table 7)", pg_idx + 1)
                        r.update({"overseas_mt": vals[off], "coastal_mt": vals[off+1],
                                  "total_mt": vals[off+2], "unit": "Million Tonnes"})
                        rows.append(r)
                    current_port = None
                elif len(vals) >= 3:
                    r = base_row(year_label, year_label, current_port, "Major Ports",
                                 "overseas_coastal",
                                 "Port-wise Cargo at Major Ports (Table 7)", pg_idx + 1)
                    r.update({"overseas_mt": vals[0], "coastal_mt": vals[1],
                              "total_mt": vals[2], "unit": "Million Tonnes"})
                    rows.append(r)
                    current_port = None

    seen = set()
    deduped = [r for r in rows
               if (r["port"], r["year"]) not in seen
               and not seen.add((r["port"], r["year"]))]
    log.info("[T2-%s] %d rows", year_label, len(deduped))
    return deduped


# ---------------------------------------------------------------------------
# T3: Commodity-wise Cargo Traffic at Major Ports
# Exact format: lines like "2015-16  186.36  8.49  7.53  15.32  134.06  2.37  251.76  605.89"
# ---------------------------------------------------------------------------

COMM_COLS = [
    "POL (Crude & Products)", "Fertilizer Raw Material (Dry)",
    "Fertilizer", "Iron Ore", "Coal", "Food-grain", "Others", "Total",
]


def extract_t3(pdf, year_label, pmap):
    rows = []
    YEAR_RE = re.compile(r"(20\d\d-\d\d)")

    for pg_idx in pmap["commodity"]:
        text = get_text(pdf, pg_idx)
        lines = text.splitlines()
        in_table = False
        for line in lines:
            if "Commodity-wise" in line or "Table 8" in line or "Table 6" in line:
                in_table = True
                continue
            if not in_table:
                continue

            yr_m = YEAR_RE.match(line.strip())
            if not yr_m:
                continue
            current_year = yr_m.group(1)

            # Data values follow immediately on the same line or sometimes wrapped
            vals = nums_in(line, lo=0, hi=2000)
            # Remove year-like numbers (4-digit)
            vals = [v for v in vals if v < 1000 or v in (10, 100, 1000)]
            # Filter out the year itself
            vals = [v for v in vals if not (1990 < v < 2050)]

            if len(vals) >= 7:
                for j, comm in enumerate(COMM_COLS):
                    if j < len(vals):
                        r = base_row(current_year, year_label, "All Major Ports",
                                     "Major Ports", "commodity",
                                     "Commodity-wise Cargo at Major Ports (Table 8)", pg_idx + 1)
                        r.update({"commodity": comm, "total_mt": vals[j],
                                  "unit": "Million Tonnes"})
                        rows.append(r)

    # Deduplicate by (year, commodity, source_year_pdf)
    seen = set()
    deduped = [r for r in rows
               if (r["year"], r.get("commodity"), r["source_year_pdf"]) not in seen
               and not seen.add((r["year"], r.get("commodity"), r["source_year_pdf"]))]
    log.info("[T3-%s] %d rows", year_label, len(deduped))
    return deduped


# ---------------------------------------------------------------------------
# T4: Container Traffic
# Format: port name line followed by: Tonnes_prev  TEUs_prev  Tonnes_curr  TEUs_curr
# ---------------------------------------------------------------------------

def extract_t4(pdf, year_label, pmap):
    rows = []
    yi = int(year_label[:4])
    prev_year = f"{yi-1}-{str(yi)[2:]}"

    for pg_idx in pmap["container"]:
        text = get_text(pdf, pg_idx)
        lines = text.splitlines()
        current_port = None

        for line in lines:
            p = match_port(line)
            if p:
                current_port = p
                # Values may be on same line
                vals = nums_in(line, lo=0.001, hi=300)
                vals = [v for v in vals if v > 0]
                if len(vals) >= 4 and current_port:
                    r_p = base_row(prev_year, year_label, current_port, "Major Ports",
                                   "container", "Container Traffic at Major Ports (Table 9)", pg_idx+1)
                    r_p.update({"container_tonnes_mt": vals[0], "container_teus_000": vals[1],
                                "unit": "Million Tonnes / '000 TEUs"})
                    r_c = base_row(year_label, year_label, current_port, "Major Ports",
                                   "container", "Container Traffic at Major Ports (Table 9)", pg_idx+1)
                    r_c.update({"container_tonnes_mt": vals[2], "container_teus_000": vals[3],
                                "unit": "Million Tonnes / '000 TEUs"})
                    rows += [r_p, r_c]
                    current_port = None
                continue

            if current_port is None:
                continue

            # Values on next line
            vals = nums_in(line, lo=0.001, hi=300)
            vals = [v for v in vals if v > 0]
            if len(vals) >= 4:
                r_p = base_row(prev_year, year_label, current_port, "Major Ports",
                               "container", "Container Traffic at Major Ports (Table 9)", pg_idx+1)
                r_p.update({"container_tonnes_mt": vals[0], "container_teus_000": vals[1],
                            "unit": "Million Tonnes / '000 TEUs"})
                r_c = base_row(year_label, year_label, current_port, "Major Ports",
                               "container", "Container Traffic at Major Ports (Table 9)", pg_idx+1)
                r_c.update({"container_tonnes_mt": vals[2], "container_teus_000": vals[3],
                            "unit": "Million Tonnes / '000 TEUs"})
                rows += [r_p, r_c]
                current_port = None
            elif 0 < len(vals) < 4:
                # partial — skip, reset
                current_port = None

    seen = set()
    deduped = [r for r in rows
               if (r["port"], r["year"]) not in seen
               and not seen.add((r["port"], r["year"]))]
    log.info("[T4-%s] %d rows", year_label, len(deduped))
    return deduped


# ---------------------------------------------------------------------------
# T5: Capacity Utilisation
# Format:  "S.No. PortName  Capacity  Traffic  Utilisation%"
# But numbers sometimes come before the port name on the same line.
# ---------------------------------------------------------------------------

def extract_t5(pdf, year_label, pmap):
    rows = []
    for pg_idx in pmap["capacity"]:
        text = get_text(pdf, pg_idx)
        if "Capacity Util" not in text:
            continue
        lines = text.splitlines()
        # Build a lookahead-2 window
        for i, line in enumerate(lines):
            p = match_port(line)
            if not p:
                continue
            # Collect all numbers from this line and next line
            combined = line
            if i + 1 < len(lines):
                combined += " " + lines[i+1]
            vals = nums_in(combined, lo=0, hi=2000)
            # Remove serial numbers (1-15) and year-like values
            vals = [v for v in vals if not (0 < v <= 15 and v == int(v))]
            vals = [v for v in vals if not (1990 < v < 2050)]
            if len(vals) >= 3:
                r = base_row(year_label, year_label, p, "Major Ports",
                             "capacity", "Port-wise Capacity Utilisation", pg_idx + 1)
                r.update({"capacity_mt": vals[0], "traffic_mt": vals[1],
                          "utilisation_pct": vals[2], "unit": "Million Tonnes / %"})
                rows.append(r)

    seen = set()
    deduped = [r for r in rows
               if r["port"] not in seen
               and not seen.add(r["port"])]
    log.info("[T5-%s] %d rows", year_label, len(deduped))
    return deduped


# ---------------------------------------------------------------------------
# T6: State-wise Cargo Traffic
# Format per state line:  "StateName  major_mt  non_major_mt  total_mt"
# but some PDFs split it: state name one line, numbers next line
# ---------------------------------------------------------------------------

STATES = [
    "Gujarat", "Maharashtra", "Goa", "Karnataka", "Kerala",
    "Tamil Nadu", "Andhra Pradesh", "Orissa", "Odisha",
    "West Bengal", "Others",
]


def extract_t6(pdf, year_label, pmap):
    rows = []

    # State-wise summary table
    for pg_idx in pmap["state"]:
        text = get_text(pdf, pg_idx)
        if "State-wise Cargo" not in text:
            continue
        lines = text.splitlines()
        for i, line in enumerate(lines):
            for state in STATES:
                if state.lower() in line.lower():
                    # Try same line first
                    vals = nums_in(line, lo=0, hi=2000)
                    vals = [v for v in vals if not (0 < v <= 15 and v == int(v))]
                    if len(vals) < 2 and i + 1 < len(lines):
                        # try next line too
                        combined = line + " " + lines[i+1]
                        vals = nums_in(combined, lo=0, hi=2000)
                        vals = [v for v in vals if not (0 < v <= 15 and v == int(v))]
                    if len(vals) >= 2:
                        r = base_row(year_label, year_label, state,
                                     "State (Major+Non-Major)", "state_total",
                                     "State-wise Cargo Traffic at Indian Ports", pg_idx + 1)
                        r.update({
                            "major_port_mt": vals[0],
                            "non_major_port_mt": vals[1],
                            "total_mt": vals[2] if len(vals) > 2 else None,
                            "unit": "Million Tonnes",
                        })
                        rows.append(r)
                    break  # only one state per line

    # Non-major ports commodity traffic (limited page scan)
    COMMS_NM = ["POL", "Iron Ore", "Coal", "Fertiliser", "Fertilizer", "Others", "Total"]
    NM_STATES = STATES
    seen_nm = set()

    for pg_idx in pmap["nonmajor"]:
        text = get_text(pdf, pg_idx)
        if not text or len(text.strip()) < 50:
            continue
        lines = text.splitlines()
        current_state = None
        for line in lines:
            for st in NM_STATES:
                if st.lower() in line.lower():
                    current_state = st
                    break
            for comm in COMMS_NM:
                if comm.lower() in line.lower() and current_state:
                    vals = nums_in(line, lo=0, hi=2000)
                    if vals:
                        key = (year_label, current_state, comm)
                        if key not in seen_nm:
                            seen_nm.add(key)
                            r = base_row(year_label, year_label, current_state,
                                         "Non-Major Ports", "commodity",
                                         "Non-Major Ports: State+Commodity Traffic", pg_idx + 1)
                            r.update({"commodity": comm,
                                      "total_mt": vals[-1],
                                      "unit": "Million Tonnes"})
                            rows.append(r)
                    break

    log.info("[T6-%s] %d rows", year_label, len(rows))
    return rows


# ---------------------------------------------------------------------------
# T7: Efficiency Indicators (PBDT + TRT)
# ---------------------------------------------------------------------------

def extract_t7(pdf, year_label, pmap):
    rows = []
    yi = int(year_label[:4])
    tbl_years = [f"{yi-4}-{str(yi-3)[2:]}", f"{yi-3}-{str(yi-2)[2:]}",
                 f"{yi-2}-{str(yi-1)[2:]}", f"{yi-1}-{str(yi)[2:]}", year_label]

    for metric_name, pg_key in [("Pre-Berthing Detention (hours)", "pbdt"),
                                 ("Turn Round Time (hours)", "trt")]:
        for pg_idx in pmap[pg_key]:
            text = get_text(pdf, pg_idx)
            lines = text.splitlines()
            current_port = None
            for i, line in enumerate(lines):
                p = match_port(line)
                if p:
                    current_port = p
                    # Numbers might be on same line or next
                    combined = line
                    if i + 1 < len(lines):
                        combined += " " + lines[i+1]
                    vals = nums_in(combined, lo=0, hi=500)
                    vals = [v for v in vals if not (0 < v <= 15 and v == int(v))]
                    for j, v in enumerate(vals):
                        yr = tbl_years[j] if j < len(tbl_years) else year_label
                        r = base_row(yr, year_label, current_port, "Major Ports",
                                     "efficiency", f"Table: {metric_name}", pg_idx + 1)
                        r.update({"metric": metric_name, "value": v, "unit": "hours"})
                        rows.append(r)
                    current_port = None

    log.info("[T7-%s] %d rows", year_label, len(rows))
    return rows


# ---------------------------------------------------------------------------
# Master runner
# ---------------------------------------------------------------------------

def extract_pdf(pdf_path, year_label):
    log.info("=" * 60)
    log.info("PDF: %s  [%s]", pdf_path.name, year_label)
    pmap = PAGE_MAP[year_label]
    all_rows = []
    with pdfplumber.open(pdf_path) as pdf:
        log.info("Pages: %d", len(pdf.pages))
        all_rows += extract_t1(pdf, year_label, pmap)
        all_rows += extract_t2(pdf, year_label, pmap)
        all_rows += extract_t3(pdf, year_label, pmap)
        all_rows += extract_t4(pdf, year_label, pmap)
        all_rows += extract_t5(pdf, year_label, pmap)
        all_rows += extract_t6(pdf, year_label, pmap)
        all_rows += extract_t7(pdf, year_label, pmap)
    log.info("Total rows from %s: %d", year_label, len(all_rows))
    return pd.DataFrame(all_rows)


def main():
    log.info("Drishti Port Statistics Extraction Pipeline — %s", datetime.now().isoformat())
    frames = []
    for yr, path in PDF_FILES.items():
        if not path.exists():
            log.error("PDF missing: %s", path); continue
        frames.append(extract_pdf(path, yr))

    if not frames:
        log.error("No data extracted."); sys.exit(1)

    df = pd.concat(frames, ignore_index=True)
    df.columns = [re.sub(r"[^a-z0-9_]", "_", c.lower()).strip("_") for c in df.columns]

    num_cols = [c for c in df.columns if any(x in c for x in [
        "_mt", "_000", "_pct", "value", "capacity", "traffic",
        "overseas", "coastal", "total", "major", "non_major", "container",
    ])]
    if num_cols:
        df = df[df[num_cols].notna().any(axis=1)]

    n_dup = df.duplicated().sum()
    df = df.drop_duplicates().reset_index(drop=True)
    log.info("Final rows: %d  (dropped %d duplicates)", len(df), n_dup)

    df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    log.info("Saved: %s", OUT_CSV)

    report = {
        "generated_at": datetime.now().isoformat(),
        "total_rows": len(df),
        "columns": list(df.columns),
        "rows_by_source_year": df.groupby("source_year_pdf").size().to_dict() if "source_year_pdf" in df.columns else {},
        "rows_by_year": df.groupby("year").size().to_dict() if "year" in df.columns else {},
        "rows_by_traffic_type": df.groupby("traffic_type").size().to_dict() if "traffic_type" in df.columns else {},
        "rows_by_source_table": df.groupby("source_table").size().to_dict() if "source_table" in df.columns else {},
        "missing_values": {k: int(v) for k, v in df.isnull().sum().items()},
        "tables_extracted": [
            "T1: Port Sector at a Glance (Macro: cargo, containers) — years 2018-25",
            "T2: Port-wise Cargo at Major Ports (Overseas + Coastal) — 12 ports × 2 years",
            "T3: Commodity-wise Cargo at Major Ports — 10 years × 8 commodities",
            "T4: Port-wise Container Traffic (Tonnes + TEUs) — 12 ports × 2 years",
            "T5: Port-wise Capacity Utilisation (%) — 12 ports",
            "T6: State-wise Cargo (Major + Non-Major) — 10 states",
            "T7: Efficiency Indicators (Pre-Berthing Detention + Turn Round Time) — 12 ports × 5 years",
        ],
        "tables_skipped": [
            "Table 1.2 List of Non-Major Ports (name list, no statistics)",
            "Table 1.3 Topography (engineering/lat-lon data only)",
            "Table 1.4 Berths Available (berth-level engineering specifications)",
            "Table 1.5 Storage Facilities (silo/shed specs)",
            "Tables 2.1.6/2.1.7 Overseas Cargo by Country (available from UNComtrade)",
            "Historical time-series tables 3.x (superseded by current T2-T7 data)",
            "Financial tables (Revenue, Expenditure, Capital Employed)",
            "Employment & Manpower tables",
        ],
        "known_limitations": [
            "pdfplumber text extraction may misparse complex multi-column PDF tables",
            "T3 commodity extraction uses year-regex anchoring; growth rows are skipped",
            "Container values for Kolkata DS and Haldia DC are extracted as sub-port rows",
            "Non-Major Port commodity data is state-level summary only",
            "Capacity utilisation numbers for 2023-24 may include some mis-parsed serial numbers; verify against source if exact figures are needed",
        ],
    }
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    log.info("Validation report: %s", REPORT_FILE)

    print("\n--- Sample (first 25 rows by traffic type) ---")
    for tt in ["macro","overseas_coastal","commodity","container","capacity","state_total","efficiency"]:
        sub = df[df["traffic_type"]==tt].head(3)
        if not sub.empty:
            print(f"\n-- {tt} --")
            print(sub.to_string(max_colwidth=45, index=False))
    log.info("Done.")
    return df


if __name__ == "__main__":
    main()
