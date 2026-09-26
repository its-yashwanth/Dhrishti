"""
Quick demo: run Supply-Chain Agent + Vulnerability Agent and print output.

Usage:
    python scripts/demo_new_agents.py
    python scripts/demo_new_agents.py --commodity Rice --hs4 1006 --trade_type Import --country THAILAND
    python scripts/demo_new_agents.py --commodity Cotton --hs4 None --trade_type Export --country BANGLADESH
"""

import sys
import json
import argparse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from agents.supply_chain_agent import SupplyChainAgent
from agents.vulnerability_agent import VulnerabilityAgent


import logging
logging.basicConfig(level=logging.WARNING)
for logger_name in (
    "agents.supply_chain_agent",
    "agents.vulnerability_agent",
    "graph.builders",
    "graph.analytics",
    "graph.propagation",
    "scripts.validate_vulnerability_data",
):
    logging.getLogger(logger_name).setLevel(logging.WARNING)


def hr(char="=", width=72):
    print(char * width)


def run_demo(commodity: str, hs4, trade_type: str, country: str,
             shock_intensity: float = 1.5, trade_share: float = 10.0):

    if hs4 and str(hs4).lower() not in ("none", "0", ""):
        hs4 = int(hs4)
    else:
        hs4 = None

    print()
    hr()
    print(f"  DRISHTI — DECISION-SUPPORT DEMO")
    print(f"  Commodity : {commodity}  |  HS4: {hs4}  |  Flow: {trade_type}")
    print(f"  Country   : {country}  |  Shock: {shock_intensity}x  |  Trade share: {trade_share}%")
    hr()

    # Ensure Windows console encoding compatibility
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    # -------------------------------------------------------
    # 1. SUPPLY-CHAIN AGENT
    # -------------------------------------------------------
    print("\n[1/2] Running Supply-Chain Agent ...\n")
    sc_agent = SupplyChainAgent()
    sc = sc_agent.analyse(
        commodity=commodity,
        hs4=hs4 or 1001,
        trade_type=trade_type,
        event_country=country,
        shock_intensity=shock_intensity,
        trade_share=trade_share,
    )
    print(sc_agent.format_report(sc))

    # -------------------------------------------------------
    # 2. VULNERABILITY AGENT
    # -------------------------------------------------------
    print("\n[2/2] Running Vulnerability Agent ...\n")
    vu_agent = VulnerabilityAgent()
    vu = vu_agent.analyse(
        commodity=commodity,
        hs4=hs4 or 1001,
        trade_type=trade_type,
        supply_chain_output=sc,
    )
    print(vu_agent.format_report(vu))

    print()
    hr()
    print("  Drishti Decision-Support Demo Complete.")
    hr()
    print()


def main():
    parser = argparse.ArgumentParser(description="Demo: Supply-Chain + Vulnerability Agents")
    parser.add_argument("--commodity",       default="Wheat",   help="Commodity name (default: Wheat)")
    parser.add_argument("--hs4",             default="1001",    help="HS4 code (default: 1001)")
    parser.add_argument("--trade_type",      default="Import",  help="Import or Export (default: Import)")
    parser.add_argument("--country",         default="RUSSIA",  help="Partner country (default: RUSSIA)")
    parser.add_argument("--shock_intensity", default=1.5,       type=float, help="Shock intensity (default: 1.5)")
    parser.add_argument("--trade_share",     default=5.0,       type=float, help="Trade share %% (default: 5.0)")
    args = parser.parse_args()

    run_demo(
        commodity=args.commodity,
        hs4=args.hs4,
        trade_type=args.trade_type,
        country=args.country,
        shock_intensity=args.shock_intensity,
        trade_share=args.trade_share,
    )


if __name__ == "__main__":
    main()
