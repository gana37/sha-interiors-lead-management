"""
hyderabad_geo.py - Hyderabad Metropolitan Service Area & Locality Master Engine
SHA Interface Interiors - AI-Powered Lead Management System (Hyderabad Edition)

Defines the geographic reference data, regional clustering, and dynamic locality
management for Hyderabad, Secunderabad, and surrounding Telangana service areas.
"""

import sys
from typing import Dict, List, Optional, Tuple, Set, Any

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Default geographical configuration
DEFAULT_COUNTRY = "India"
DEFAULT_STATE = "Telangana"
DEFAULT_CITY = "Hyderabad"

# Core Hyderabad Metropolitan Regions
HYDERABAD_REGIONS = [
    "West Hyderabad",
    "North Hyderabad",
    "Central Hyderabad",
    "East Hyderabad",
    "South Hyderabad",
    "Secunderabad"
]

# Standard Locality Master Catalog partitioned by Region
LOCALITY_CATALOG: Dict[str, List[str]] = {
    "West Hyderabad": [
        "Gachibowli",
        "Madhapur",
        "Kondapur",
        "HITEC City",
        "Financial District",
        "Nanakramguda",
        "Kokapet",
        "Narsingi",
        "Tellapur",
        "Manikonda",
        "Nallagandla",
        "Hafeezpet",
        "Chandanagar",
        "Serilingampally"
    ],
    "North Hyderabad": [
        "Kukatpally",
        "Miyapur",
        "Bachupally",
        "Nizampet",
        "Kompally",
        "Suchitra",
        "Bowenpally",
        "Alwal",
        "Jeedimetla",
        "Quthbullapur"
    ],
    "Central Hyderabad": [
        "Banjara Hills",
        "Jubilee Hills",
        "Somajiguda",
        "Begumpet",
        "Punjagutta",
        "Ameerpet",
        "Khairatabad",
        "Lakdikapul",
        "Himayatnagar",
        "Abids"
    ],
    "East Hyderabad": [
        "Uppal",
        "Nagole",
        "LB Nagar",
        "Habsiguda",
        "Tarnaka",
        "Nacharam",
        "Ghatkesar",
        "Boduppal",
        "Peerzadiguda",
        "Pocharam"
    ],
    "South Hyderabad": [
        "Mehdipatnam",
        "Attapur",
        "Rajendra Nagar",
        "Shamshabad",
        "Bandlaguda",
        "Chandrayangutta",
        "Falaknuma",
        "Kothapet",
        "Saroornagar",
        "Saidabad"
    ],
    "Secunderabad": [
        "Secunderabad",
        "Sainikpuri",
        "Malkajgiri",
        "ECIL",
        "AS Rao Nagar",
        "Trimulgherry",
        "Kapra",
        "Yapral",
        "Moula Ali"
    ]
}

# Authentic PIN Code Reference Map for Hyderabad Metropolitan Localities
LOCALITY_PINCODES: Dict[str, str] = {
    # West Hyderabad
    "Gachibowli": "500032",
    "Madhapur": "500081",
    "Kondapur": "500084",
    "HITEC City": "500081",
    "Financial District": "500032",
    "Nanakramguda": "500032",
    "Kokapet": "500075",
    "Narsingi": "500075",
    "Tellapur": "502032",
    "Manikonda": "500089",
    "Nallagandla": "500019",
    "Hafeezpet": "500049",
    "Chandanagar": "500050",
    "Serilingampally": "500019",

    # North Hyderabad
    "Kukatpally": "500072",
    "Miyapur": "500049",
    "Bachupally": "500090",
    "Nizampet": "500090",
    "Kompally": "500014",
    "Suchitra": "500067",
    "Bowenpally": "500011",
    "Alwal": "500010",
    "Jeedimetla": "500055",
    "Quthbullapur": "500055",

    # Central Hyderabad
    "Banjara Hills": "500034",
    "Jubilee Hills": "500033",
    "Somajiguda": "500082",
    "Begumpet": "500016",
    "Punjagutta": "500082",
    "Ameerpet": "500016",
    "Khairatabad": "500004",
    "Lakdikapul": "500004",
    "Himayatnagar": "500029",
    "Abids": "500001",

    # East Hyderabad
    "Uppal": "500039",
    "Nagole": "500068",
    "LB Nagar": "500074",
    "Habsiguda": "500007",
    "Tarnaka": "500017",
    "Nacharam": "500076",
    "Ghatkesar": "501301",
    "Boduppal": "500092",
    "Peerzadiguda": "500039",
    "Pocharam": "500088",

    # South Hyderabad
    "Mehdipatnam": "500028",
    "Attapur": "500048",
    "Rajendra Nagar": "500030",
    "Shamshabad": "501218",
    "Bandlaguda": "500068",
    "Chandrayangutta": "500005",
    "Falaknuma": "500053",
    "Kothapet": "500035",
    "Saroornagar": "500035",
    "Saidabad": "500059",

    # Secunderabad
    "Secunderabad": "500003",
    "Sainikpuri": "500094",
    "Malkajgiri": "500047",
    "ECIL": "500062",
    "AS Rao Nagar": "500062",
    "Trimulgherry": "500015",
    "Kapra": "500062",
    "Yapral": "500087",
    "Moula Ali": "500040"
}


