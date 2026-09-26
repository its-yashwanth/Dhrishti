"""
Drishti Supply-Chain Shock Propagation
========================================
Implements a transparent, step-by-step scenario shock propagation
through the supply-chain graph.

Propagation Model
-----------------
A geopolitical shock is modeled as a perturbation that travels along
graph edges in a decay-weighted fashion:

  Geopolitical Shock
      │
      ▼  TRADE edge (weight = trade_share/100)
  Country Node (shock_intensity × trade_share/100 = effective_shock)
      │
      ▼  HANDLES edge (weight = affinity_confidence)
  Port Node  (exposure = effective_shock × affinity_confidence)
      │
      ▼  PORT_STATE edge (weight = 1.0 — structural only)
  State Node (exposure = port exposure, no further decay here)
      │
      ▼  (via IN_STATE) District Node
  Agricultural Region (exposure = state exposure × production_share)

At each step, the propagation exposure is:
  node_exposure = upstream_exposure × edge_weight

This is a SCENARIO PROPAGATION MODEL, not a causal prediction.

Research integrity:
  - The propagation is a MODELED scenario, not an empirical estimate.
  - Edge weights for HANDLES are inferred affinities, not observed flows.
  - PORT_STATE edges are geographic: cargo routing to states is NOT modeled.
  - The resulting "propagation exposure" is a relative indicator only.
  - No probability interpretation should be applied.
  - All terms: "scenario exposure", "modeled dependency", "propagation indicator".

Decay parameters:
  HANDLES_DECAY: float [0, 1]
    Controls how much exposure decays when propagating through a HANDLES edge.
    Interpretation: Commodity-port affinity confidence already embedded in weight;
    this decay acknowledges that port affinity ≠ certain trade routing.
    Value: 0.85 (15% additional uncertainty for affinity propagation)
    Rationale: Conservative reduction to acknowledge inferred affinities.
    Range: [0.5, 1.0]; lower = more conservative propagation.

  PORT_STATE_DECAY: float [0, 1]
    Controls decay through PORT_STATE edges.
    Value: 0.70
    Rationale: Port cargo is not uniformly destined for the port's home state;
    significant decay appropriate.
    Range: [0.3, 1.0].

  DISTRICT_DECAY: float [0, 1]
    Applied via production_share from PRODUCES edge; no additional decay.
    The production_share already scales district exposure proportionally.
"""

import logging
from typing import Dict, Any, List, Optional
from collections import defaultdict

import networkx as nx
import numpy as np

log = logging.getLogger(__name__)

# Documented propagation decay parameters
HANDLES_DECAY: float = 0.85    # Affinity uncertainty factor
PORT_STATE_DECAY: float = 0.70  # Port-to-state routing uncertainty
# District exposure = state_exposure × production_share (no additional decay)


