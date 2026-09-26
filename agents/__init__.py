"""Drishti Agents Package."""
from agents.event_intelligence_agent import EventIntelligenceAgent
from agents.impact_interpretation_agent import ImpactInterpretationAgent
from agents.stakeholder_advisory_agent import StakeholderAdvisoryAgent
from agents.mitigation_action_agent import MitigationActionAgent
from agents.orchestrator import DrishtiAgentOrchestrator
from agents.crop_commodity_mapping import resolve_crop, get_crop_names_for_commodity

# Lazy-import graph-based agents to avoid circular imports
# (graph.builders imports agents.crop_commodity_mapping, which is fine;
#  agents.supply_chain_agent imports graph.builders → must NOT be triggered
#  at package-init time)
def _lazy():
    from agents.supply_chain_agent import SupplyChainAgent
    from agents.vulnerability_agent import VulnerabilityAgent
    return SupplyChainAgent, VulnerabilityAgent

__all__ = [
    "EventIntelligenceAgent",
    "ImpactInterpretationAgent",
    "StakeholderAdvisoryAgent",
    "MitigationActionAgent",
    "DrishtiAgentOrchestrator",
    "resolve_crop",
    "get_crop_names_for_commodity",
]
