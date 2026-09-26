"""
Drishti Supply-Chain Graph Builder
====================================
Constructs a heterogeneous, weighted, directed MultiDiGraph representing
relationships among geopolitical actors, commodities, Indian ports, states,
and agricultural districts.

Graph Schema
------------
Node types  (node_type attribute):
  "country"   – foreign partner country in a trade relationship
  "commodity" – traded agricultural commodity (HS4-identified)
  "port"      – Indian Major Port
  "state"     – Indian state
  "district"  – Indian agricultural district

Edge types  (edge_type attribute):
  "TRADE"      – country ↔ commodity  (directed: country → commodity for import,
                                       commodity → country for export)
  "HANDLES"    – commodity → port     (inferred affinity or observed cargo)
  "PORT_STATE" – port → state         (geographic location of the port)
  "PRODUCES"   – district → commodity (agricultural production relationship)
  "IN_STATE"   – district → state     (administrative relationship)

Weight conventions (documented per edge type):
  TRADE      weight = trade_share / 100   (proportion of India's trade with partner)
  HANDLES    weight = affinity_confidence (0-1, inferred unless observed cargo)
  PORT_STATE weight = 1.0                 (structural, no magnitude)
  PRODUCES   weight = production_share    (district prod / state total prod, latest year)
  IN_STATE   weight = 1.0                 (structural, no magnitude)

Provenance tags used:
  [PORT DATA]          – port_statistics.csv dataset
  [AGRICULTURE DATA]   – crop-wise-area-production-yield.csv
  [RULE-BASED OUTPUT]  – derived/inferred from rules or lookups
  [USER / CLI PARAMETER] – shock inputs from user

Research integrity rules:
  - Inferred commodity-port affinities are explicitly marked
    relationship_type = "inferred_affinity"
  - PORT_STATE edges represent physical port location, NOT cargo destination
  - PRODUCES edges use historical agricultural data; they do not imply
    that the district "depends" on the exact commodity traded
  - No causal claims are made from graph metrics
"""

import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set

import pandas as pd
import numpy as np
import networkx as nx

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from scripts.validate_supply_chain_data import (
    load_port_data,
    get_trusted_port_cargo,
    get_trusted_commodity_cargo,
    get_trusted_state_cargo,
)
from scripts.validate_vulnerability_data import (
    load_raw_data as load_agri_data,
    preprocess_dataset,
)
from agents.crop_commodity_mapping import (
    get_crop_names_for_commodity,
    get_commodity_for_hs4,
)

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Port → geographic state mapping
# Source: Ministry of Ports, Shipping and Waterways official port locations
# ---------------------------------------------------------------------------
PORT_STATE_MAP: Dict[str, str] = {
    "Paradip Port Authority":                "Odisha",
    "Vishakhapatnam Port Authority":         "Andhra Pradesh",
    "Kamarajar Port Limited":                "Tamil Nadu",
    "Chennai Port Authority":                "Tamil Nadu",
    "V.O. Chidambaranar Port Authority":     "Tamil Nadu",
    "Cochin Port Authority":                 "Kerala",
    "New Mangalore Port Authority":          "Karnataka",
    "Mormugao Port Authority":               "Goa",
    "JNPA":                                  "Maharashtra",
    "Mumbai Port Authority":                 "Maharashtra",
    "Deendayal Port Authority":              "Gujarat",
    "SMPA Kolkata DS":                       "West Bengal",
    "SMPA Haldia DC":                        "West Bengal",
}

