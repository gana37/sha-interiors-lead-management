"""
cost_estimator.py - Advanced Parametric Interior Cost Estimation Engine
SHA Interface Interiors - AI-Powered Lead Management System

Provides transparent, indicative cost estimation across Essential, Premium,
and Luxury tiers based on property size, city index, room scope, and material
specifications. Includes itemized BOQs, per-sqft metrics, and explicit disclaimers.
"""

import sys
from typing import Dict, List, Optional, Any

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ==============================================================================
# 1. PRICING CONFIGURATION & CITY MULTIPLIERS
# ==============================================================================

CITY_COST_INDEX: Dict[str, float] = {
    "bangalore": 1.00,    # Primary studio hub (Baseline = 1.0)
    "hyderabad": 0.98,    # Primary studio hub
    "chennai": 0.95,      # Secondary expansion hub
    "mumbai": 1.15,       # Higher logistics & labor index
    "pune": 1.00,
    "delhi": 1.05,
    "other": 0.92
}

DEFAULT_PROPERTY_AREAS: Dict[str, int] = {
    "1BHK": 600,
    "2BHK": 1050,
    "3BHK": 1550,
    "4BHK": 2400,
    "Villa": 3500,
    "Studio": 450,
    "Commercial": 1200
}

# Base Turnkey Rate Card (₹ per sq ft of built-up area)
TURNKEY_RATES_PER_SQFT = {
    "essential": {
        "tier_name": "Essential / Budget-Friendly",
        "min_rate": 1150,
        "max_rate": 1450,
        "avg_rate": 1300,
        "description": "Functional, durable home interior using Commercial Plywood, 0.8mm Laminates, Ebco hardware, and basic false ceiling.",
        "materials": "MR/Commercial Ply, 0.8mm Matte Laminate, Ebco fittings, Tractor Emulsion, Granite counter"
    },
    "premium": {
        "tier_name": "Premium / Balanced Elegance",
        "min_rate": 1650,
        "max_rate": 2150,
        "avg_rate": 1900,
        "description": "High-durability luxury living with BWP/BWR Marine Ply, 1mm Merino Laminate / Acrylic, Hettich/Hafele soft-close hardware, Saint-Gobain full false ceiling, and Asian Paints Royale.",
        "materials": "IS 710 BWP Ply + HDHMR, 1mm Laminate & Acrylic, Hettich soft-close, Royale Luxury Emulsion, Quartz counter"
    },
    "luxury": {
        "tier_name": "Luxury / Bespoke Architectural",
        "min_rate": 2600,
        "max_rate": 3600,
        "avg_rate": 3100,
        "description": "Ultra-luxe bespoke interiors featuring authentic Italian marble accents, natural wood veneers with PU polish, Blum Austria motion fittings, magnetic track lighting, and smart automation.",
        "materials": "100% Calibrated Marine Ply, Natural Veneer with PU / 2mm Acrylic, Blum Blumotion, Italian Statuario marble, Profile & track lighting"
    }
}

# Component Itemized Pricing (Baseline in INR for Bangalore/Hyderabad)
COMPONENT_ESTIMATES = {
    "kitchen": {
        "essential": {"min": 140000, "max": 190000, "label": "Modular Kitchen (Straight/L-Shape, Commercial Ply + 0.8mm Laminate, Ebco)"},
        "premium": {"min": 240000, "max": 360000, "label": "Modular Kitchen (L/Parallel Shape, BWP Marine Ply + Acrylic/1mm Laminate, Hettich InnoTech, Quartz)"},
        "luxury": {"min": 450000, "max": 750000, "label": "Modular Kitchen (Island/U-Shape, Marine Ply + PU/Ceramic finish, Blum Tandembox & Aventos)"}
    },
    "wardrobe": {
        "essential": {"min": 60000, "max": 80000, "label": "Wardrobe (per 7x7 ft unit, Hinged, 0.8mm Laminate)"},
        "premium": {"min": 95000, "max": 140000, "label": "Wardrobe (per 7x7 ft unit, Sliding with Loft, 1mm Laminate / Acrylic, Soft-close)"},
        "luxury": {"min": 160000, "max": 260000, "label": "Wardrobe (per unit, Floor-to-Ceiling Lacquered Glass / Veneer PU, Hafele Slido, LED profiles)"}
    },
    "living_room": {
        "essential": {"min": 65000, "max": 100000, "label": "Living Room (TV console + Basic shoe console + Wall paint)"},
        "premium": {"min": 140000, "max": 240000, "label": "Living Room (Fluted TV unit + Partition screen + Foyer console with mirror + Accent wall)"},
        "luxury": {"min": 320000, "max": 550000, "label": "Living Room (Italian Marble feature wall + Veneer rafters + Bespoke bar/crockery + Smart lighting)"}
    },
    "false_ceiling": {
        "rate_per_sqft": {"min": 110, "max": 165},
        "label": "Gypsum False Ceiling with perimeter LED cove & spotlight points"
    },
    "painting": {
        "rate_per_sqft": {"min": 35, "max": 55},
        "label": "Wall Painting (2 coats putty + primer + 2 coats Asian Paints Royale luxury emulsion)"
    }
}