def get_pincode_for_locality(locality: Optional[str]) -> str:
    """Returns authentic postal PIN code for locality, or empty string if custom/unlisted."""
    if not locality:
        return ""
    loc_clean = locality.strip()
    for k, pin in LOCALITY_PINCODES.items():
        if k.lower() == loc_clean.lower():
            return pin
    return ""

# Dynamic registry for user-added / runtime localities
CUSTOM_LOCALITIES: Dict[str, str] = {}

# Locality Scoring Tiers for Interior Design Lead Qualification (Max 20 pts)
LOCALITY_SCORING_TIERS: Dict[str, int] = {
    # Tier 1: Prime Luxury & IT Corridors (Score: 20 pts)
    "Jubilee Hills": 20,
    "Banjara Hills": 20,
    "Gachibowli": 20,
    "Madhapur": 20,
    "Financial District": 20,
    "Kokapet": 20,
    "HITEC City": 20,
    "Kondapur": 20,
    "Nanakramguda": 20,

    # Tier 2: High-Demand Established Residential Corridors (Score: 17 pts)
    "Narsingi": 17,
    "Tellapur": 17,
    "Manikonda": 17,
    "Nallagandla": 17,
    "Kukatpally": 17,
    "Miyapur": 17,
    "Bachupally": 17,
    "Nizampet": 17,
    "Kompally": 17,
    "Begumpet": 17,
    "Somajiguda": 17,
    "Secunderabad": 17,
    "Sainikpuri": 17,
    "Himayatnagar": 17,
    "Serilingampally": 17,

    # Tier 3: Core Urban & Established Communities (Score: 14 pts)
    "Ameerpet": 14,
    "Punjagutta": 14,
    "Suchitra": 14,
    "Bowenpally": 14,
    "Chandanagar": 14,
    "Hafeezpet": 14,
    "Alwal": 14,
    "Uppal": 14,
    "Nagole": 14,
    "Habsiguda": 14,
    "Tarnaka": 14,
    "Attapur": 14,
    "Mehdipatnam": 14,
    "ECIL": 14,
    "AS Rao Nagar": 14,
    "Trimulgherry": 14,
    "Moula Ali": 14,

    # Tier 4: Developing / Greater Metropolitan Corridors (Score: 12 pts)
    "LB Nagar": 12,
    "Kothapet": 12,
    "Saroornagar": 12,
    "Saidabad": 12,
    "Jeedimetla": 12,
    "Quthbullapur": 12,
    "Nacharam": 12,
    "Ghatkesar": 12,
    "Boduppal": 12,
    "Peerzadiguda": 12,
    "Pocharam": 12,
    "Rajendra Nagar": 12,
    "Shamshabad": 12,
    "Bandlaguda": 12,
    "Chandrayangutta": 12,
    "Falaknuma": 12,
    "Malkajgiri": 12,
    "Kapra": 12,
    "Yapral": 12,
    "Khairatabad": 12,
    "Lakdikapul": 12,
    "Abids": 12
}


def get_all_localities() -> List[str]:
    """Returns a sorted list of all standard and dynamically added Hyderabad localities."""
    all_locs = set()
    for loc_list in LOCALITY_CATALOG.values():
        all_locs.update(loc_list)
    all_locs.update(CUSTOM_LOCALITIES.keys())
    return sorted(list(all_locs))


# Canonical reference list of all authentic Hyderabad reference localities
HYDERABAD_LOCALITIES: List[str] = get_all_localities()

# Display-ready region options with Secunderabad & Metropolitan Areas
DISPLAY_REGION_OPTIONS = [
    "All Regions",
    "West Hyderabad",
    "North Hyderabad",
    "Central Hyderabad",
    "East Hyderabad",
    "South Hyderabad",
    "Secunderabad & Metropolitan Areas"
]


def is_known_locality(locality: Optional[str]) -> bool:
    """Returns True if the locality is validated in the catalog or registered custom localities."""
    if not locality or not locality.strip():
        return False
    clean = locality.strip().lower()
    return clean in [l.lower() for l in get_all_localities()]