# ---------------------------------------------------------------------------
# Port → commodity affinity
# Source: publicly known port specialisations (NOT inferred trade lanes)
# confidence: HIGH for well-documented, MEDIUM for plausible, LOW for generic
# ---------------------------------------------------------------------------
PORT_COMMODITY_AFFINITY: Dict[str, List[Dict[str, Any]]] = {
    "Paradip Port Authority": [
        {"commodity_key": "rice",       "confidence": 0.75, "basis": "food grain terminal"},
        {"commodity_key": "wheat",      "confidence": 0.75, "basis": "food grain terminal"},
        {"commodity_key": "coal",       "confidence": 0.85, "basis": "major coal handling"},
        {"commodity_key": "fertilizer", "confidence": 0.80, "basis": "fertilizer berths"},
    ],
    "Vishakhapatnam Port Authority": [
        {"commodity_key": "coal",       "confidence": 0.90, "basis": "largest coal import port"},
        {"commodity_key": "fertilizer", "confidence": 0.70, "basis": "fertilizer terminal"},
    ],
    "Kamarajar Port Limited": [
        {"commodity_key": "coal",       "confidence": 0.90, "basis": "coal dedicated port"},
    ],
    "Chennai Port Authority": [
        {"commodity_key": "rice",       "confidence": 0.70, "basis": "food grain handling"},
        {"commodity_key": "wheat",      "confidence": 0.70, "basis": "food grain handling"},
        {"commodity_key": "cotton",     "confidence": 0.60, "basis": "general cargo"},
        {"commodity_key": "sugar",      "confidence": 0.60, "basis": "general cargo"},
        {"commodity_key": "sugarcane",  "confidence": 0.55, "basis": "general cargo"},
    ],
    "V.O. Chidambaranar Port Authority": [
        {"commodity_key": "rice",       "confidence": 0.65, "basis": "food grain handling"},
        {"commodity_key": "wheat",      "confidence": 0.65, "basis": "food grain handling"},
        {"commodity_key": "cotton",     "confidence": 0.65, "basis": "general cargo"},
    ],
    "Cochin Port Authority": [
        {"commodity_key": "pepper",     "confidence": 0.85, "basis": "historic spice port"},
        {"commodity_key": "chilli",     "confidence": 0.75, "basis": "spice handling"},
        {"commodity_key": "turmeric",   "confidence": 0.75, "basis": "spice handling"},
        {"commodity_key": "ginger",     "confidence": 0.75, "basis": "spice handling"},
        {"commodity_key": "cashewnut",  "confidence": 0.70, "basis": "nut exports"},
        {"commodity_key": "coconut",    "confidence": 0.65, "basis": "coconut products"},
    ],
    "New Mangalore Port Authority": [
        {"commodity_key": "coal",       "confidence": 0.75, "basis": "coal import"},
        {"commodity_key": "fertilizer", "confidence": 0.65, "basis": "fertilizer import"},
    ],
    "Mormugao Port Authority": [
        {"commodity_key": "coal",       "confidence": 0.70, "basis": "coal handling"},
    ],
    "JNPA": [
        {"commodity_key": "rice",       "confidence": 0.60, "basis": "container port – food grain"},
        {"commodity_key": "wheat",      "confidence": 0.60, "basis": "container port – food grain"},
        {"commodity_key": "cotton",     "confidence": 0.65, "basis": "container port – textile"},
        {"commodity_key": "sugar",      "confidence": 0.60, "basis": "container port – agri"},
        {"commodity_key": "sugarcane",  "confidence": 0.55, "basis": "container port – agri"},
        {"commodity_key": "pulses",     "confidence": 0.60, "basis": "container port – food"},
        {"commodity_key": "onion",      "confidence": 0.65, "basis": "major onion export gateway"},
    ],
    "Mumbai Port Authority": [
        {"commodity_key": "sugar",      "confidence": 0.70, "basis": "sugar export hub"},
        {"commodity_key": "cotton",     "confidence": 0.65, "basis": "traditional cotton port"},
        {"commodity_key": "pepper",     "confidence": 0.60, "basis": "spice trade"},
        {"commodity_key": "onion",      "confidence": 0.60, "basis": "agri export"},
    ],
    "Deendayal Port Authority": [
        {"commodity_key": "rice",       "confidence": 0.70, "basis": "food grain handling"},
        {"commodity_key": "wheat",      "confidence": 0.70, "basis": "food grain handling"},
        {"commodity_key": "cotton",     "confidence": 0.75, "basis": "Gujarat cotton export hub"},
        {"commodity_key": "groundnut",  "confidence": 0.70, "basis": "oilseed export"},
        {"commodity_key": "fertilizer", "confidence": 0.75, "basis": "fertilizer import terminal"},
        {"commodity_key": "onion",      "confidence": 0.55, "basis": "agri export"},
    ],
    "SMPA Kolkata DS": [
        {"commodity_key": "rice",       "confidence": 0.70, "basis": "food grain – eastern region"},
        {"commodity_key": "wheat",      "confidence": 0.65, "basis": "food grain – eastern region"},
        {"commodity_key": "jute",       "confidence": 0.80, "basis": "traditional jute port"},
    ],
    "SMPA Haldia DC": [
        {"commodity_key": "rice",       "confidence": 0.65, "basis": "food grain – eastern region"},
        {"commodity_key": "wheat",      "confidence": 0.65, "basis": "food grain – eastern region"},
        {"commodity_key": "coal",       "confidence": 0.75, "basis": "coal handling – east"},
        {"commodity_key": "fertilizer", "confidence": 0.70, "basis": "fertilizer import"},
    ],
}