def estimate_project_cost(
    property_type: str = "3BHK",
    built_up_area: Optional[int] = None,
    city: str = "Hyderabad",
    scope_of_work: str = "Complete Turnkey Interiors",
    custom_wardrobes_count: Optional[int] = None
) -> Dict[str, Any]:
    """
    Computes parametric interior cost estimates for Essential, Premium, and Luxury tiers.
    """
    p_type = property_type.strip()
    area = built_up_area or DEFAULT_PROPERTY_AREAS.get(p_type, 1200)
    city_slug = city.lower().strip()
    multiplier = CITY_COST_INDEX.get(city_slug, CITY_COST_INDEX["other"])

    # Determine default wardrobe count based on BHK
    w_count = custom_wardrobes_count
    if w_count is None:
        if "1BHK" in p_type or "Studio" in p_type:
            w_count = 1
        elif "2BHK" in p_type:
            w_count = 2
        elif "3BHK" in p_type:
            w_count = 3
        elif "4BHK" in p_type:
            w_count = 4
        elif "Villa" in p_type:
            w_count = 5
        else:
            w_count = 2

    # Tier calculations
    tiers_result: Dict[str, Any] = {}
    for tier_key in ["essential", "premium", "luxury"]:
        tier_cfg = TURNKEY_RATES_PER_SQFT[tier_key]
        base_rate = tier_cfg["avg_rate"]
        adjusted_rate = int(base_rate * multiplier)

        total_cost = int(area * adjusted_rate)
        min_cost = int(area * tier_cfg["min_rate"] * multiplier)
        max_cost = int(area * tier_cfg["max_rate"] * multiplier)

        # Approximate BOQ category breakdown percentages
        # Woodwork: 58%, Civil & Plumbing: 10%, False Ceiling & Lighting: 14%, Painting: 8%, Hardware & Fitting: 10%
        woodwork_cost = int(total_cost * 0.58)
        ceiling_lighting_cost = int(total_cost * 0.14)
        civil_plumbing_cost = int(total_cost * 0.10)
        painting_cost = int(total_cost * 0.08)
        hardware_fitting_cost = int(total_cost * 0.10)

        # Component specific estimates
        kitchen_cost = int(COMPONENT_ESTIMATES["kitchen"][tier_key]["max"] * multiplier)
        wardrobe_unit_cost = int(COMPONENT_ESTIMATES["wardrobe"][tier_key]["max"] * multiplier)
        total_wardrobe_cost = wardrobe_unit_cost * w_count

        tiers_result[tier_key] = {
            "tier_name": tier_cfg["tier_name"],
            "total_estimated_inr": total_cost,
            "cost_range_inr": f"₹{min_cost / 100000:.2f}L – ₹{max_cost / 100000:.2f}L",
            "rate_per_sqft": adjusted_rate,
            "description": tier_cfg["description"],
            "materials_summary": tier_cfg["materials"],
            "boq_breakdown": {
                "modular_woodwork": woodwork_cost,
                "false_ceiling_and_electrical": ceiling_lighting_cost,
                "civil_countertop_plumbing": civil_plumbing_cost,
                "wall_painting_and_finishes": painting_cost,
                "hardware_and_installation": hardware_fitting_cost
            },
            "key_components": {
                "kitchen_estimate": kitchen_cost,
                "wardrobe_count": w_count,
                "total_wardrobes_estimate": total_wardrobe_cost
            }
        }

    return {
        "property_type": p_type,
        "built_up_area_sqft": area,
        "city": city.capitalize(),
        "city_cost_index": multiplier,
        "scope_of_work": scope_of_work,
        "wardrobes_counted": w_count,
        "tiers": tiers_result,
        "assumptions": [
            f"Built-up area estimated at {area} sq ft for standard {p_type} layout.",
            f"Location cost index applied: {multiplier:.2f}x for {city.capitalize()} market conditions.",
            "Includes material supply, factory fabrication, freight, site carpentry, and installation supervision.",
            "Woodwork based on standard ceiling height of 9.5 to 10 feet.",
            "Excludes loose furniture (sofa, dining chairs, mattress), movable appliances (chimney, hob, refrigerator), and GST (18%)."
        ],
        "disclaimer": (
            "⚠️ IMPORTANT NOTICE: This is an automated indicative project cost estimate generated for preliminary spatial budgeting. "
            "It does NOT constitute an official, binding commercial quotation from SHA Interface Interiors. "
            "Final pricing is confirmed following an on-site architectural measurement and customized material selection."
        )
    }


