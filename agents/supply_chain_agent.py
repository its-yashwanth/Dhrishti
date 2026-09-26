"""
Drishti Supply-Chain Agent (Graph-Based)
==========================================
Upgraded Supply-Chain Agent using a heterogeneous, weighted, directed
MultiDiGraph (NetworkX) to model relationships among geopolitical actors,
commodities, Indian Major Ports, states, and agricultural districts.

Research Contribution
---------------------
A heterogeneous, weighted, directed supply-chain graph models relationships
among geopolitical actors, commodities, Indian ports, states, districts and
agricultural production, enabling dependency, connectivity, bottleneck and
scenario shock-propagation analysis.

Responsibility Boundaries
--------------------------
This agent is responsible for:
  - Supply-chain network construction
  - Trade/port/logistics dependency analysis
  - Graph construction and analytics
  - Scenario exposure propagation
  - Bottleneck and alternative path identification

This agent does NOT:
  - Replicate ML Models A-D functionality
  - Replace the Event Intelligence Agent
  - Provide agricultural vulnerability scores (that is VulnerabilityAgent)
  - Make causal predictions about disruption

Integration
-----------
Receives from Orchestrator:
  commodity, hs4, trade_type, event_country, shock_intensity,
  trade_share, ml_predictions (optional)

Returns structured supply_chain_analysis dict consumed by:
  - Orchestrator (for final result assembly)
  - Dashboard visualization
  - Mitigation Agent (context enrichment)

Provenance tags:
  [USER / CLI PARAMETER] — inputs from user
  [PORT DATA]            — port_statistics.csv (MoPSW)
  [AGRICULTURE DATA]     — crop-wise-area-production-yield.csv
  [GRAPH-DERIVED]        — computed from graph structure
  [RULE-BASED OUTPUT]    — rule-based inferences
  [ML MODEL OUTPUT]      — from existing ML cascade
"""

import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from graph.builders import SupplyChainGraphBuilder, PORT_COMMODITY_AFFINITY, PORT_STATE_MAP
from graph.analytics import compute_all_analytics
from graph.propagation import propagate_shock
from agents.crop_commodity_mapping import resolve_crop

log = logging.getLogger(__name__)

# Singleton graph builder (data loaded once)
_BUILDER: Optional[SupplyChainGraphBuilder] = None


def _get_builder() -> SupplyChainGraphBuilder:
    global _BUILDER
    if _BUILDER is None:
        _BUILDER = SupplyChainGraphBuilder()
    return _BUILDER


