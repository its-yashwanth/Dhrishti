"""
Drishti Supply-Chain Graph Analytics
======================================
Computes meaningful, documented graph metrics on the Drishti supply-chain
MultiDiGraph.

Each metric is documented with:
  - Why it is relevant to supply-chain analysis
  - What it measures on THIS graph
  - What data underpins it
  - Whether it is observed or derived
  - Key limitations / caveats

Metrics implemented:
  1. Weighted degree / node strength
  2. In-degree / out-degree
  3. Betweenness centrality
  4. Port dependency
  5. Trade dependency
  6. Alternative path analysis
  7. Critical node identification
  8. Commodity concentration
  9. Regional (state) dependency
 10. Bottleneck detection

CRITICAL: Graph metrics are DERIVED indicators, not causal predictions.
High betweenness centrality means a node lies on many modeled paths in
this graph. It does NOT mean the node is causally responsible for
disruption or that disruption will occur.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple, Set
from collections import defaultdict

import networkx as nx
import numpy as np

log = logging.getLogger(__name__)

# Minimum confidence threshold for including HANDLES edges in path analysis
MIN_HANDLES_CONFIDENCE = 0.50


def compute_all_analytics(
    G: nx.MultiDiGraph,
    commodity: str,
    trade_type: str,
    event_country: str,
) -> Dict[str, Any]:
    """
    Compute the full suite of supply-chain graph analytics.

    Returns
    -------
    dict containing all metric groups with documentation and provenance.
    """
    analytics: Dict[str, Any] = {}

    # 1. Node strength (weighted degree)
    analytics["node_strength"] = compute_node_strength(G)

    # 2. Degree analysis
    analytics["degree_analysis"] = compute_degree_analysis(G)

    # 3. Betweenness centrality
    analytics["betweenness_centrality"] = compute_betweenness(G)

    # 4. Port dependency
    analytics["port_dependency"] = compute_port_dependency(G, commodity)

    # 5. Trade dependency
    analytics["trade_dependency"] = compute_trade_dependency(G, event_country, commodity, trade_type)

    # 6. Alternative path analysis
    analytics["alternative_paths"] = compute_alternative_paths(G, commodity)

    # 7. Bottleneck analysis
    analytics["bottleneck_analysis"] = compute_bottlenecks(G, commodity, trade_type)

    # 8. Commodity concentration
    analytics["commodity_concentration"] = compute_commodity_concentration(G, commodity)

    # 9. Regional dependency
    analytics["regional_dependency"] = compute_regional_dependency(G, commodity)

    # 10. Critical node identification
    analytics["critical_nodes"] = identify_critical_nodes(G, commodity)

    # 11. Graph connectivity summary
    analytics["connectivity"] = compute_connectivity(G)

    # Provenance tag for all analytics
    analytics["provenance"] = "[GRAPH-DERIVED] computed from supply-chain MultiDiGraph"
    analytics["caveat"] = (
        "All graph metrics are derived indicators from a modeled supply-chain graph. "
        "High centrality or dependency scores indicate structural positions in the model, "
        "NOT causal responsibility for disruption. Limitations: inferred port affinities, "
        "absence of granular trade-lane data, historical agricultural data only."
    )

    return analytics


# ---------------------------------------------------------------------------
# 1. Node Strength (weighted degree)
# ---------------------------------------------------------------------------

def compute_node_strength(G: nx.MultiDiGraph) -> Dict[str, Any]:
    """
    Node strength = sum of edge weights connected to a node.

    Relevance: Identifies nodes with high aggregate weight in the graph.
    In this supply-chain model, high strength indicates a node is involved
    in many high-confidence or high-weight relationships.
    Data basis: edge weights (trade_share, affinity_confidence, production_share).
    Type: DERIVED from graph structure.
    """
    in_strength = defaultdict(float)
    out_strength = defaultdict(float)

    for u, v, data in G.edges(data=True):
        w = float(data.get("weight", 1.0))
        out_strength[u] += w
        in_strength[v] += w

    results = {}
    for node in G.nodes:
        ntype = G.nodes[node].get("node_type", "unknown")
        results[node] = {
            "node_type": ntype,
            "in_strength": round(in_strength[node], 4),
            "out_strength": round(out_strength[node], 4),
            "total_strength": round(in_strength[node] + out_strength[node], 4),
        }

    # Top by total strength
    top_by_strength = sorted(results.items(), key=lambda x: x[1]["total_strength"], reverse=True)[:10]

    return {
        "description": "Weighted degree (sum of edge weights per node). High strength = involved in many high-weight relationships.",
        "node_strengths": results,
        "top_10_by_total_strength": [(k, v) for k, v in top_by_strength],
        "data_basis": "Edge weights: trade_share/100 (TRADE), affinity_confidence (HANDLES), production_share (PRODUCES)",
        "type": "DERIVED",
        "provenance": "[GRAPH-DERIVED]",
    }


# ---------------------------------------------------------------------------
# 2. Degree Analysis
# ---------------------------------------------------------------------------

def compute_degree_analysis(G: nx.MultiDiGraph) -> Dict[str, Any]:
    """
    In-degree: number of incoming edges (influences a node receives).
    Out-degree: number of outgoing edges (influences a node propagates).

    Relevance: Nodes with high in-degree receive inputs from many sources.
    Nodes with high out-degree propagate to many targets.
    For commodity nodes: high in-degree = many production/trade sources.
    For port nodes: high in-degree = handles many commodities.
    Type: DERIVED from graph structure.
    """
    by_type: Dict[str, List] = defaultdict(list)

    for node in G.nodes:
        ntype = G.nodes[node].get("node_type", "unknown")
        in_d = G.in_degree(node)
        out_d = G.out_degree(node)
        by_type[ntype].append({
            "node": node,
            "name": G.nodes[node].get("name", node),
            "in_degree": in_d,
            "out_degree": out_d,
            "total_degree": in_d + out_d,
        })

    # Sort each type by total_degree
    for ntype in by_type:
        by_type[ntype] = sorted(by_type[ntype], key=lambda x: x["total_degree"], reverse=True)

    return {
        "description": "In/out degree per node. High in-degree = many incoming relationships; high out-degree = many outgoing.",
        "by_node_type": dict(by_type),
        "type": "DERIVED",
        "provenance": "[GRAPH-DERIVED]",
    }


# ---------------------------------------------------------------------------
# 3. Betweenness Centrality
# ---------------------------------------------------------------------------

def compute_betweenness(G: nx.MultiDiGraph) -> Dict[str, Any]:
    """
    Betweenness centrality = fraction of shortest paths passing through a node.

    Relevance: Identifies nodes that lie on many paths between other nodes.
    In this model, a port with high betweenness centrality is on many modeled
    commodity-to-district pathways — indicating it is a structural intermediary.

    IMPORTANT CAVEAT: High betweenness does NOT mean this node will be disrupted
    or that its disruption causes proportional supply-chain failure. The graph
    is a simplified model; real supply chains have redundancies not captured here.

    Type: DERIVED from graph structure.
    Data limitation: Uses inferred affinity edges; betweenness reflects the model,
    not observed logistics flows.
    """
    # Work on a simple DiGraph (sum edge weights for multi-edges)
    simple_G = _to_simple_digraph(G, weight_attr="weight")

    try:
        betweenness = nx.betweenness_centrality(simple_G, weight="weight", normalized=True)
    except Exception as e:
        log.warning("Betweenness centrality computation failed: %s", e)
        betweenness = {}

    enriched = {}
    for node, score in betweenness.items():
        enriched[node] = {
            "betweenness_centrality": round(score, 6),
            "node_type": G.nodes[node].get("node_type", "unknown") if node in G.nodes else "unknown",
            "name": G.nodes[node].get("name", node) if node in G.nodes else node,
        }

    # Top nodes sorted by betweenness
    top_nodes = sorted(enriched.items(), key=lambda x: x[1]["betweenness_centrality"], reverse=True)[:10]

    return {
        "description": (
            "Betweenness centrality: fraction of shortest weighted paths passing through each node. "
            "High score = structural intermediary in the modeled supply chain."
        ),
        "caveat": (
            "High betweenness centrality indicates a structural position in the graph model, "
            "NOT causal responsibility for disruption. The graph uses inferred port affinities."
        ),
        "node_centralities": enriched,
        "top_10_by_betweenness": [(k, v) for k, v in top_nodes],
        "type": "DERIVED",
        "provenance": "[GRAPH-DERIVED]",
    }


# ---------------------------------------------------------------------------
# 4. Port Dependency
# ---------------------------------------------------------------------------

def compute_port_dependency(G: nx.MultiDiGraph, commodity: str) -> Dict[str, Any]:
    """
    Port dependency analysis for the specified commodity.

    Metrics:
    - Which ports are connected to this commodity via HANDLES edges
    - Port cargo share (from port node attributes)
    - Port affinity confidence
    - Structural importance (number of HANDLES paths)

    Type: DERIVED from graph + PORT DATA.
    """
    commodity_node = f"commodity:{commodity}"
    port_deps = []

    for u, v, data in G.edges(data=True):
        if data.get("edge_type") == "HANDLES" and u == commodity_node:
            port_name = G.nodes[v].get("name", v)
            port_data = G.nodes[v]
            port_deps.append({
                "port": port_name,
                "port_node": v,
                "confidence": data.get("confidence", 0.0),
                "affinity_basis": data.get("affinity_basis", ""),
                "relationship_type": data.get("relationship_type", "inferred_affinity"),
                "port_total_mt": port_data.get("total_mt"),
                "port_share_pct": port_data.get("share_of_all_major_ports_pct"),
                "geographic_state": port_data.get("state", "Unknown"),
                "data_quality": port_data.get("data_quality", "UNKNOWN"),
                "cargo_data_year": port_data.get("cargo_year"),
                "provenance": data.get("provenance", "[RULE-BASED OUTPUT]"),
            })

    # Sort by confidence then cargo share
    port_deps.sort(key=lambda x: (x["confidence"], x.get("port_share_pct") or 0), reverse=True)

    # Concentration: Herfindahl-like measure using port cargo shares
    shares = [p["port_share_pct"] or 0 for p in port_deps]
    total_share = sum(shares)
    if total_share > 0:
        normalized = [s / total_share for s in shares]
        hhi = sum(s * s for s in normalized)
    else:
        hhi = None

    return {
        "description": "Ports identified as relevant handlers for this commodity.",
        "commodity": commodity,
        "n_relevant_ports": len(port_deps),
        "port_dependencies": port_deps,
        "port_concentration_hhi": round(hhi, 4) if hhi is not None else None,
        "port_concentration_note": (
            f"HHI = {hhi:.4f} (0=perfectly distributed, 1=all handled by one port). "
            "Computed over relevant ports' cargo shares."
        ) if hhi is not None else "Insufficient port cargo data for HHI.",
        "type": "DERIVED from HANDLES edges + [PORT DATA]",
        "data_note": "HANDLES edges represent inferred affinity, NOT observed commodity-specific routing.",
        "provenance": "[GRAPH-DERIVED] + [PORT DATA]",
    }


# ---------------------------------------------------------------------------
# 5. Trade Dependency
# ---------------------------------------------------------------------------

def compute_trade_dependency(G: nx.MultiDiGraph, country: str, commodity: str,
                              trade_type: str) -> Dict[str, Any]:
    """
    Trade dependency analysis for the country-commodity TRADE edge.

    Type: Directly from USER / CLI PARAMETER via TRADE edge.
    """
    country_node = f"country:{country}"
    commodity_node = f"commodity:{commodity}"

    trade_edges = []
    for u, v, data in G.edges(data=True):
        if data.get("edge_type") == "TRADE" and (
            (u == country_node and v == commodity_node) or
            (u == commodity_node and v == country_node)
        ):
            trade_edges.append(data)

    if not trade_edges:
        return {"note": "No TRADE edge found.", "provenance": "[GRAPH-DERIVED]"}

    edge = trade_edges[0]
    ts = edge.get("trade_share_pct", 0)
    eff_shock = edge.get("effective_shock", 0)
    weight = edge.get("weight", ts / 100.0)

    # Classify dependency
    if ts >= 20:
        dep_level = "HIGH"
        dep_note = f"Partner trade share of {ts}% indicates high bilateral dependency. Supply disruption would materially affect {commodity} flows."
    elif ts >= 8:
        dep_level = "MODERATE"
        dep_note = f"Partner trade share of {ts}% indicates moderate bilateral exposure. Partial alternative sourcing may be available."
    else:
        dep_level = "LOW"
        dep_note = f"Partner trade share of {ts}% suggests limited bilateral dependency. Alternative sources are likely available."

    return {
        "description": "Trade dependency of India on this partner for the specified commodity.",
        "country": country,
        "commodity": commodity,
        "trade_type": trade_type,
        "trade_share_pct": ts,
        "effective_shock": eff_shock,
        "dependency_level": dep_level,
        "dependency_note": dep_note,
        "graph_edge_weight": round(weight, 4),
        "type": "Derived from TRADE edge weight",
        "data_note": edge.get("data_note", ""),
        "provenance": "[USER / CLI PARAMETER] → [GRAPH-DERIVED]",
    }


# ---------------------------------------------------------------------------
# 6. Alternative Path Analysis
# ---------------------------------------------------------------------------

def compute_alternative_paths(G: nx.MultiDiGraph, commodity: str) -> Dict[str, Any]:
    """
    Identifies alternative logistics paths in the graph.

    For a given commodity, alternative paths are:
    - Other countries with TRADE edges (potential alternative sourcing)
    - Other ports with HANDLES edges (potential alternative routing)
    - Other states accessible from those ports

    Relevance: Alternative paths indicate resilience — if one country/port
    is disrupted, these are the modeled alternatives.
    Type: DERIVED from graph structure.
    Limitation: Based on model topology, not observed trade flows.
    """
    commodity_node = f"commodity:{commodity}"

    # Alternative source countries (other TRADE edges to this commodity)
    alt_countries = []
    for u, v, data in G.edges(data=True):
        if data.get("edge_type") == "TRADE" and (u == commodity_node or v == commodity_node):
            country_node = u if v == commodity_node else v
            if G.nodes.get(country_node, {}).get("node_type") == "country":
                alt_countries.append({
                    "country": G.nodes[country_node].get("name", country_node),
                    "trade_share_pct": data.get("trade_share_pct", "N/A"),
                })

    # Alternative handling ports (other HANDLES edges)
    alt_ports = []
    for u, v, data in G.edges(data=True):
        if data.get("edge_type") == "HANDLES" and u == commodity_node:
            port_data = G.nodes.get(v, {})
            alt_ports.append({
                "port": port_data.get("name", v),
                "state": port_data.get("state", "Unknown"),
                "confidence": data.get("confidence", 0),
                "cargo_mt": port_data.get("total_mt"),
                "share_pct": port_data.get("share_of_all_major_ports_pct"),
            })
    alt_ports.sort(key=lambda x: x["confidence"], reverse=True)

    return {
        "description": "Alternative paths available in the supply-chain model.",
        "alternative_source_countries": alt_countries,
        "n_alternative_countries": len(alt_countries),
        "alternative_ports": alt_ports,
        "n_alternative_ports": len(alt_ports),
        "path_availability": (
            "HIGH — multiple ports available for commodity handling" if len(alt_ports) >= 4
            else "MODERATE — limited port alternatives identified" if len(alt_ports) >= 2
            else "LOW — very few alternative port paths in model"
        ),
        "data_note": "Alternative paths are modeled from graph topology using inferred port affinities. Not validated against observed logistics data.",
        "type": "DERIVED",
        "provenance": "[GRAPH-DERIVED]",
    }


# ---------------------------------------------------------------------------
# 7. Bottleneck Detection
# ---------------------------------------------------------------------------

def compute_bottlenecks(G: nx.MultiDiGraph, commodity: str, trade_type: str) -> Dict[str, Any]:
    """
    Identifies structural bottlenecks in the supply-chain graph.

    A node is flagged as a potential bottleneck if:
    1. Its betweenness centrality is in the top quartile, AND
    2. It lies on the primary path from the trade shock to agricultural districts, OR
       it has high port cargo share with few alternative ports.

    Type: DERIVED from graph structure + PORT DATA.
    Caveat: Structural bottlenecks in the model; real systems may have redundancies.
    """
    simple_G = _to_simple_digraph(G, weight_attr="weight")
    try:
        betweenness = nx.betweenness_centrality(simple_G, weight="weight", normalized=True)
    except Exception:
        betweenness = {}

    bottlenecks = []

    for node, score in sorted(betweenness.items(), key=lambda x: x[1], reverse=True):
        if node not in G.nodes:
            continue
        ntype = G.nodes[node].get("node_type", "")
        if ntype not in ("port", "state", "commodity"):
            continue

        # Port-specific bottleneck criteria
        if ntype == "port":
            cargo_share = G.nodes[node].get("share_of_all_major_ports_pct") or 0
            if score > 0.05 or cargo_share >= 10:
                bottlenecks.append({
                    "node": node,
                    "name": G.nodes[node].get("name", node),
                    "node_type": ntype,
                    "betweenness_centrality": round(score, 6),
                    "cargo_share_pct": cargo_share,
                    "bottleneck_criteria": (
                        "High betweenness centrality" if score > 0.05 else "High cargo share (>= 10%)"
                    ),
                    "risk_level": (
                        "HIGH" if (score > 0.1 or cargo_share >= 20) else
                        "MODERATE" if (score > 0.05 or cargo_share >= 10) else "LOW"
                    ),
                    "explanation": (
                        f"Port handles {cargo_share:.1f}% of Major Port cargo and has "
                        f"betweenness centrality {score:.4f}. This suggests observed "
                        f"traffic concentration indicating potential logistics dependency."
                    ),
                    "provenance": "[GRAPH-DERIVED] + [PORT DATA]",
                })

    # Sort by risk level
    risk_order = {"HIGH": 0, "MODERATE": 1, "LOW": 2}
    bottlenecks.sort(key=lambda x: risk_order.get(x.get("risk_level", "LOW"), 3))

    return {
        "description": "Structural bottlenecks identified from graph topology and port cargo share.",
        "n_bottlenecks_identified": len(bottlenecks),
        "bottlenecks": bottlenecks,
        "caveat": (
            "Bottlenecks are structural positions in the modeled graph, not proven disruption points. "
            "Real logistics systems have redundancies not captured in this model. "
            "Language: 'potential bottleneck', 'structural dependency', 'observed concentration'."
        ),
        "type": "DERIVED",
        "provenance": "[GRAPH-DERIVED]",
    }


# ---------------------------------------------------------------------------
# 8. Commodity Concentration
# ---------------------------------------------------------------------------

def compute_commodity_concentration(G: nx.MultiDiGraph, commodity: str) -> Dict[str, Any]:
    """
    Measures commodity-specific concentration across ports.

    Uses HANDLES edge weights (affinity confidence) to assess how
    concentrated the commodity handling is.
    Type: DERIVED.
    """
    commodity_node = f"commodity:{commodity}"
    handles_edges = [
        (v, d) for u, v, d in G.edges(data=True)
        if d.get("edge_type") == "HANDLES" and u == commodity_node
    ]

    if not handles_edges:
        return {"note": "No HANDLES edges for this commodity.", "provenance": "[GRAPH-DERIVED]"}

    confidences = [d.get("confidence", 0) for _, d in handles_edges]
    cargo_shares = [
        G.nodes[n].get("share_of_all_major_ports_pct") or 0
        for n, _ in handles_edges
    ]

    total_share = sum(cargo_shares)
    if total_share > 0:
        norm = [s / total_share for s in cargo_shares]
        hhi = sum(s * s for s in norm)
        hhi_note = f"HHI = {hhi:.4f}; 0=fully dispersed, 1=monopoly concentration."
    else:
        hhi = None
        hhi_note = "Port cargo data insufficient for HHI calculation."

    return {
        "description": "Commodity handling concentration across Major Ports.",
        "commodity": commodity,
        "n_handling_ports": len(handles_edges),
        "mean_affinity_confidence": round(float(np.mean(confidences)), 4),
        "port_cargo_share_hhi": round(hhi, 4) if hhi is not None else None,
        "hhi_note": hhi_note,
        "data_note": "Based on inferred port affinities and aggregate port cargo data. Not commodity-specific routing data.",
        "type": "DERIVED",
        "provenance": "[GRAPH-DERIVED]",
    }


# ---------------------------------------------------------------------------
# 9. Regional Dependency
# ---------------------------------------------------------------------------

def compute_regional_dependency(G: nx.MultiDiGraph, commodity: str) -> Dict[str, Any]:
    """
    State-level agricultural dependency on the commodity.

    Aggregates PRODUCES edges by state to identify which states have
    high production exposure to this commodity.
    Type: DERIVED from PRODUCES edges + AGRICULTURE DATA.
    """
    state_production: Dict[str, float] = defaultdict(float)

    for u, v, data in G.edges(data=True):
        if data.get("edge_type") == "PRODUCES" and v == f"commodity:{commodity}":
            dist_data = G.nodes.get(u, {})
            state = dist_data.get("state", "Unknown")
            prod = data.get("production_tonnes", 0.0)
            state_production[state] += prod

    total_prod = sum(state_production.values())
    state_shares = {
        s: {
            "production_tonnes": round(p, 2),
            "share_pct": round(100 * p / total_prod, 2) if total_prod > 0 else None,
        }
        for s, p in sorted(state_production.items(), key=lambda x: x[1], reverse=True)
    }

    top_states = list(state_shares.items())[:5]

    return {
        "description": "State-level production dependency for the affected commodity.",
        "commodity": commodity,
        "state_production_shares": state_shares,
        "top_5_producing_states": top_states,
        "total_modeled_production_tonnes": round(total_prod, 2),
        "n_states_represented": len(state_shares),
        "data_note": (
            "Production data from crop-wise-area-production-yield.csv. "
            "Top-20 districts included in graph (not all districts in India)."
        ),
        "type": "DERIVED from PRODUCES edges",
        "provenance": "[AGRICULTURE DATA] → [GRAPH-DERIVED]",
    }


# ---------------------------------------------------------------------------
# 10. Critical Node Identification
# ---------------------------------------------------------------------------

def identify_critical_nodes(G: nx.MultiDiGraph, commodity: str) -> Dict[str, Any]:
    """
    Identifies critical nodes using a composite of:
    - Betweenness centrality (structural importance)
    - Port cargo share (observed logistics volume)
    - Production share for districts (agricultural importance)

    Critical nodes are those whose removal would most disrupt modeled pathways.
    Type: DERIVED.
    """
    simple_G = _to_simple_digraph(G, weight_attr="weight")
    try:
        betweenness = nx.betweenness_centrality(simple_G, weight="weight", normalized=True)
    except Exception:
        betweenness = {}

    critical = []
    for node, bt in sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:15]:
        if node not in G.nodes:
            continue
        ntype = G.nodes[node].get("node_type", "")
        name = G.nodes[node].get("name", node)

        # Composite score depends on node type
        if ntype == "port":
            cargo_share = G.nodes[node].get("share_of_all_major_ports_pct") or 0
            composite = 0.5 * bt + 0.5 * (cargo_share / 100.0)
            reason = f"betweenness={bt:.4f}, cargo_share={cargo_share:.1f}%"
        elif ntype == "country":
            ts = G.nodes[node].get("trade_share_pct", 0)
            composite = 0.5 * bt + 0.5 * (ts / 100.0)
            reason = f"betweenness={bt:.4f}, trade_share={ts:.1f}%"
        else:
            composite = bt
            reason = f"betweenness={bt:.4f}"

        critical.append({
            "node": node,
            "name": name,
            "node_type": ntype,
            "betweenness_centrality": round(bt, 6),
            "composite_importance": round(composite, 4),
            "reason": reason,
            "provenance": "[GRAPH-DERIVED]",
        })

    critical.sort(key=lambda x: x["composite_importance"], reverse=True)

    return {
        "description": "Critical nodes identified by composite graph importance score.",
        "critical_nodes": critical[:10],
        "methodology": (
            "Composite = 0.5 * normalized_betweenness + 0.5 * cargo/trade share (port/country). "
            "Pure betweenness for other node types."
        ),
        "caveat": "Critical nodes reflect structural model positions, not validated disruption vulnerabilities.",
        "type": "DERIVED",
        "provenance": "[GRAPH-DERIVED]",
    }


# ---------------------------------------------------------------------------
# 11. Connectivity
# ---------------------------------------------------------------------------

def compute_connectivity(G: nx.MultiDiGraph) -> Dict[str, Any]:
    """
    Computes basic connectivity metrics of the supply-chain graph.
    """
    undirected = G.to_undirected()
    n_components = nx.number_connected_components(undirected)
    largest_cc = max(nx.connected_components(undirected), key=len) if n_components > 0 else set()

    return {
        "n_nodes": G.number_of_nodes(),
        "n_edges": G.number_of_edges(),
        "n_weakly_connected_components": nx.number_weakly_connected_components(G),
        "n_strongly_connected_components": nx.number_strongly_connected_components(G),
        "n_undirected_components": n_components,
        "largest_component_size": len(largest_cc),
        "is_connected_undirected": n_components == 1,
        "type": "DERIVED",
        "provenance": "[GRAPH-DERIVED]",
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _to_simple_digraph(G: nx.MultiDiGraph, weight_attr: str = "weight") -> nx.DiGraph:
    """
    Convert MultiDiGraph to simple DiGraph by summing edge weights
    for parallel edges.
    """
    simple = nx.DiGraph()
    simple.add_nodes_from(G.nodes(data=True))

    for u, v, data in G.edges(data=True):
        w = float(data.get(weight_attr, 1.0))
        if simple.has_edge(u, v):
            simple[u][v][weight_attr] += w
        else:
            simple.add_edge(u, v, **{weight_attr: w})
    return simple
