"""
Drishti Agent: Supply-Chain Agent
==================================
Contextual/rule-based agent that maps a geopolitical trade shock to
Indian port logistics context using the Ministry of Ports, Shipping
and Waterways dataset.

Purpose
-------
Given:  event_country, commodity, hs4, trade_type, shock direction,
        shock intensity, trade share
Return: structured supply-chain context including:
  - Relevant Indian Major Ports
  - Port cargo dependency (overseas + coastal)
  - Commodity cargo context at Major Ports
  - Container traffic dependency
  - State-level logistics concentration
  - Potential bottleneck / dependency indicators
  - Provenance for every dataset-derived value

Important caveats
-----------------
- Does NOT claim causal responsibility.
- Uses hedging language: "indicates exposure", "suggests dependency",
  "potential bottleneck", "logistics concentration", "observed traffic".
- Does NOT invent statistics.
- Returns "Insufficient data" when the dataset has no matching record.
- Provenance tags follow Drishti convention:
    [PORT DATA]        — dataset-derived values
    [RULE-BASED OUTPUT]— deterministic computation
    [USER / CLI PARAMETER] — user inputs

Trade direction convention
--------------------------
  Export: India ships commodity → foreign country
          ∴ relevant ports are those that handle India's outbound cargo
  Import: foreign country ships commodity → India
          ∴ relevant ports are those that receive India's inbound cargo
"""

import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from scripts.validate_supply_chain_data import (
    load_port_data,
    validate_port_data,
    get_trusted_port_cargo,
    get_trusted_commodity_cargo,
    get_trusted_container_traffic,
    get_trusted_state_cargo,
)

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Port ↔ Commodity keyword mapping
# Used to identify which ports typically handle specific commodities.
# Based on publicly known port specialisations, not fabricated.
# ---------------------------------------------------------------------------
PORT_COMMODITY_AFFINITY: Dict[str, List[str]] = {
    "Paradip Port Authority":                  ["coal", "fertilizer", "iron ore", "food grain", "rice", "wheat"],
    "Vishakhapatnam Port Authority":           ["coal", "iron ore", "fertilizer", "general cargo"],
    "Kamarajar Port Limited":                  ["coal", "iron ore"],
    "Chennai Port Authority":                  ["container", "rice", "wheat", "general cargo", "automobile"],
    "V.O. Chidambaranar Port Authority":       ["container", "rice", "wheat", "general cargo", "tuticorin"],
    "Cochin Port Authority":                   ["container", "spices", "pepper", "general cargo"],
    "New Mangalore Port Authority":            ["coal", "fertilizer", "general cargo"],
    "Mormugao Port Authority":                 ["iron ore", "coal", "fertilizer"],
    "JNPA":                                    ["container", "general cargo", "rice", "wheat"],
    "Mumbai Port Authority":                   ["container", "general cargo", "spices", "sugar"],
    "Deendayal Port Authority":                ["container", "general cargo", "rice", "wheat", "fertilizer"],
    "SMPA Kolkata DS":                         ["general cargo", "rice", "wheat", "jute"],
    "SMPA Haldia DC":                          ["coal", "fertilizer", "general cargo", "rice", "wheat"],
}

# Commodity → port commodity category alignment
COMMODITY_TO_PORT_CATEGORY: Dict[str, str] = {
    "rice":      "food grain",
    "wheat":     "food grain",
    "maize":     "food grain",
    "soybean":   "fertilizer",     # also general cargo
    "soyabean":  "fertilizer",
    "groundnut": "general cargo",
    "cotton":    "general cargo",
    "sugar":     "general cargo",
    "sugarcane": "general cargo",
    "coal":      "coal",
    "iron ore":  "iron ore",
    "fertilizer": "fertilizer",
    "pepper":    "general cargo",
    "spices":    "general cargo",
    "turmeric":  "general cargo",
    "ginger":    "general cargo",
    "onion":     "general cargo",
    "potato":    "general cargo",
    "palm oil":  "general cargo",
    "pulses":    "food grain",
}