def get_localities_for_region(region: Optional[str]) -> List[str]:
    """Returns sorted list of localities in a region. Supports 'Secunderabad & Metropolitan Areas'."""
    if not region or region in ("All", "All Regions"):
        return get_all_localities()
    reg_clean = "Secunderabad" if "Secunderabad" in region else region
    return sorted(LOCALITY_CATALOG.get(reg_clean, []))



def get_locality_metadata(locality: Optional[str]) -> Dict[str, Any]:
    """
    Returns a unified metadata dictionary for a Hyderabad locality:
    region, pincode, qualification tier (1 to 4), and scoring weight (12 to 20).
    """
    if not locality or not locality.strip():
        return {
            "locality": "Unspecified",
            "region": "Unspecified Hyderabad",
            "pincode": "",
            "tier": 4,
            "score": 0
        }

    clean_loc = locality.strip()
    reg = get_region_for_locality(clean_loc)
    pin = get_pincode_for_locality(clean_loc)
    score = get_locality_score(clean_loc)

    if score >= 20:
        tier = 1
    elif score >= 17:
        tier = 2
    elif score >= 14:
        tier = 3
    else:
        tier = 4

    return {
        "locality": clean_loc,
        "region": reg,
        "pincode": pin,
        "tier": tier,
        "score": score
    }


def get_region_for_locality(locality: Optional[str]) -> str:
    """
    Resolves the administrative/marketing region for a given Hyderabad locality.
    Falls back to 'Other / Emerging Hyderabad' if not in predefined catalog.
    """
    if not locality or not locality.strip():
        return "Unspecified Hyderabad"

    loc_clean = locality.strip()

    # Check custom registry first
    if loc_clean in CUSTOM_LOCALITIES:
        return CUSTOM_LOCALITIES[loc_clean]

    # Check standard catalog (case-insensitive)
    for region, loc_list in LOCALITY_CATALOG.items():
        for l in loc_list:
            if l.lower() == loc_clean.lower():
                return region

    return "Other / Emerging Hyderabad"


def get_locality_score(locality: Optional[str]) -> int:
    """
    Returns the location score (0 to 20) for Hyderabad lead scoring.
    Recognized Hyderabad localities receive 12-20 points based on premium tier.
    Unlisted or custom Hyderabad localities receive 14 points (standard service baseline).
    Non-Hyderabad or empty locations receive 0 points.
    """
    if not locality or not locality.strip():
        return 0

    loc_clean = locality.strip()

    # Exact match in scoring tiers
    for k, score in LOCALITY_SCORING_TIERS.items():
        if k.lower() == loc_clean.lower():
            return score

    # If it is in the catalog or custom registered, award baseline Hyderabad score (14)
    if loc_clean.lower() in [l.lower() for l in get_all_localities()]:
        return 14

    # Unverified / non-Hyderabad locality receives 0 points
    return 0


def is_hyderabad_service_area(city: Optional[str], state: Optional[str] = None) -> bool:
    """
    Verifies if a city/state falls within the active Hyderabad service jurisdiction.
    Accepts Hyderabad, Secunderabad, Cyberabad, and Greater Hyderabad.
    """
    if not city:
        return False

    c = city.strip().lower()
    valid_cities = {
        "hyderabad",
        "secunderabad",
        "cyberabad",
        "greater hyderabad",
        "hyderabad metropolitan",
        "hyderabad, telangana"
    }
    return c in valid_cities or "hyderabad" in c or "secunderabad" in c


def register_custom_locality(locality: str, region: str = "Other / Emerging Hyderabad") -> bool:
    """
    Dynamically registers a new Hyderabad neighbourhood so the CRM adapts to user expansion.
    Never rejects new localities.
    """
    clean_loc = locality.strip().title()
    if not clean_loc:
        return False
    CUSTOM_LOCALITIES[clean_loc] = region
    global HYDERABAD_LOCALITIES
    if clean_loc not in HYDERABAD_LOCALITIES:
        HYDERABAD_LOCALITIES = get_all_localities()
    return True


def get_region_breakdown() -> Dict[str, List[str]]:
    """Returns a full mapping of regions to their registered localities."""
    result = {r: list(locs) for r, locs in LOCALITY_CATALOG.items()}
    # Append custom localities into their designated regions
    for loc, reg in CUSTOM_LOCALITIES.items():
        if reg in result:
            if loc not in result[reg]:
                result[reg].append(loc)
        else:
            result.setdefault(reg, []).append(loc)
    return result
