"""
Drishti — Centralized Commodity-to-Crop Name Mapping
=====================================================
Maps Drishti commodity names (and COMMODITY_TO_HS4 keys) to the
exact crop_name values present in the agricultural vulnerability dataset
(data/vulnerability/raw/crop-wise-area-production-yield.csv).

Rules
-----
1.  Mappings are explicit and documented — no fuzzy matching.
2.  If no reliable match exists, the value is None (returned as
    "no reliable crop match" by callers).
3.  One commodity may map to multiple crop_name values (e.g., 'Pulses'
    covers Gram, Arhar/Tur, Moong, Urad, Masoor).
4.  All crop_name values are the exact strings from the dataset.
5.  Do NOT collapse dissimilar crops into one entry.

Usage
-----
from agents.crop_commodity_mapping import (
    get_crop_names_for_commodity,
    get_commodity_for_hs4,
    COMMODITY_TO_CROPS,
)
"""

from typing import List, Optional, Dict

# ---------------------------------------------------------------------------
# Commodity → list of exact crop_name strings in the vulnerability dataset
# ---------------------------------------------------------------------------
# Keys: lowercase commodity names (matching COMMODITY_TO_HS4 in config/settings.py)
# Values: list of exact crop_name strings as they appear in the CSV

COMMODITY_TO_CROPS: Dict[str, List[str]] = {
    # Cereals
    "rice":       ["Rice"],
    "wheat":      ["Wheat"],
    "maize":      ["Maize"],
    "corn":       ["Maize"],
    "barley":     ["Barley"],
    "jowar":      ["Jowar"],
    "sorghum":    ["Jowar"],
    "bajra":      ["Bajra"],
    "millet":     ["Bajra"],

    # Pulses
    "gram":          ["Gram"],
    "chickpea":      ["Gram"],
    "pulse":         ["Gram", "Arhar/Tur", "Moong(Green Gram)", "Urad", "Masoor"],
    "pulses":        ["Gram", "Arhar/Tur", "Moong(Green Gram)", "Urad", "Masoor"],
    "lentil":        ["Masoor"],
    "lentils":       ["Masoor"],

    # Vegetables
    "onion":     ["Onion"],
    "onions":    ["Onion"],
    "potato":    ["Potato"],
    "potatoes":  ["Potato"],
    "garlic":    ["Garlic"],

    # Oilseeds
    "soybean":      ["Soyabean"],
    "soyabean":     ["Soyabean"],
    "groundnut":    ["Groundnut"],
    "peanut":       ["Groundnut"],
    "sunflower":    ["Sunflower"],
    "palm oil":     None,   # No domestic crop in dataset (imported commodity)
    "palmoil":      None,
    "rapeseed":     ["Rapeseed &Mustard"],
    "mustard":      ["Rapeseed &Mustard"],
    "castor":       ["Castor Seed"],
    "sesamum":      ["Sesamum"],
    "linseed":      ["Linseed"],

    # Fibres / Industrial
    "cotton":    ["Cotton(Lint)"],
    "jute":      ["Jute"],

    # Sugars
    "sugar":      ["Sugarcane"],
    "sugarcane":  ["Sugarcane"],

    # Fruits
    "banana":    ["Banana"],
    "cashew":    ["Cashewnut"],
    "cashewnut": ["Cashewnut"],
    "coconut":   ["Coconut"],

    # Spices
    "pepper":     ["Black Pepper"],
    "chilli":     ["Dry Chillies"],
    "chillies":   ["Dry Chillies"],
    "turmeric":   ["Turmeric"],
    "ginger":     ["Ginger"],
    "coriander":  ["Coriander"],

    # Beverages
    "tea":     None,   # Not in district-level crop dataset
    "coffee":  None,   # Not in district-level crop dataset
}

# ---------------------------------------------------------------------------
# HS4 → commodity name (canonical Drishti lowercase key)
# ---------------------------------------------------------------------------
HS4_TO_COMMODITY: Dict[int, str] = {
    1006: "rice",
    1001: "wheat",
    1005: "maize",
    1003: "barley",
    1007: "jowar",
    1008: "bajra",
    713:  "pulses",
    703:  "onion",
    701:  "potato",
    1201: "soybean",
    1202: "groundnut",
    1511: "palm oil",
    1206: "sunflower",
    1701: "sugarcane",
    803:  "banana",
    801:  "cashewnut",
    902:  "tea",
    901:  "coffee",
    904:  "pepper",
    910:  "turmeric",
    1204: "linseed",
    1205: "rapeseed",
    1207: "sesamum",
    909:  "coriander",
}


def get_crop_names_for_commodity(commodity: str) -> Optional[List[str]]:
    """
    Given a commodity name (any case), return the list of matching
    crop_name strings from the vulnerability dataset.

    Returns None if no reliable match exists.
    Returns a list of crop names if matches exist.
    """
    key = commodity.strip().lower()
    if key in COMMODITY_TO_CROPS:
        return COMMODITY_TO_CROPS[key]

    # Partial match fallback (explicit whitelist only — no fuzzy)
    for k, v in COMMODITY_TO_CROPS.items():
        if k in key or key in k:
            return v

    return None


def get_commodity_for_hs4(hs4: int) -> Optional[str]:
    """Return the canonical lowercase commodity key for an HS4 code."""
    return HS4_TO_COMMODITY.get(int(hs4))


def resolve_crop(commodity: str, hs4: Optional[int] = None) -> Dict[str, object]:
    """
    Full resolution: commodity string + optional HS4 → crop names.

    Returns
    -------
    dict:
        matched_crops: list[str] or None
        matched_commodity_key: str
        match_source: "commodity_name" | "hs4_fallback" | "none"
        reliable: bool
        note: str
    """
    crops = get_crop_names_for_commodity(commodity)
    source = "commodity_name"

    if crops is None and hs4 is not None:
        comm_key = get_commodity_for_hs4(hs4)
        if comm_key:
            crops = get_crop_names_for_commodity(comm_key)
            source = "hs4_fallback"

    reliable = crops is not None
    if not reliable:
        note = (
            f"No reliable agricultural crop match for commodity='{commodity}' "
            f"(HS4={hs4}). Returning 'no reliable crop match'."
        )
    elif crops is None:
        note = f"Commodity '{commodity}' maps to None (e.g., palm oil — imported, no domestic crop record)."
        reliable = False
    else:
        note = f"Mapped to {len(crops)} crop name(s): {crops}"

    return {
        "matched_crops": crops,
        "matched_commodity_key": commodity.strip().lower(),
        "match_source": source if reliable else "none",
        "reliable": reliable,
        "note": note,
    }