class SupplyChainAgent:
    """
    Rule-based / contextual supply-chain analysis agent.
    Loaded once per process; data is cached in memory.
    """

    _data_cache: Optional[pd.DataFrame] = None

    def __init__(self):
        self._load_data()

    def _load_data(self):
        """Load and cache port data (with trusted filtering)."""
        if SupplyChainAgent._data_cache is None:
            try:
                raw = load_port_data()
                SupplyChainAgent._data_cache = raw
                log.info("SupplyChainAgent: port data loaded (%d rows)", len(raw))
            except FileNotFoundError as e:
                log.error("SupplyChainAgent: %s", e)
                SupplyChainAgent._data_cache = pd.DataFrame()

    @property
    def _raw(self) -> pd.DataFrame:
        return SupplyChainAgent._data_cache if SupplyChainAgent._data_cache is not None else pd.DataFrame()

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def analyse(
        self,
        commodity: str,
        hs4: int,
        trade_type: str,
        event_country: str,
        shock_direction: str = "supply_contraction",
        shock_intensity: float = 1.0,
        trade_share: float = 5.0,
        ml_predictions: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Run supply-chain analysis for a given commodity + trade shock.

        Parameters
        ----------
        commodity       : Commodity name (e.g. 'Wheat', 'Rice', 'Palm Oil')
        hs4             : 4-digit HS code
        trade_type      : 'Import' or 'Export'
        event_country   : Foreign partner country
        shock_direction : Canonical shock type from EventIntelligenceAgent
        shock_intensity : Intensity index
        trade_share     : Partner trade share %
        ml_predictions  : Optional ML cascade predictions (for context only)

        Returns
        -------
        dict following the Drishti supply_chain_analysis schema
        """
        if self._raw.empty:
            return self._insufficient_data(commodity, hs4, trade_type, event_country,
                                           reason="Port statistics dataset not available.")

        # Compute effective shock
        effective_shock = shock_intensity * (trade_share / 100.0)

        # Determine trade direction label
        if trade_type.strip().capitalize() == "Export":
            trade_direction_label = f"India's exports to {event_country}"
            exposure_type = "export_exposure"
        else:
            trade_direction_label = f"India's imports from {event_country}"
            exposure_type = "import_exposure"

        # Get trusted sub-tables
        t2 = get_trusted_port_cargo(self._raw)
        t3 = get_trusted_commodity_cargo(self._raw)
        t4 = get_trusted_container_traffic(self._raw)
        t6 = get_trusted_state_cargo(self._raw)

        # --- Port cargo analysis (T2) ---
        port_cargo_rows  = self._get_latest_port_cargo(t2)
        relevant_ports   = self._identify_relevant_ports(commodity, hs4)
        port_dependency  = self._compute_port_dependency(port_cargo_rows, relevant_ports)

        # --- Commodity cargo context (T3) ---
        commodity_context = self._get_commodity_context(t3, commodity, hs4)

        # --- Container dependency (T4) ---
        container_dep = self._get_container_dependency(t4, commodity, hs4)

        # --- State logistics context (T6) ---
        state_context = self._get_state_logistics(t6)

        # --- Bottleneck indicators ---
        bottlenecks = self._identify_bottlenecks(
            port_cargo_rows, relevant_ports, trade_type, effective_shock
        )

        # --- Risk indicators ---
        risk_indicators = self._compute_risk_indicators(
            trade_share, effective_shock, trade_type,
            port_dependency, commodity_context, ml_predictions
        )

        # --- Limitations ---
        limitations = self._standard_limitations(commodity, hs4)

        # --- Provenance ---
        provenance = self._build_provenance(t2, t3, t4, t6)

        return {
            "supply_chain_analysis": {
                "commodity": commodity,
                "hs4": hs4,
                "trade_type": trade_type,
                "affected_country": event_country,
                "trade_direction": trade_direction_label,
                "exposure_type": exposure_type,
                "effective_shock": round(effective_shock, 4),
                "relevant_ports": relevant_ports,
                "port_cargo_context": port_dependency,
                "commodity_port_context": commodity_context,
                "container_dependency": container_dep,
                "state_logistics_context": state_context,
                "potential_bottlenecks": bottlenecks,
                "risk_indicators": risk_indicators,
                "limitations": limitations,
                "provenance_tags": {
                    "port_cargo": "[PORT DATA] source: Port-wise Cargo at Major Ports",
                    "commodity_cargo": "[PORT DATA] source: Commodity-wise Cargo at Major Ports",
                    "container": "[PORT DATA] source: Container Traffic at Major Ports",
                    "state": "[PORT DATA] source: State-wise Cargo Traffic at Indian Ports",
                    "effective_shock": "[RULE-BASED OUTPUT]",
                    "risk_indicators": "[RULE-BASED OUTPUT]",
                    "trade_direction": "[USER / CLI PARAMETER]",
                },
            },
            "provenance": provenance,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_latest_port_cargo(self, t2: pd.DataFrame) -> pd.DataFrame:
        """Get most recent year port cargo rows from trusted T2."""
        if t2.empty:
            return t2
        # Prefer 2024-25 rows, then 2023-24
        latest_year = sorted(t2["year"].unique(), reverse=True)
        for yr in latest_year:
            sub = t2[t2["year"] == yr]
            if len(sub) >= 5:
                return sub
        return t2

    def _identify_relevant_ports(self, commodity: str, hs4: int) -> List[Dict[str, Any]]:
        """
        Identify ports with known affinity to this commodity.
        Returns list of port dicts with reasoning.
        """
        c_lower = commodity.strip().lower()
        port_cat = COMMODITY_TO_PORT_CATEGORY.get(c_lower, "general cargo")

        results = []
        for port, affinities in PORT_COMMODITY_AFFINITY.items():
            matched = [a for a in affinities
                       if c_lower in a.lower() or a.lower() in c_lower
                       or port_cat in a.lower()]
            if matched:
                results.append({
                    "port": port,
                    "affinity_basis": matched,
                    "note": f"Port has known handling affinity for {', '.join(matched)} cargo.",
                    "provenance": "[PORT DATA] Based on known port specialisation",
                })

        if not results:
            results.append({
                "port": "Unable to determine specific port",
                "affinity_basis": [],
                "note": f"No specific port affinity identified for commodity '{commodity}'. "
                        "General cargo ports (JNPA, Deendayal, Chennai) handle residual categories.",
                "provenance": "[RULE-BASED OUTPUT]",
            })
        return results

    def _compute_port_dependency(
        self, port_cargo: pd.DataFrame, relevant_ports: List[Dict]
    ) -> List[Dict[str, Any]]:
        """
        For each relevant port, attach actual traffic data (if available).
        """
        if port_cargo.empty:
            return [{"note": "Insufficient data", "provenance": "[PORT DATA]"}]

        total_all = port_cargo["total_mt"].sum()
        results = []
        relevant_names = [p["port"] for p in relevant_ports if p.get("port") != "Unable to determine specific port"]

        for port_name in relevant_names:
            port_row = port_cargo[port_cargo["port"].str.contains(port_name[:12], case=False, na=False)]
            if port_row.empty:
                results.append({
                    "port": port_name,
                    "year": "N/A",
                    "total_mt": None,
                    "overseas_mt": None,
                    "coastal_mt": None,
                    "share_of_all_ports_pct": None,
                    "note": f"No port cargo data available for {port_name} in trusted dataset.",
                    "provenance": "[PORT DATA] Not available",
                })
                continue

            row = port_row.iloc[0]
            total_mt = float(row["total_mt"]) if pd.notna(row["total_mt"]) else None
            overseas  = float(row["overseas_mt"]) if pd.notna(row.get("overseas_mt")) else None
            coastal   = float(row["coastal_mt"])  if pd.notna(row.get("coastal_mt"))  else None
            share_pct = round(100.0 * total_mt / total_all, 2) if total_mt and total_all > 0 else None

            # Dependency classification
            if share_pct is not None:
                if share_pct >= 20:
                    dep_level = "HIGH — observed logistics concentration"
                elif share_pct >= 10:
                    dep_level = "MODERATE — meaningful traffic share"
                else:
                    dep_level = "LOW — minor share of total port traffic"
            else:
                dep_level = "UNKNOWN — data not available"

            results.append({
                "port": port_name,
                "year": str(row.get("year", "N/A")),
                "total_mt": total_mt,
                "overseas_mt": overseas,
                "coastal_mt": coastal,
                "share_of_all_major_ports_pct": share_pct,
                "dependency_level": dep_level,
                "note": (
                    f"Port handled approximately {total_mt:.1f} MT total cargo "
                    f"({overseas:.1f} MT overseas, {coastal:.1f} MT coastal), "
                    f"representing ~{share_pct:.1f}% of all Major Port traffic. "
                    "This indicates observed traffic concentration, not causal attribution."
                ) if total_mt else "Data unavailable",
                "source_table": str(row.get("source_table", "N/A")),
                "source_page": str(row.get("source_page", "N/A")),
                "source_year_pdf": str(row.get("source_year_pdf", "N/A")),
                "provenance": "[PORT DATA] Port-wise Cargo at Major Ports",
            })

        return results if results else [{"note": "No matching port data", "provenance": "[PORT DATA]"}]

    def _get_commodity_context(
        self, t3: pd.DataFrame, commodity: str, hs4: int
    ) -> List[Dict[str, Any]]:
        """
        Get commodity-wise cargo data at Major Ports.
        Match by commodity name proximity to T3 commodity column.
        """
        if t3.empty:
            return [{"note": "Commodity cargo data not available", "provenance": "[PORT DATA]"}]

        c_lower = commodity.strip().lower()

        # Map commodity to port commodity category
        COMM_KEYWORD_MAP = {
            "rice": ["food-grain", "others"],
            "wheat": ["food-grain", "others"],
            "maize": ["food-grain", "others"],
            "coal": ["coal"],
            "iron ore": ["iron ore"],
            "fertilizer": ["fertilizer"],
            "palm oil": ["others"],
            "soybean": ["others"],
            "sugar": ["others"],
            "pepper": ["others"],
            "cotton": ["others"],
        }
        keywords = COMM_KEYWORD_MAP.get(c_lower, ["others"])

        # Get latest year data
        latest_years = sorted(t3["year"].unique(), reverse=True)
        results = []
        for yr in latest_years[:2]:
            yr_df = t3[t3["year"] == yr]
            if yr_df.empty:
                continue
            total_row = yr_df[yr_df["commodity"].str.lower() == "total"]
            total_mt_all = float(total_row["total_mt"].iloc[0]) if len(total_row) > 0 else None

            for kw in keywords:
                matching = yr_df[yr_df["commodity"].str.lower().str.contains(kw, na=False)]
                for _, row in matching.iterrows():
                    comm_mt = float(row["total_mt"]) if pd.notna(row["total_mt"]) else None
                    share = (
                        round(100.0 * comm_mt / total_mt_all, 2)
                        if comm_mt and total_mt_all
                        else None
                    )
                    results.append({
                        "year": yr,
                        "commodity_category": str(row["commodity"]),
                        "total_mt": comm_mt,
                        "share_of_all_major_port_cargo_pct": share,
                        "note": (
                            f"Major Port commodity category '{row['commodity']}' handled "
                            f"{comm_mt:.2f} MT in {yr}"
                            + (f" (~{share:.1f}% of total Major Port cargo)" if share else "")
                            + f". Commodity '{commodity}' may fall under this category."
                        ),
                        "source_table": str(row.get("source_table", "N/A")),
                        "source_page": str(row.get("source_page", "N/A")),
                        "source_year_pdf": str(row.get("source_year_pdf", "N/A")),
                        "provenance": "[PORT DATA] Commodity-wise Cargo at Major Ports",
                    })

        if not results:
            return [{
                "note": (
                    f"No commodity category match for '{commodity}' in Major Port statistics. "
                    "The commodity may fall under 'Others' which aggregates multiple categories."
                ),
                "provenance": "[PORT DATA]",
            }]
        return results

    def _get_container_dependency(
        self, t4: pd.DataFrame, commodity: str, hs4: int
    ) -> List[Dict[str, Any]]:
        """
        Assess container dependency for the commodity.
        Containerised commodities: rice, wheat (packed), general goods, pepper, spices.
        Bulk commodities (NOT typically containerised): coal, iron ore, fertilizer raw material.
        """
        c_lower = commodity.strip().lower()
        BULK_COMMODITIES = {"coal", "iron ore", "fertilizer", "crude oil", "pol"}
        CONTAINER_COMMODITIES = {"rice", "wheat", "pepper", "spices", "turmeric",
                                  "ginger", "sugar", "cotton", "pulses", "gram"}

        if c_lower in BULK_COMMODITIES:
            return [{
                "note": (
                    f"'{commodity}' is typically transported as bulk cargo (not containerised). "
                    "Container traffic statistics are not the primary logistics channel for this commodity."
                ),
                "container_relevant": False,
                "provenance": "[RULE-BASED OUTPUT]",
            }]

        if t4.empty:
            return [{"note": "Container traffic data not available", "provenance": "[PORT DATA]"}]

        # Get aggregate container stats for latest year
        latest_year = sorted(t4["year"].unique(), reverse=True)[0] if not t4.empty else None
        if not latest_year:
            return [{"note": "No container data available", "provenance": "[PORT DATA]"}]

        yr_t4 = t4[t4["year"] == latest_year]
        total_teus = yr_t4["container_teus_000"].sum()
        total_mt   = yr_t4["container_tonnes_mt"].sum()

        # Top container ports
        top_ports = (
            yr_t4.sort_values("container_teus_000", ascending=False)
            .head(5)[["port", "container_tonnes_mt", "container_teus_000"]]
            .to_dict("records")
        )

        container_relevant = c_lower in CONTAINER_COMMODITIES

        return [{
            "year": latest_year,
            "container_relevant": container_relevant,
            "total_container_traffic_mt": round(float(total_mt), 2),
            "total_container_traffic_000_teus": round(float(total_teus), 2),
            "top_container_ports": top_ports,
            "note": (
                f"'{commodity}' {'is commonly' if container_relevant else 'may occasionally be'} "
                f"transported via containers. Major Port total container traffic: "
                f"{total_mt:.1f} MT ({total_teus:.0f} thousand TEUs) in {latest_year}. "
                "This indicates potential container logistics exposure if supply chains are disrupted."
            ) if container_relevant else (
                f"Container exposure for '{commodity}' is considered LOW (bulk commodity). "
                f"Total Major Port container traffic: {total_mt:.1f} MT ({total_teus:.0f} 000 TEUs) in {latest_year}."
            ),
            "source_year_pdf": latest_year,
            "provenance": "[PORT DATA] Container Traffic at Major Ports",
        }]

    def _get_state_logistics(self, t6: pd.DataFrame) -> List[Dict[str, Any]]:
        """Get state-wise cargo distribution context."""
        if t6.empty:
            return [{"note": "State-wise cargo data not available", "provenance": "[PORT DATA]"}]

        latest_year = sorted(t6["year"].unique(), reverse=True)[0]
        yr_t6 = t6[t6["year"] == latest_year].copy()

        # Sort by total_mt
        yr_t6 = yr_t6.dropna(subset=["total_mt"]).sort_values("total_mt", ascending=False)
        grand_total = yr_t6["total_mt"].sum()

        results = []
        for _, row in yr_t6.head(5).iterrows():
            share = round(100 * float(row["total_mt"]) / grand_total, 1) if grand_total > 0 else None
            results.append({
                "state": str(row["port"]),  # 'port' column holds state name in T6
                "year": latest_year,
                "major_port_mt": float(row["major_port_mt"]) if pd.notna(row.get("major_port_mt")) else None,
                "non_major_port_mt": float(row["non_major_port_mt"]) if pd.notna(row.get("non_major_port_mt")) else None,
                "total_mt": float(row["total_mt"]),
                "share_of_india_total_pct": share,
                "note": f"State handled {float(row['total_mt']):.1f} MT ({share:.1f}% of Indian port traffic) in {latest_year}.",
                "source_table": str(row.get("source_table", "N/A")),
                "source_page": str(row.get("source_page", "N/A")),
                "provenance": "[PORT DATA] State-wise Cargo Traffic at Indian Ports",
            })

        return results

    def _identify_bottlenecks(
        self,
        port_cargo: pd.DataFrame,
        relevant_ports: List[Dict],
        trade_type: str,
        effective_shock: float,
    ) -> List[Dict[str, Any]]:
        """
        Identify potential bottleneck scenarios.
        High share + high shock = potential logistics bottleneck.
        All language is hedged (potential, may indicate, observed).
        """
        bottlenecks = []

        if port_cargo.empty:
            return [{"note": "Insufficient data to assess bottlenecks", "provenance": "[PORT DATA]"}]

        total_all = port_cargo["total_mt"].sum() if not port_cargo.empty else 0

        for port_info in relevant_ports:
            port_name = port_info.get("port", "")
            if port_name == "Unable to determine specific port":
                continue
            prow = port_cargo[port_cargo["port"].str.contains(port_name[:12], case=False, na=False)]
            if prow.empty:
                continue
            p_total = float(prow.iloc[0]["total_mt"]) if pd.notna(prow.iloc[0]["total_mt"]) else 0
            share = 100 * p_total / total_all if total_all > 0 else 0

            if share >= 15 and effective_shock > 0.1:
                bottlenecks.append({
                    "port": port_name,
                    "observed_share_pct": round(share, 1),
                    "effective_shock": round(effective_shock, 4),
                    "level": "POTENTIAL HIGH" if share >= 20 else "POTENTIAL MODERATE",
                    "note": (
                        f"{port_name} handles ~{share:.1f}% of Major Port cargo. "
                        f"Combined with effective shock exposure of {effective_shock:.3f}, "
                        "this suggests potential logistics concentration risk. "
                        "This is an observed traffic pattern, not a causal prediction."
                    ),
                    "provenance": "[RULE-BASED OUTPUT] based on [PORT DATA]",
                })

        if not bottlenecks:
            bottlenecks.append({
                "note": (
                    "No single port identified as a high-concentration bottleneck for this "
                    "commodity+shock combination. Cargo distribution across Major Ports reduces "
                    "single-point logistics dependency risk."
                ),
                "provenance": "[RULE-BASED OUTPUT]",
            })

        return bottlenecks

    def _compute_risk_indicators(
        self,
        trade_share: float,
        effective_shock: float,
        trade_type: str,
        port_dependency: List[Dict],
        commodity_context: List[Dict],
        ml_predictions: Optional[Dict],
    ) -> List[Dict[str, Any]]:
        """
        Compute rule-based risk indicators from available data.
        """
        indicators = []

        # Trade share indicator
        if trade_share >= 15:
            ts_level = "HIGH"
            ts_note = f"Partner trade share of {trade_share:.1f}% indicates high bilateral dependency."
        elif trade_share >= 5:
            ts_level = "MODERATE"
            ts_note = f"Partner trade share of {trade_share:.1f}% suggests moderate bilateral exposure."
        else:
            ts_level = "LOW"
            ts_note = f"Partner trade share of {trade_share:.1f}% suggests limited bilateral dependency."

        indicators.append({
            "indicator": "Trade Share Concentration",
            "level": ts_level,
            "value": trade_share,
            "note": ts_note,
            "provenance": "[USER / CLI PARAMETER]",
        })

        # Effective shock indicator
        eff_level = "HIGH" if effective_shock > 0.2 else ("MODERATE" if effective_shock > 0.05 else "LOW")
        indicators.append({
            "indicator": "Effective Shock Exposure",
            "level": eff_level,
            "value": round(effective_shock, 4),
            "formula": "shock_intensity × (trade_share / 100)",
            "note": f"Effective shock exposure = {effective_shock:.4f} "
                    f"(shock_intensity × trade_share%). "
                    "Higher values indicate greater potential transmission channel.",
            "provenance": "[RULE-BASED OUTPUT]",
        })

        # ML cascade context (if provided)
        if ml_predictions:
            trade_ret = ml_predictions.get("trade", {}).get("Trade_Return_1M_Pred")
            if trade_ret is not None:
                indicators.append({
                    "indicator": "ML Cascade Trade Signal",
                    "level": "NEGATIVE" if trade_ret < 0 else "POSITIVE",
                    "value": round(trade_ret, 4),
                    "note": (
                        f"Model A projects a trade flow return of {trade_ret:+.2f}% for this scenario. "
                        "Combined with supply-chain context, this "
                        + ("reinforces logistics disruption risk." if trade_ret < 0 else "suggests stable trade flow context.")
                    ),
                    "provenance": "[ML MODEL OUTPUT]",
                })

        return indicators

    def _standard_limitations(self, commodity: str, hs4: int) -> List[str]:
        return [
            "Supply-chain analysis is based on aggregate Major Port statistics from Ministry of "
            "Ports, Shipping and Waterways publications (2023-24 and 2024-25).",
            "Port affinity mappings are based on publicly known port specialisations, not real-time data.",
            "The analysis indicates exposure and dependency patterns, not causal responsibility.",
            "Data does not include Minor/Non-Major port cargo for all states.",
            "Commodity-specific port routing is not available at granular trade-lane level.",
            f"No direct commodity-level port routing data available for HS4={hs4} ('{commodity}').",
            "Capacity utilisation data from 2023-24 PDF was flagged as potentially mis-parsed; "
            "it is excluded from this analysis.",
            "Pre-Berthing Detention and Turn Round Time data excluded due to extraction ambiguity.",
        ]

    def _build_provenance(
        self, t2: pd.DataFrame, t3: pd.DataFrame, t4: pd.DataFrame, t6: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        entries = []
        for sub, label in [(t2, "T2 Port Cargo"), (t3, "T3 Commodity"), (t4, "T4 Container"), (t6, "T6 State")]:
            if not sub.empty:
                src_tables = sub["source_table"].unique().tolist() if "source_table" in sub.columns else []
                entries.append({
                    "source_type": "[PORT DATA]",
                    "table_label": label,
                    "source_tables": src_tables,
                    "n_rows_used": len(sub),
                    "years_covered": sorted(sub["year"].unique().tolist()) if "year" in sub.columns else [],
                })
        return entries

    def _insufficient_data(
        self, commodity: str, hs4: int, trade_type: str,
        event_country: str, reason: str
    ) -> Dict[str, Any]:
        return {
            "supply_chain_analysis": {
                "commodity": commodity,
                "hs4": hs4,
                "trade_type": trade_type,
                "affected_country": event_country,
                "relevant_ports": [],
                "port_cargo_context": [],
                "commodity_port_context": [],
                "container_dependency": [],
                "state_logistics_context": [],
                "potential_bottlenecks": [],
                "risk_indicators": [],
                "limitations": [reason, "Insufficient data — cannot produce supply-chain analysis."],
            },
            "provenance": [],
        }
