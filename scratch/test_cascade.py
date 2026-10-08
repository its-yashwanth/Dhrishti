import sys
from pathlib import Path
BASE_DIR = Path('.').resolve()
sys.path.insert(0, str(BASE_DIR))

from drishti_mcp.tools.ml_cascade_tool import run_drishti_ml_cascade

scenarios = [
    {"name": "Wheat -> Russia (Export)", "country": "RUSSIA", "commodity": "Wheat", "hs4": 1001, "trade_type": "Export", "shock_intensity": 1.5, "trade_share": 5.0},
    {"name": "Wheat -> Russia (Import)", "country": "RUSSIA", "commodity": "Wheat", "hs4": 1001, "trade_type": "Import", "shock_intensity": 1.8, "trade_share": 5.0},
    {"name": "Cotton -> Bangladesh (Export)", "country": "BANGLADESH", "commodity": "Cotton", "hs4": 5201, "trade_type": "Export", "shock_intensity": 1.2, "trade_share": 14.5},
    {"name": "Wheat -> Bangladesh (Export)", "country": "BANGLADESH", "commodity": "Wheat", "hs4": 1001, "trade_type": "Export", "shock_intensity": 1.2, "trade_share": 8.0},
]

for sc in scenarios:
    out = run_drishti_ml_cascade(
        country=sc["country"],
        trade_type=sc["trade_type"],
        hs4=sc["hs4"],
        commodity=sc["commodity"],
        shock_intensity=sc["shock_intensity"],
        trade_share=sc["trade_share"]
    )
    preds = out["predictions"]
    print(f"\n=== {sc['name']} ===")
    print(f"Model A (Trade Return 1M): {preds['trade']['Trade_Return_1M_Pred']:.2f}%")
    print(f"Model B (Prod Growth):     {preds['agriculture']['Production_Growth_Pred']:.2f}%, Risk: {preds['agriculture']['Production_Risk']}")
    print(f"Model C (Price Return 1M): {preds['price']['Price_Return_1M_Pred']}")
    print(f"Model D (Agri GVA):        {preds['economy']['Agri_GVA_Growth_Pred']:.2f}%, Inflation: {preds['economy']['Inflation_Change_Pred']:.2f} pp")