def format_cost_estimate_markdown(estimate: Dict[str, Any]) -> str:
    """Formats the estimate dictionary into an executive Markdown report."""
    tiers = estimate["tiers"]
    e_tier = tiers["essential"]
    p_tier = tiers["premium"]
    l_tier = tiers["luxury"]

    md = (
        f"### 💰 Interior Project Cost Estimate for {estimate['property_type']} ({estimate['built_up_area_sqft']} sq ft)\n"
        f"**Location:** {estimate['city']} | **Scope:** {estimate['scope_of_work']}\n\n"
        f"| Package Tier | Total Estimated Cost | Rate per Sq Ft | Core Material Specifications |\n"
        f"|:---|:---:|:---:|:---|\n"
        f"| **1. {e_tier['tier_name']}** | **{e_tier['cost_range_inr']}** | ₹{e_tier['rate_per_sqft']}/sqft | {e_tier['materials_summary']} |\n"
        f"| **2. {p_tier['tier_name']}** | **{p_tier['cost_range_inr']}** | ₹{p_tier['rate_per_sqft']}/sqft | {p_tier['materials_summary']} |\n"
        f"| **3. {l_tier['tier_name']}** | **{l_tier['cost_range_inr']}** | ₹{l_tier['rate_per_sqft']}/sqft | {l_tier['materials_summary']} |\n\n"
        f"#### 📊 Recommended Package: **{p_tier['tier_name']}** (~₹{p_tier['total_estimated_inr'] / 100000:.2f} Lakh)\n"
        f"**Itemized BOQ Breakdown:**\n"
        f"- 🪵 **Modular Woodwork (Kitchen, {estimate['wardrobes_counted']} Wardrobes, Consoles):** ₹{p_tier['boq_breakdown']['modular_woodwork']:,}\n"
        f"- 💡 **False Ceiling & Electrical Lighting Points:** ₹{p_tier['boq_breakdown']['false_ceiling_and_electrical']:,}\n"
        f"- 🪨 **Civil, Countertops & Wet Zone Plumbing:** ₹{p_tier['boq_breakdown']['civil_countertop_plumbing']:,}\n"
        f"- 🎨 **Wall Preparation & Asian Paints Royale:** ₹{p_tier['boq_breakdown']['wall_painting_and_finishes']:,}\n"
        f"- 🔩 **Premium Hettich Hardware & Installation:** ₹{p_tier['boq_breakdown']['hardware_and_installation']:,}\n\n"
        f"**Key Assumptions:**\n"
    )
    for a in estimate["assumptions"]:
        md += f"- {a}\n"

    md += f"\n> {estimate['disclaimer']}"
    return md