class SupplyChainGraphBuilder:
    """
    Builds a heterogeneous, weighted, directed MultiDiGraph
    from port statistics and agricultural production datasets.

    The graph is scenario-parameterized: nodes and edges relevant to a
    specific (country, commodity, trade_type) scenario are annotated
    with scenario-specific attributes.
    """

    def __init__(self):
        self._port_df: Optional[pd.DataFrame] = None
        self._agri_clean: Optional[pd.DataFrame] = None
        self._agri_all: Optional[pd.DataFrame] = None  # full all-crop dataset (for HHI/concentration denominator)
        self._load_data()

    def _load_data(self):
        try:
            raw_port = load_port_data()
            self._port_df = raw_port
            log.info("GraphBuilder: port data loaded (%d rows)", len(raw_port))
        except FileNotFoundError as e:
            log.error("GraphBuilder: port data not found: %s", e)

        try:
            raw_agri = load_agri_data()
            self._agri_all = raw_agri   # full dataset (all crops) for denominator calculations
            self._agri_clean = preprocess_dataset(raw_agri)  # season-selected, cleaned
            log.info("GraphBuilder: agri data loaded (%d raw, %d clean rows)",
                     len(raw_agri), len(self._agri_clean))
        except FileNotFoundError as e:
            log.error("GraphBuilder: agri data not found: %s", e)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build_scenario_graph(
        self,
        commodity: str,
        hs4: int,
        trade_type: str,
        event_country: str,
        shock_intensity: float = 1.0,
        trade_share: float = 5.0,
        ml_predictions: Optional[Dict[str, Any]] = None,
    ) -> nx.MultiDiGraph:
        """
        Build a heterogeneous directed multigraph for a given trade shock scenario.

        Returns
        -------
        G : nx.MultiDiGraph
            Annotated supply-chain graph with scenario-specific attributes.
        """
        G = nx.MultiDiGraph()
        G.graph["scenario"] = {
            "commodity": commodity,
            "hs4": hs4,
            "trade_type": trade_type,
            "event_country": event_country,
            "shock_intensity": shock_intensity,
            "trade_share": trade_share,
            "effective_shock": round(shock_intensity * (trade_share / 100.0), 6),
        }

        # Normalize commodity key for mapping
        comm_lower = commodity.strip().lower()

        # Step 1: Add country node
        self._add_country_node(G, event_country, trade_type, trade_share, shock_intensity)

        # Step 2: Add commodity node
        self._add_commodity_node(G, commodity, hs4)

        # Step 3: TRADE edge: country ↔ commodity
        self._add_trade_edge(G, event_country, commodity, trade_type, trade_share, shock_intensity)

        # Step 4: Add port nodes + HANDLES edges
        relevant_ports = self._get_relevant_ports(comm_lower)
        port_cargo_df = get_trusted_port_cargo(self._port_df) if self._port_df is not None else pd.DataFrame()
        state_cargo_df = get_trusted_state_cargo(self._port_df) if self._port_df is not None else pd.DataFrame()
        self._add_port_nodes_and_edges(G, commodity, comm_lower, relevant_ports, port_cargo_df)

        # Step 5: Add state nodes + PORT_STATE edges
        self._add_state_nodes_and_port_state_edges(G, relevant_ports, port_cargo_df, state_cargo_df)

        # Step 6: Add district nodes + PRODUCES edges (top-N producers)
        crop_names = get_crop_names_for_commodity(comm_lower)
        if crop_names and self._agri_clean is not None:
            self._add_district_nodes_and_produces_edges(G, commodity, crop_names)
            self._add_in_state_edges(G)

        # Annotate graph with node/edge counts
        G.graph["summary"] = {
            "n_nodes": G.number_of_nodes(),
            "n_edges": G.number_of_edges(),
            "node_types": list({G.nodes[n]["node_type"] for n in G.nodes}),
            "edge_types": list({G.edges[e]["edge_type"] for e in G.edges}),
        }
        log.info("GraphBuilder: scenario graph built — %d nodes, %d edges",
                 G.number_of_nodes(), G.number_of_edges())
        return G

    # ------------------------------------------------------------------
    # Node builders
    # ------------------------------------------------------------------

    def _add_country_node(self, G: nx.MultiDiGraph, country: str, trade_type: str,
                          trade_share: float, shock_intensity: float):
        node_id = f"country:{country}"
        effective_shock = round(shock_intensity * (trade_share / 100.0), 6)
        G.add_node(node_id,
                   node_type="country",
                   name=country,
                   trade_type=trade_type,
                   trade_share_pct=trade_share,
                   shock_intensity=shock_intensity,
                   effective_shock=effective_shock,
                   provenance="[USER / CLI PARAMETER]")

    def _add_commodity_node(self, G: nx.MultiDiGraph, commodity: str, hs4: int):
        node_id = f"commodity:{commodity}"
        crop_names = get_crop_names_for_commodity(commodity.lower()) or []
        G.add_node(node_id,
                   node_type="commodity",
                   name=commodity,
                   hs4=hs4,
                   matched_crops=crop_names,
                   provenance="[USER / CLI PARAMETER]")

    def _add_port_nodes_and_edges(self, G: nx.MultiDiGraph, commodity: str,
                                   comm_lower: str, relevant_ports: List[str],
                                   port_cargo_df: pd.DataFrame):
        """Add port nodes and HANDLES edges (commodity → port)."""
        # Total cargo across all trusted ports for share calculation
        total_mt_all = float(port_cargo_df["total_mt"].sum()) if not port_cargo_df.empty else 0.0
        latest_year = (sorted(port_cargo_df["year"].unique(), reverse=True)[0]
                       if not port_cargo_df.empty else "N/A")

        for port_name in PORT_COMMODITY_AFFINITY:
            state = PORT_STATE_MAP.get(port_name, "Unknown")
            node_id = f"port:{port_name}"

            # Get port cargo data
            pcargo = (port_cargo_df[port_cargo_df["port"].str.contains(port_name[:12], case=False, na=False)]
                      if not port_cargo_df.empty else pd.DataFrame())
            total_mt = float(pcargo.iloc[0]["total_mt"]) if not pcargo.empty and pd.notna(pcargo.iloc[0]["total_mt"]) else None
            share_pct = round(100.0 * total_mt / total_mt_all, 3) if total_mt and total_mt_all > 0 else None

            G.add_node(node_id,
                       node_type="port",
                       name=port_name,
                       state=state,
                       total_mt=total_mt,
                       share_of_all_major_ports_pct=share_pct,
                       cargo_year=latest_year if total_mt else None,
                       data_quality="TRUSTED" if total_mt else "NO_DATA",
                       provenance="[PORT DATA]" if total_mt else "[RULE-BASED OUTPUT]")

            # HANDLES edges: commodity → port (for relevant ports only)
            affinities = PORT_COMMODITY_AFFINITY.get(port_name, [])
            for aff in affinities:
                if aff["commodity_key"] == comm_lower:
                    edge_id = G.add_edge(
                        f"commodity:{commodity}",
                        node_id,
                        edge_type="HANDLES",
                        relationship_type="inferred_affinity",
                        commodity=commodity,
                        port=port_name,
                        affinity_basis=aff["basis"],
                        confidence=aff["confidence"],
                        weight=aff["confidence"],  # weight = confidence (0-1)
                        weight_meaning="Affinity confidence (0=unknown, 1=well-documented)",
                        port_total_mt=total_mt,
                        port_share_pct=share_pct,
                        in_relevant_set=port_name in relevant_ports,
                        provenance="[RULE-BASED OUTPUT] port specialisation knowledge",
                        data_note="Inferred affinity based on known port specialisation, NOT observed commodity-specific trade lane data.",
                    )

    def _add_state_nodes_and_port_state_edges(self, G: nx.MultiDiGraph,
                                               relevant_ports: List[str],
                                               port_cargo_df: pd.DataFrame,
                                               state_cargo_df: pd.DataFrame):
        """Add state nodes and PORT_STATE edges (port → state)."""
        states_added: Set[str] = set()

        for port_name, state in PORT_STATE_MAP.items():
            port_node = f"port:{port_name}"
            state_node = f"state:{state}"

            if state_node not in G.nodes:
                # Get state cargo data
                scargo = (state_cargo_df[state_cargo_df["port"].str.contains(state[:8], case=False, na=False)]
                          if not state_cargo_df.empty else pd.DataFrame())
                total_mt = float(scargo.iloc[0]["total_mt"]) if not scargo.empty and pd.notna(scargo.iloc[0].get("total_mt")) else None

                G.add_node(state_node,
                           node_type="state",
                           name=state,
                           total_cargo_mt=total_mt,
                           provenance="[PORT DATA]" if total_mt else "[RULE-BASED OUTPUT]")

            if port_node in G.nodes:
                G.add_edge(port_node, state_node,
                           edge_type="PORT_STATE",
                           relationship_type="geographic_location",
                           weight=1.0,
                           weight_meaning="Structural geographic relationship (no cargo magnitude)",
                           data_note=(
                               "PORT_STATE edge represents the geographic location of the port "
                               "in that state. It does NOT imply that cargo handled by this port "
                               "is destined for or originates from this state."
                           ),
                           provenance="[RULE-BASED OUTPUT] port location mapping")

    def _add_district_nodes_and_produces_edges(self, G: nx.MultiDiGraph,
                                                commodity: str, crop_names: List[str]):
        """
        Add district nodes and PRODUCES edges (district → commodity).
        Uses latest year agricultural production data.
        Limited to top-20 producing districts to keep graph tractable.
        """
        if self._agri_clean is None:
            return

        crop_df = self._agri_clean[
            self._agri_clean["crop_name"].isin(crop_names) &
            ~self._agri_clean["production_missing"]
        ].copy()
        if crop_df.empty:
            return

        latest_year = sorted(crop_df["year"].unique())[-1]
        latest = crop_df[crop_df["year"] == latest_year].copy()

        # Aggregate: one record per (state, district, crop) in latest year
        agg = (
            latest.groupby(["state_name", "district_name", "crop_name"])
            .agg(production=("production", "sum"), area=("area", "sum"), yield_=("yield", "mean"))
            .reset_index()
        )

        # State-level total production for production share denominator
        state_total = (
            agg.groupby(["state_name", "crop_name"])["production"]
            .sum().reset_index().rename(columns={"production": "state_total_prod"})
        )
        agg = agg.merge(state_total, on=["state_name", "crop_name"], how="left")
        agg["production_share"] = np.where(
            agg["state_total_prod"] > 0,
            agg["production"] / agg["state_total_prod"],
            0.0
        )

        # Top-20 by production
        top_districts = agg.nlargest(20, "production").reset_index(drop=True)

        for _, row in top_districts.iterrows():
            district_node = f"district:{row['state_name']}:{row['district_name']}"
            state_node = f"state:{row['state_name']}"

            if district_node not in G.nodes:
                G.add_node(district_node,
                           node_type="district",
                           name=row["district_name"],
                           state=row["state_name"],
                           provenance="[AGRICULTURE DATA]")

            # Ensure state node exists (for non-port producing states)
            if state_node not in G.nodes:
                G.add_node(state_node,
                           node_type="state",
                           name=str(row["state_name"]),
                           total_cargo_mt=None,
                           has_major_port=False,
                           provenance="[AGRICULTURE DATA]")

            # PRODUCES edge: district → commodity
            G.add_edge(district_node,
                       f"commodity:{commodity}",
                       edge_type="PRODUCES",
                       relationship_type="agricultural_production",
                       crop_name=row["crop_name"],
                       year=latest_year,
                       production_tonnes=float(row["production"]),
                       area_ha=float(row["area"]),
                       yield_t_per_ha=float(row["yield_"]),
                       production_share=round(float(row["production_share"]), 4),
                       weight=round(float(row["production_share"]), 4),
                       weight_meaning="Production share = district_prod / state_total_prod",
                       provenance="[AGRICULTURE DATA] crop-wise-area-production-yield.csv")

    def _add_in_state_edges(self, G: nx.MultiDiGraph):
        """Add IN_STATE edges: district → state (administrative relationship)."""
        for node, data in G.nodes(data=True):
            if data.get("node_type") == "district":
                state_name = data.get("state", "")
                state_node = f"state:{state_name}"
                if state_node in G.nodes:
                    G.add_edge(node, state_node,
                               edge_type="IN_STATE",
                               relationship_type="administrative",
                               weight=1.0,
                               weight_meaning="Administrative membership (no magnitude)",
                               provenance="[AGRICULTURE DATA]")

    def _add_trade_edge(self, G: nx.MultiDiGraph, country: str, commodity: str,
                        trade_type: str, trade_share: float, shock_intensity: float):
        """
        TRADE edge: country → commodity (for import) or commodity → country (for export).
        Weight = trade_share / 100 (proportion of India's commodity trade with partner).
        """
        country_node = f"country:{country}"
        commodity_node = f"commodity:{commodity}"
        effective_shock = round(shock_intensity * (trade_share / 100.0), 6)
        weight = trade_share / 100.0

        if trade_type.capitalize() == "Import":
            src, tgt = country_node, commodity_node
            direction_note = f"India imports {commodity} from {country}"
        else:
            src, tgt = commodity_node, country_node
            direction_note = f"India exports {commodity} to {country}"

        G.add_edge(src, tgt,
                   edge_type="TRADE",
                   relationship_type="observed_trade_relationship",
                   trade_type=trade_type,
                   trade_share_pct=trade_share,
                   shock_intensity=shock_intensity,
                   effective_shock=effective_shock,
                   weight=weight,
                   weight_meaning="trade_share / 100 — proportion of India's bilateral commodity trade",
                   direction=direction_note,
                   data_note=(
                       "Trade share is a user-specified parameter representing the partner country's "
                       "share of India's total commodity trade. It is NOT derived from granular "
                       "trade-lane or port-specific routing data."
                   ),
                   provenance="[USER / CLI PARAMETER]")

    def _get_relevant_ports(self, comm_lower: str) -> List[str]:
        """Return list of port names with known affinity for this commodity."""
        return [
            port for port, affs in PORT_COMMODITY_AFFINITY.items()
            if any(a["commodity_key"] == comm_lower for a in affs)
        ]

    # ------------------------------------------------------------------
    # Serialization helper
    # ------------------------------------------------------------------

    def graph_to_dict(self, G: nx.MultiDiGraph) -> Dict[str, Any]:
        """
        Convert graph to a JSON-serializable dict for API output
        and dashboard consumption.
        """
        nodes = []
        for node_id, data in G.nodes(data=True):
            nodes.append({"id": node_id, **{k: _jsonify(v) for k, v in data.items()}})

        edges = []
        for u, v, key, data in G.edges(keys=True, data=True):
            edges.append({"source": u, "target": v, "key": key,
                          **{k: _jsonify(v) for k, v in data.items()}})

        return {
            "graph_meta": G.graph,
            "nodes": nodes,
            "edges": edges,
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _jsonify(v: Any) -> Any:
    """Convert numpy scalars to Python primitives for JSON serialization."""
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return float(v)
    if isinstance(v, (np.ndarray,)):
        return v.tolist()
    return v