def propagate_shock(
    G: nx.MultiDiGraph,
    commodity: str,
    trade_type: str,
    event_country: str,
    shock_intensity: float,
    trade_share: float,
    top_n_districts: int = 10,
) -> Dict[str, Any]:
    """
    Execute transparent shock propagation through the supply-chain graph.

    Parameters
    ----------
    G               : Supply-chain scenario graph (from builders.py)
    commodity       : Commodity name
    trade_type      : 'Import' or 'Export'
    event_country   : Partner country
    shock_intensity : User-specified shock multiplier
    trade_share     : Partner's share of India's commodity trade (%)
    top_n_districts : Number of top-exposed districts to return

    Returns
    -------
    dict with structured propagation results including per-step exposures,
    exposed ports, states, and agricultural districts.
    """
    effective_shock = round(shock_intensity * (trade_share / 100.0), 6)
    country_node = f"country:{event_country}"
    commodity_node = f"commodity:{commodity}"

    propagation_steps = []

    # -------------------------------------------------------
    # Step 0: Geopolitical event → effective shock
    # -------------------------------------------------------
    propagation_steps.append({
        "step": 0,
        "description": "Geopolitical event parameterized as effective shock",
        "node": country_node,
        "node_type": "country",
        "exposure": effective_shock,
        "calculation": f"effective_shock = shock_intensity ({shock_intensity}) × (trade_share ({trade_share}%) / 100)",
        "provenance": "[USER / CLI PARAMETER]",
    })

    # -------------------------------------------------------
    # Step 1: Country → Commodity (TRADE edge)
    # -------------------------------------------------------
    commodity_exposure = effective_shock  # TRADE edge weight = trade_share/100, already embedded
    propagation_steps.append({
        "step": 1,
        "description": "Shock propagates from partner country to commodity via TRADE relationship",
        "node": commodity_node,
        "node_type": "commodity",
        "exposure": commodity_exposure,
        "calculation": f"commodity_exposure = effective_shock ({effective_shock:.4f}) [TRADE edge, weight = {trade_share/100:.4f}]",
        "edge_type": "TRADE",
        "provenance": "[USER / CLI PARAMETER] → [GRAPH-DERIVED]",
        "note": "The effective shock represents the proportion of commodity trade affected by the geopolitical event.",
    })

    # -------------------------------------------------------
    # Step 2: Commodity → Ports (HANDLES edges)
    # -------------------------------------------------------
    port_exposures: Dict[str, Dict] = {}
    for u, v, data in G.edges(data=True):
        if data.get("edge_type") == "HANDLES" and u == commodity_node:
            affinity = data.get("confidence", 0.5)
            port_exp = commodity_exposure * affinity * HANDLES_DECAY
            port_name = G.nodes[v].get("name", v)
            port_exposures[v] = {
                "port_node": v,
                "port_name": port_name,
                "state": G.nodes[v].get("state", "Unknown"),
                "exposure": round(port_exp, 6),
                "affinity_confidence": affinity,
                "handles_decay": HANDLES_DECAY,
                "cargo_mt": G.nodes[v].get("total_mt"),
                "cargo_share_pct": G.nodes[v].get("share_of_all_major_ports_pct"),
                "data_quality": G.nodes[v].get("data_quality", "UNKNOWN"),
                "relationship_type": data.get("relationship_type", "inferred_affinity"),
                "provenance": data.get("provenance", "[RULE-BASED OUTPUT]"),
                "calculation": (
                    f"port_exposure = commodity_exposure ({commodity_exposure:.4f}) × "
                    f"affinity ({affinity:.2f}) × decay ({HANDLES_DECAY})"
                ),
            }

    for port_node, pexp in sorted(port_exposures.items(),
                                   key=lambda x: x[1]["exposure"], reverse=True):
        propagation_steps.append({
            "step": 2,
            "description": f"Shock propagates from commodity to port (inferred affinity)",
            "node": port_node,
            "node_type": "port",
            "exposure": pexp["exposure"],
            "calculation": pexp["calculation"],
            "edge_type": "HANDLES",
            "affinity_confidence": pexp["affinity_confidence"],
            "provenance": pexp["provenance"],
            "note": (
                "HANDLES edge represents inferred port-commodity affinity, not observed "
                "trade routing. Exposure is a modeled indicator, not an observed flow."
            ),
        })

    # -------------------------------------------------------
    # Step 3: Port → State (PORT_STATE edges) + decay
    # -------------------------------------------------------
    state_exposures: Dict[str, Dict] = defaultdict(lambda: {
        "state_node": "", "state_name": "", "exposure": 0.0,
        "contributing_ports": [], "provenance": "[GRAPH-DERIVED]"
    })

    for port_node, pexp in port_exposures.items():
        for _, state_node, data in G.out_edges(port_node, data=True):
            if data.get("edge_type") == "PORT_STATE":
                state_exp = pexp["exposure"] * PORT_STATE_DECAY
                state_name = G.nodes[state_node].get("name", state_node)
                state_exposures[state_node]["state_node"] = state_node
                state_exposures[state_node]["state_name"] = state_name
                state_exposures[state_node]["exposure"] = max(
                    state_exposures[state_node]["exposure"], state_exp
                )
                state_exposures[state_node]["contributing_ports"].append({
                    "port": pexp["port_name"],
                    "port_exposure": pexp["exposure"],
                    "port_state_decay": PORT_STATE_DECAY,
                    "state_exposure_via_port": round(state_exp, 6),
                })
                state_exposures[state_node]["provenance"] = "[GRAPH-DERIVED]"
                state_exposures[state_node]["calculation"] = (
                    f"state_exposure = max(port_exposures × decay ({PORT_STATE_DECAY}))"
                )
                state_exposures[state_node]["data_note"] = (
                    "PORT_STATE edges reflect geographic port location, not cargo destination. "
                    f"PORT_STATE_DECAY={PORT_STATE_DECAY} acknowledges routing uncertainty."
                )

    for state_node, sexp in sorted(state_exposures.items(),
                                    key=lambda x: x[1]["exposure"], reverse=True):
        propagation_steps.append({
            "step": 3,
            "description": "Shock propagates from port to state (geographic, with uncertainty decay)",
            "node": state_node,
            "node_type": "state",
            "exposure": round(sexp["exposure"], 6),
            "calculation": sexp["calculation"],
            "edge_type": "PORT_STATE",
            "port_state_decay": PORT_STATE_DECAY,
            "provenance": sexp["provenance"],
            "note": sexp.get("data_note", ""),
        })

    # -------------------------------------------------------
    # Step 4: District exposure via state + production share
    # -------------------------------------------------------
    district_exposures = []
    for u, v, data in G.edges(data=True):
        if data.get("edge_type") == "IN_STATE":
            state_node = v
            if state_node in state_exposures:
                state_exp = state_exposures[state_node]["exposure"]
                # Find production share of this district for the commodity
                prod_share = 0.0
                prod_tonnes = None
                for _, cv, pdata in G.out_edges(u, data=True):
                    if pdata.get("edge_type") == "PRODUCES" and cv == commodity_node:
                        prod_share = pdata.get("production_share", 0.0)
                        prod_tonnes = pdata.get("production_tonnes")
                        break

                if prod_share > 0:
                    dist_exp = state_exp * prod_share
                    dist_data = G.nodes[u]
                    district_exposures.append({
                        "district_node": u,
                        "district_name": dist_data.get("name", u),
                        "state": dist_data.get("state", "Unknown"),
                        "exposure": round(dist_exp, 6),
                        "state_exposure": round(state_exp, 6),
                        "production_share": round(prod_share, 4),
                        "production_tonnes": prod_tonnes,
                        "calculation": (
                            f"district_exposure = state_exposure ({state_exp:.4f}) × "
                            f"production_share ({prod_share:.4f})"
                        ),
                        "provenance": "[GRAPH-DERIVED] + [AGRICULTURE DATA]",
                    })

    district_exposures.sort(key=lambda x: x["exposure"], reverse=True)
    top_districts = district_exposures[:top_n_districts]

    # -------------------------------------------------------
    # Summary
    # -------------------------------------------------------
    max_port_exp = max((p["exposure"] for p in port_exposures.values()), default=0)
    max_state_exp = max((s["exposure"] for s in state_exposures.values()), default=0)
    max_dist_exp = max((d["exposure"] for d in district_exposures), default=0)

    propagation_summary = {
        "effective_shock": effective_shock,
        "max_commodity_exposure": commodity_exposure,
        "max_port_exposure": round(max_port_exp, 6),
        "max_state_exposure": round(max_state_exp, 6),
        "max_district_exposure": round(max_dist_exp, 6),
        "n_ports_in_propagation": len(port_exposures),
        "n_states_in_propagation": len(state_exposures),
        "n_districts_in_propagation": len(district_exposures),
        "propagation_decay_params": {
            "handles_decay": HANDLES_DECAY,
            "port_state_decay": PORT_STATE_DECAY,
            "handles_decay_rationale": "15% reduction for inferred affinity uncertainty",
            "port_state_decay_rationale": "30% reduction: port location ≠ cargo destination",
        },
    }

    return {
        "scenario": {
            "commodity": commodity,
            "trade_type": trade_type,
            "event_country": event_country,
            "shock_intensity": shock_intensity,
            "trade_share": trade_share,
            "effective_shock": effective_shock,
        },
        "propagation_model": "Heterogeneous graph traversal with affinity and routing decay",
        "propagation_steps": propagation_steps,
        "propagation_summary": propagation_summary,
        "exposed_ports": sorted(port_exposures.values(), key=lambda x: x["exposure"], reverse=True),
        "exposed_states": sorted(
            [s for s in state_exposures.values() if s["state_name"]],
            key=lambda x: x["exposure"], reverse=True
        ),
        "top_exposed_districts": top_districts,
        "all_district_exposures": district_exposures,
        "research_disclaimer": (
            "This is a SCENARIO PROPAGATION MODEL, not a causal prediction. "
            "Exposure values are relative indicators derived from modeled relationships. "
            "They should not be interpreted as probabilities or causal magnitudes. "
            "HANDLES edges use inferred port affinities; PORT_STATE edges use geographic location "
            "which does NOT imply cargo routing."
        ),
        "provenance": "[GRAPH-DERIVED] + [AGRICULTURE DATA] + [USER / CLI PARAMETER]",
    }