class SupplyChainAgent:
    """
    Graph-based Supply-Chain Agent for Drishti.

    Builds a heterogeneous, weighted, directed MultiDiGraph per scenario
    and computes dependency, bottleneck, and propagation analytics.
    """

    def __init__(self):
        self._builder = _get_builder()

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
        Run supply-chain analysis for a given trade shock scenario.

        Parameters
        ----------
        commodity       : Commodity name (e.g., 'Wheat', 'Rice')
        hs4             : HS4 tariff code
        trade_type      : 'Import' or 'Export'
        event_country   : Partner country name (UPPERCASE)
        shock_direction : Direction of shock (for context only)
        shock_intensity : Shock multiplier (e.g. 1.5 = 50% stronger than baseline)
        trade_share     : Partner's share of India's commodity trade (%)
        ml_predictions  : Optional ML cascade predictions (for context)

        Returns
        -------
        dict with supply_chain_analysis key
        """
        effective_shock = round(shock_intensity * (trade_share / 100.0), 6)
        comm_lower = commodity.strip().lower()

        # Step 1: Build the scenario graph
        try:
            G = self._builder.build_scenario_graph(
                commodity=commodity,
                hs4=hs4,
                trade_type=trade_type,
                event_country=event_country,
                shock_intensity=shock_intensity,
                trade_share=trade_share,
                ml_predictions=ml_predictions,
            )
        except Exception as e:
            log.error("SupplyChainAgent: graph build failed: %s", e)
            return self._error_output(commodity, hs4, trade_type, event_country,
                                       effective_shock, str(e))

        # Step 2: Compute analytics
        try:
            analytics = compute_all_analytics(
                G, commodity=commodity,
                trade_type=trade_type, event_country=event_country,
            )
        except Exception as e:
            log.warning("SupplyChainAgent: analytics failed: %s", e)
            analytics = {"error": str(e)}

        # Step 3: Shock propagation
        try:
            propagation = propagate_shock(
                G,
                commodity=commodity,
                trade_type=trade_type,
                event_country=event_country,
                shock_intensity=shock_intensity,
                trade_share=trade_share,
            )
        except Exception as e:
            log.warning("SupplyChainAgent: propagation failed: %s", e)
            propagation = {"error": str(e)}

        # Step 4: Graph serialization (for dashboard/RAG)
        graph_dict = self._builder.graph_to_dict(G)

        # Step 5: Build structured output
        trade_dep = analytics.get("trade_dependency", {})
        port_dep = analytics.get("port_dependency", {})
        if "port_concentration_hhi" in port_dep and "port_cargo_hhi" not in port_dep:
            port_dep["port_cargo_hhi"] = port_dep["port_concentration_hhi"]
        bottleneck = analytics.get("bottleneck_analysis", {})
        alt_paths = analytics.get("alternative_paths", {})
        regional = analytics.get("regional_dependency", {})
        critical = analytics.get("critical_nodes", {})
        betweenness = analytics.get("betweenness_centrality", {})

        # ML context extraction
        ml_context = self._extract_ml_context(ml_predictions, effective_shock, trade_share)

        # Risk indicators (combined graph + rule-based + ML)
        risk_indicators = self._compute_risk_indicators(
            trade_share, effective_shock, trade_dep, port_dep,
            bottleneck, alt_paths, ml_predictions
        )

        # Summary scenario exposure
        prop_summary = propagation.get("propagation_summary", {}) if isinstance(propagation, dict) else {}

        # Direction string
        if trade_type.capitalize() == "Import":
            trade_direction = f"India's imports from {event_country}"
            exposure_type = "import_exposure"
        else:
            trade_direction = f"India's exports to {event_country}"
            exposure_type = "export_exposure"

        alt_ports_list = alt_paths.get("alternative_ports", [])
        network_resilience = {
            "modeled_alternative_ports": alt_ports_list,
            "n_alternative_ports": len(alt_ports_list),
            "path_availability": alt_paths.get("path_availability", "UNKNOWN"),
            "container_dependency": port_dep.get("container_dependency", "N/A"),
            "alternative_handling_info": alt_paths.get("description", ""),
            "note": "Modeled alternative handling ports derived from graph topology using inferred port affinities. Commodity routing is inferred, not observed.",
            "provenance": "[GRAPH-DERIVED]",
        }

        result = {
            "supply_chain_analysis": {
                # Backward-compatibility flat aliases
                "commodity": commodity,
                "hs4": hs4,
                "trade_type": trade_type,
                "trade_direction": trade_direction,
                "affected_country": event_country,
                "effective_shock": effective_shock,
                "exposure_type": exposure_type,
                "relevant_ports": port_dep.get("relevant_ports", []),
                "port_cargo_context": port_dep.get("relevant_ports", []),
                "commodity_port_context": port_dep.get("commodity_cargo_context", []),
                "container_dependency": port_dep.get("container_dependency", "N/A"),
                "potential_bottlenecks": bottleneck.get("bottleneck_ports", []),

                "scenario": {
                    "commodity": commodity,
                    "hs4": hs4,
                    "trade_type": trade_type,
                    "affected_country": event_country,
                    "shock_direction": shock_direction,
                    "shock_intensity": shock_intensity,
                    "trade_share_pct": trade_share,
                    "effective_shock": effective_shock,
                    "trade_direction": trade_direction,
                    "exposure_type": exposure_type,
                },
                "graph_summary": {
                    "n_nodes": G.number_of_nodes(),
                    "n_edges": G.number_of_edges(),
                    "node_types": list({G.nodes[n]["node_type"] for n in G.nodes}),
                    "edge_types": list({G.edges[e]["edge_type"] for e in G.edges}),
                },
                "graph_nodes": graph_dict["nodes"],
                "graph_edges": graph_dict["edges"],
                "trade_dependency": trade_dep,
                "port_dependency": port_dep,
                "critical_ports": self._extract_critical_ports(critical, bottleneck),
                "bottleneck_analysis": bottleneck,
                "alternative_paths": alt_paths,
                "network_resilience": network_resilience,
                "regional_dependency": regional,
                "propagation_paths": propagation,
                "network_metrics": {
                    "node_strength": analytics.get("node_strength", {}),
                    "betweenness_centrality": betweenness,
                    "degree_analysis": analytics.get("degree_analysis", {}),
                    "connectivity": analytics.get("connectivity", {}),
                    "commodity_concentration": analytics.get("commodity_concentration", {}),
                    "critical_nodes": critical,
                },
                "scenario_exposure": {
                    "effective_shock": effective_shock,
                    "max_port_exposure": prop_summary.get("max_port_exposure"),
                    "max_state_exposure": prop_summary.get("max_state_exposure"),
                    "max_district_exposure": prop_summary.get("max_district_exposure"),
                    "n_ports_in_propagation": prop_summary.get("n_ports_in_propagation"),
                    "n_states_in_propagation": prop_summary.get("n_states_in_propagation"),
                    "n_districts_in_propagation": prop_summary.get("n_districts_in_propagation"),
                    "top_exposed_districts": propagation.get("top_exposed_districts", []) if isinstance(propagation, dict) else [],
                    "exposed_states": propagation.get("exposed_states", []) if isinstance(propagation, dict) else [],
                    "disclaimer": propagation.get("research_disclaimer", "") if isinstance(propagation, dict) else "",
                },
                "risk_indicators": risk_indicators,
                "ml_cascade_context": ml_context,
                "confidence": self._compute_confidence(trade_share, port_dep, analytics),
                "limitations": self._standard_limitations(commodity, trade_share),
                "provenance_tags": {
                    "graph_structure": "[GRAPH-DERIVED] from NetworkX MultiDiGraph",
                    "port_cargo": "[PORT DATA] Ministry of Ports, Shipping and Waterways",
                    "port_affinity": "[RULE-BASED OUTPUT] inferred_affinity from port specialisation",
                    "trade_relationship": "[USER / CLI PARAMETER]",
                    "agricultural_production": "[AGRICULTURE DATA] crop-wise-area-production-yield.csv",
                    "risk_indicators": "[RULE-BASED OUTPUT] + [GRAPH-DERIVED]",
                    "ml_context": "[ML MODEL OUTPUT]" if ml_predictions else "N/A",
                    "propagation": "[GRAPH-DERIVED]",
                },
            },
            "provenance": [
                {
                    "source_type": "[PORT DATA]",
                    "dataset": "port_statistics.csv",
                    "origin": "Ministry of Ports, Shipping and Waterways (MoPSW)",
                    "years": "2023-24, 2024-25",
                },
                {
                    "source_type": "[AGRICULTURE DATA]",
                    "dataset": "crop-wise-area-production-yield.csv",
                    "years": "2017-18 to 2022-23",
                },
                {
                    "source_type": "[GRAPH-DERIVED]",
                    "description": "NetworkX MultiDiGraph analytics and propagation",
                    "graph_type": "Heterogeneous, weighted, directed MultiDiGraph",
                },
            ],
        }

        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _extract_critical_ports(self, critical: Dict, bottleneck: Dict) -> List[Dict]:
        """Combine critical node analysis and bottleneck analysis into a clean port list."""
        critical_ports = []
        seen = set()

        # From bottleneck analysis
        for b in bottleneck.get("bottlenecks", []):
            name = b.get("name", "")
            if name not in seen:
                seen.add(name)
                critical_ports.append({
                    "port": name,
                    "risk_level": b.get("risk_level", "MODERATE"),
                    "betweenness_centrality": b.get("betweenness_centrality"),
                    "cargo_share_pct": b.get("cargo_share_pct"),
                    "identification_basis": "bottleneck_analysis",
                    "note": b.get("explanation", ""),
                    "provenance": "[GRAPH-DERIVED] + [PORT DATA]",
                })

        # From critical node analysis
        for cn in critical.get("critical_nodes", []):
            if cn.get("node_type") == "port":
                name = cn.get("name", "")
                if name not in seen:
                    seen.add(name)
                    critical_ports.append({
                        "port": name,
                        "risk_level": "MODERATE",
                        "betweenness_centrality": cn.get("betweenness_centrality"),
                        "composite_importance": cn.get("composite_importance"),
                        "identification_basis": "critical_node_analysis",
                        "provenance": "[GRAPH-DERIVED]",
                    })

        return critical_ports

    def _compute_risk_indicators(
        self,
        trade_share: float,
        effective_shock: float,
        trade_dep: Dict,
        port_dep: Dict,
        bottleneck: Dict,
        alt_paths: Dict,
        ml_predictions: Optional[Dict],
    ) -> List[Dict]:
        indicators = []

        # 1. Trade dependency
        dep_level = trade_dep.get("dependency_level", "LOW")
        indicators.append({
            "indicator": "Trade Share Exposure",
            "level": dep_level,
            "value": trade_share,
            "note": f"Trade Share Exposure: {trade_share:.1f}%. Partner-country share of the relevant trade exposure.",
            "provenance": "[USER / CLI PARAMETER] → [GRAPH-DERIVED]",
        })

        # 2. Effective shock
        eff_level = "HIGH" if effective_shock >= 0.15 else "MODERATE" if effective_shock >= 0.05 else "LOW"
        indicators.append({
            "indicator": "Effective Shock Exposure",
            "level": eff_level,
            "value": effective_shock,
            "note": (
                f"Effective shock = {effective_shock:.4f} "
                f"(shock_intensity × trade_share%). Higher values indicate greater exposure."
            ),
            "provenance": "[USER / CLI PARAMETER] → [GRAPH-DERIVED]",
        })

        # 3. Port bottleneck
        n_bottlenecks = bottleneck.get("n_bottlenecks_identified", 0)
        if n_bottlenecks > 0:
            top_bottleneck = bottleneck.get("bottlenecks", [{}])[0]
            bt_level = top_bottleneck.get("risk_level", "MODERATE")
            indicators.append({
                "indicator": "Port Bottleneck Exposure",
                "level": bt_level,
                "value": n_bottlenecks,
                "note": f"{n_bottlenecks} potential port bottleneck(s) identified. Top: {top_bottleneck.get('name', 'N/A')} ({bt_level}).",
                "provenance": "[GRAPH-DERIVED] + [PORT DATA]",
            })

        # 4. Port HHI concentration (structural metric; not labeled as arbitrary risk)
        hhi = port_dep.get("port_concentration_hhi")
        if hhi is not None:
            indicators.append({
                "indicator": "Port Cargo Concentration (HHI)",
                "level": "INFO",
                "value": round(hhi, 4),
                "note": (
                    f"Port cargo HHI = {hhi:.4f}. "
                    "0 = distributed across ports, 1 = concentrated in a single port."
                ),
                "provenance": "[GRAPH-DERIVED] + [PORT DATA]",
            })

        # 6. ML signals
        if ml_predictions:
            trade_return = ml_predictions.get("trade", {}).get("Trade_Return_1M_Pred")
            prod_growth = ml_predictions.get("agriculture", {}).get("Production_Growth_Pred")
            prod_risk = ml_predictions.get("agriculture", {}).get("Production_Risk", "")

            if trade_return is not None:
                ml_trade_level = "HIGH" if abs(trade_return) >= 3 else "MODERATE" if abs(trade_return) >= 1 else "LOW"
                indicators.append({
                    "indicator": "ML Model A — Trade Signal",
                    "level": ml_trade_level,
                    "value": f"{trade_return:+.2f}%",
                    "note": f"Model A projects {trade_return:+.2f}% trade return. Negative = contraction.",
                    "provenance": "[ML MODEL OUTPUT]",
                })

            if prod_growth is not None:
                ml_prod_level = str(prod_risk).upper() if prod_risk else ("HIGH" if prod_growth < -2 else "MODERATE")
                indicators.append({
                    "indicator": "ML Model B — Production Signal",
                    "level": ml_prod_level,
                    "value": f"{prod_growth:+.2f}% | Risk: {prod_risk}",
                    "note": f"Model B national production growth: {prod_growth:+.2f}%, Risk tier: {prod_risk}",
                    "provenance": "[ML MODEL OUTPUT]",
                })

        return indicators

    def _extract_ml_context(
        self, ml_predictions: Optional[Dict], effective_shock: float, trade_share: float
    ) -> Dict[str, Any]:
        if not ml_predictions:
            return {"note": "No ML predictions provided.", "provenance": "N/A"}

        return {
            "trade_return_1m": ml_predictions.get("trade", {}).get("Trade_Return_1M_Pred"),
            "production_growth_pct": ml_predictions.get("agriculture", {}).get("Production_Growth_Pred"),
            "production_risk": ml_predictions.get("agriculture", {}).get("Production_Risk"),
            "price_return_1m": ml_predictions.get("price", {}).get("Price_Return_1M_Pred"),
            "agri_gva_growth": ml_predictions.get("economy", {}).get("Agri_GVA_Growth_Pred"),
            "inflation_change": ml_predictions.get("economy", {}).get("Inflation_Change_Pred"),
            "note": (
                "ML cascade predictions provide national-level quantitative forecasts. "
                "Supply-chain graph provides logistics and port dependency context. "
                "These are complementary — ML output is statistical, graph output is structural."
            ),
            "provenance": "[ML MODEL OUTPUT]",
        }

    def _compute_confidence(
        self, trade_share: float, port_dep: Dict, analytics: Dict
    ) -> Dict[str, Any]:
        """
        Structured confidence assessment for the supply-chain analysis.
        Not a probability — a data-quality / reliability assessment.
        """
        issues = []
        if trade_share == 5.0:
            issues.append("trade_share uses default value (5.0%); actual value may differ")

        n_ports_no_data = sum(
            1 for p in port_dep.get("port_dependencies", [])
            if p.get("data_quality") == "NO_DATA"
        )
        if n_ports_no_data > 0:
            issues.append(f"{n_ports_no_data} relevant ports have no cargo data in trusted dataset")

        all_inferred = all(
            p.get("relationship_type") == "inferred_affinity"
            for p in port_dep.get("port_dependencies", [])
        )
        if all_inferred:
            issues.append("All commodity-port relationships are inferred affinity (not observed routes)")

        overall = "MEDIUM" if not issues else "LOW" if len(issues) >= 2 else "MEDIUM-LOW"

        return {
            "overall": overall,
            "issues": issues,
            "note": (
                "Confidence reflects data quality and model assumptions, "
                "NOT a statistical probability of disruption."
            ),
        }

    def _standard_limitations(self, commodity: str, trade_share: float) -> List[str]:
        return [
            "Supply-chain analysis is based on aggregate Major Port statistics from MoPSW (2023-24, 2024-25).",
            "Port affinity mappings are based on publicly known port specialisations, not observed commodity-specific trade-lane data.",
            "The analysis indicates exposure and dependency patterns — not causal responsibility for disruption.",
            "PORT_STATE edges represent geographic port location, NOT cargo destination routing.",
            "HANDLES edges are inferred affinities; confidence values reflect model assumptions.",
            "Non-major ports (handles ~30% of India's sea cargo) are not included in this analysis.",
            "Agricultural production data covers 2017-18 to 2022-23; more recent seasons not included.",
            f"Trade share ({trade_share}%) is user-specified; actual bilateral trade share may differ.",
            "Graph-derived metrics (betweenness, centrality) reflect the modeled topology, not observed logistics.",
            "Shock propagation uses decay parameters (HANDLES_DECAY=0.85, PORT_STATE_DECAY=0.70) based on modeling assumptions.",
        ]

    def _error_output(
        self, commodity: str, hs4: int, trade_type: str, event_country: str,
        effective_shock: float, error: str
    ) -> Dict[str, Any]:
        return {
            "supply_chain_analysis": {
                "scenario": {
                    "commodity": commodity, "hs4": hs4,
                    "trade_type": trade_type, "affected_country": event_country,
                    "effective_shock": effective_shock,
                },
                "error": error,
                "graph_summary": {},
                "graph_nodes": [], "graph_edges": [],
                "trade_dependency": {}, "port_dependency": {},
                "critical_ports": [], "bottleneck_analysis": {},
                "alternative_paths": {}, "regional_dependency": {},
                "propagation_paths": {}, "network_metrics": {},
                "scenario_exposure": {}, "risk_indicators": [],
                "ml_cascade_context": {}, "confidence": {},
                "limitations": [error, "Graph construction failed."],
                "provenance_tags": {},
            },
            "provenance": [],
        }

    @staticmethod
    def format_report(analysis_result: Dict[str, Any]) -> str:
        """
        Formats SupplyChainAgent analysis into a clean, human-readable terminal report.
        """
        sca = analysis_result.get("supply_chain_analysis", analysis_result)
        scenario = sca.get("scenario", {})
        lines = []
        hr = "=" * 60

        lines.append(hr)
        lines.append("SUPPLY CHAIN ANALYSIS")
        lines.append(hr)
        lines.append("")

        # SCENARIO
        lines.append("SCENARIO")
        lines.append("--------")
        lines.append(f"Commodity        : {scenario.get('commodity', sca.get('commodity', 'N/A'))}")
        lines.append(f"HS4              : {scenario.get('hs4', sca.get('hs4', 'N/A'))}")
        lines.append(f"Trade Type       : {scenario.get('trade_type', sca.get('trade_type', 'N/A'))}")
        lines.append(f"Trade Direction  : {scenario.get('trade_direction', sca.get('trade_direction', 'N/A'))}")
        lines.append(f"Affected Country : {scenario.get('affected_country', sca.get('affected_country', 'N/A'))}")
        eff_shock = scenario.get('effective_shock', sca.get('effective_shock'))
        eff_shock_str = f"{eff_shock:.4f}" if eff_shock is not None else "Unavailable"
        lines.append(f"Effective Shock  : {eff_shock_str}")
        lines.append("")

        # TRADE EXPOSURE
        lines.append("TRADE EXPOSURE")
        lines.append("--------------")
        ts = scenario.get('trade_share_pct', sca.get('trade_share_pct'))
        ts_str = f"{ts:.2f}%" if ts is not None else "Unavailable"
        lines.append(f"Trade Share Exposure    : {ts_str}")
        lines.append("  Partner-country share of the relevant trade exposure.")
        lines.append(f"Effective Shock Exposure: {eff_shock_str}")
        lines.append("")

        # PORT NETWORK
        lines.append("PORT NETWORK")
        lines.append("------------")
        port_dep = sca.get("port_dependency", {})
        relevant_ports = port_dep.get("relevant_ports", sca.get("relevant_ports", []))
        if relevant_ports:
            lines.append("Relevant Ports:")
            for p in relevant_ports:
                p_name = p.get("port", "Unknown Port")
                state = p.get("state", "")
                cargo = p.get("cargo_mt")
                share = p.get("share_pct")
                extra = []
                if state:
                    extra.append(state)
                if cargo is not None:
                    extra.append(f"Cargo: {cargo:.1f} MT")
                if share is not None:
                    extra.append(f"Share: {share:.1f}%")
                detail = f" - {', '.join(extra)}" if extra else ""
                lines.append(f"  * {p_name}{detail}")
        else:
            lines.append("  No relevant handling ports identified.")
        lines.append("")

        # RISK INDICATORS
        lines.append("RISK INDICATORS")
        lines.append("---------------")
        indicators = sca.get("risk_indicators", [])
        hhi_val = None
        for ind in indicators:
            name = ind.get("indicator", "")
            lvl = ind.get("level", "INFO")
            val = ind.get("value", "")
            note = ind.get("note", "")
            if "HHI" in name:
                hhi_val = val
                continue
            lines.append(f"[{lvl:<8s}] {name}")
            if note:
                lines.append(f"           {note}")
            lines.append("")

        if hhi_val is not None:
            lines.append(f"Port Cargo Concentration (HHI): {hhi_val}")
            lines.append("  0 = distributed across ports")
            lines.append("  1 = concentrated in a single port")
            lines.append("")

        # NETWORK RESILIENCE
        lines.append("NETWORK RESILIENCE")
        lines.append("------------------")
        alt_paths = sca.get("alternative_paths", {})
        alt_ports = alt_paths.get("alternative_ports", [])
        lines.append(f"Modeled Alternative Handling Ports: {len(alt_ports)}")
        if alt_ports:
            lines.append("")
            for idx, ap in enumerate(alt_ports, 1):
                p_name = ap.get("port", "Unknown")
                state = ap.get("state", "Unknown")
                conf = ap.get("confidence")
                cargo = ap.get("cargo_mt")
                share = ap.get("share_pct")
                lines.append(f"  {idx}. {p_name} - {state}")
                if conf is not None:
                    lines.append(f"     Inferred affinity confidence: {conf:.2f}")
                cargo_str = f"{cargo:.1f} MT" if cargo is not None else "Unavailable"
                share_str = f"{share:.1f}%" if share is not None else "Unavailable"
                lines.append(f"     Cargo context: {cargo_str}  |  Share: {share_str}")
                lines.append("")
        else:
            lines.append("  No modeled alternative handling ports identified.")
            lines.append("")

        container_dep = sca.get("network_resilience", {}).get(
            "container_dependency", port_dep.get("container_dependency")
        )
        if container_dep and container_dep != "N/A":
            lines.append(f"Container Dependency: {container_dep}")
            lines.append("")

        # LIMITATIONS
        lines.append("LIMITATIONS")
        lines.append("-----------")
        limitations = sca.get("limitations", [])
        if limitations:
            for lim in limitations[:4]:
                lines.append(f"* {lim}")
        lines.append("")

        # PROVENANCE
        lines.append("PROVENANCE")
        lines.append("----------")
        prov_tags = sca.get("provenance_tags", {})
        if prov_tags:
            for k, v in prov_tags.items():
                clean_k = k.replace("_", " ").title()
                lines.append(f"* {clean_k:<24s}: {v}")
        lines.append("")
        lines.append(hr)

        return "\n".join(lines)

