"""
material_knowledge.py - Interior Materials, Specifications & Technical Consultant
SHA Interface Interiors - AI-Powered Lead Management System

Comprehensive technical repository and comparative intelligence engine for
core boards (Plywood, HDHMR, MDF, Particle Board), surface finishes (Laminate,
Acrylic, Veneer, PU), architectural hardware (Blum, Hettich, Hafele), countertops,
flooring, and false ceiling materials.
"""

import sys
from typing import Dict, List, Optional, Any

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ==============================================================================
# 1. CORE SUBSTRATES / BOARDS REPOSITORY
# ==============================================================================

CORE_BOARDS: Dict[str, Dict[str, Any]] = {
    "bwp_plywood": {
        "name": "BWP Marine Grade Plywood (IS 710)",
        "full_form": "Boiling Water Proof Plywood",
        "standard": "IS:710 certified (72 hours boiling water test certified)",
        "density": "750–800 kg/m³",
        "adhesive": "Phenol Formaldehyde (PF) synthetic resin",
        "core_types": "100% Gurjan / Hardwood Eucalyptus layers",
        "advantages": [
            "100% waterproof and termite/borer treated under vacuum pressure",
            "Highest mechanical screw-holding capacity among all core boards",
            "Zero delamination even in prolonged wet conditions",
            "High structural flexural strength with minimal deflection under load"
        ],
        "disadvantages": [
            "Higher cost compared to commercial ply or MDF",
            "Requires careful calibrated sanding for ultra-thin acrylic sheets"
        ],
        "applications": ["Kitchen sink base units", "Bathroom vanities", "Balcony storage", "Heavy load book racks"],
        "durability_years": "25+ years",
        "maintenance": "Virtually zero moisture maintenance; wipe clean",
        "cost_tier": "Premium (₹110–₹160 per sq ft for 19mm)"
    },
    "bwr_plywood": {
        "name": "BWR Grade Plywood (IS 303)",
        "full_form": "Boiling Water Resistant Plywood",
        "standard": "IS:303 certified (8 hours boiling water test)",
        "density": "700–750 kg/m³",
        "adhesive": "Fortified Melamine Urea Formaldehyde (MUF) resin",
        "core_types": "Hardwood core with alternate poplar/eucalyptus",
        "advantages": [
            "Excellent moisture resistance for semi-wet zones",
            "Durable screw-holding capability",
            "Cost-effective alternative to full BWP marine ply for dry zones"
        ],
        "disadvantages": [
            "Not suitable for continuous water submersion or chronic leakage areas"
        ],
        "applications": ["Modular kitchen wall cabinets", "Utility room cabinetry", "Dining room storage"],
        "durability_years": "15–20 years",
        "maintenance": "Dry wipe; avoid standing puddles",
        "cost_tier": "Medium (₹85–₹110 per sq ft for 19mm)"
    },
    "mr_plywood": {
        "name": "MR Commercial Plywood (IS 303)",
        "full_form": "Moisture Resistant (Commercial) Plywood",
        "standard": "IS:303 Commercial Grade",
        "density": "650–700 kg/m³",
        "adhesive": "Urea Formaldehyde (UF) resin",
        "core_types": "Poplar and mixed soft-hard woods",
        "advantages": [
            "Economical and lightweight",
            "Good screw holding for basic residential cabinetry in dry rooms"
        ],
        "disadvantages": [
            "Will swell and delaminate if exposed to direct water or chronic humidity",
            "Must not be used anywhere near kitchen sinks or bathrooms"
        ],
        "applications": ["Bedroom wardrobes (dry walls)", "TV entertainment units", "Shoe consoles", "Study tables"],
        "durability_years": "10–15 years",
        "maintenance": "Strictly keep dry",
        "cost_tier": "Budget (₹60–₹80 per sq ft for 19mm)"
    },
    "hdhmr": {
        "name": "HDHMR Board (Action TESA / Century)",
        "full_form": "High Density High Moisture Resistance Board",
        "standard": "IS:5509 Fire & Moisture standard compliant",
        "density": "850–900 kg/m³ (significantly denser than MDF/Ply)",
        "adhesive": "Special water-resistant bonding matrix",
        "core_types": "Dense compressed hardwood eucalyptus fiber chips",
        "advantages": [
            "Extremely uniform core with zero internal voids or gaps",
            "Superb routing and CNC carving capability without chip-outs",
            "Exceptional moisture resistance compared to standard MDF or particle board",
            "Seamless laser-edge banded surfaces for modern handle-less doors"
        ],
        "disadvantages": [
            "Heavy board weight requires heavy-duty hinges (minimum 3 hinges per shutter)",
            "Once pierced by water over long periods, edges may swell slightly if unbanded"
        ],
        "applications": ["Kitchen shutters", "Wardrobe shutters", "CNC decorative jalis", "Bathroom vanity fronts"],
        "durability_years": "15–20 years",
        "maintenance": "Easy to clean; maintain edge-banding intact",
        "cost_tier": "Medium (₹65–₹85 per sq ft for 18mm)"
    },
    "mdf": {
        "name": "MDF Board",
        "full_form": "Medium Density Fibreboard",
        "standard": "IS:12406",
        "density": "700–750 kg/m³",
        "adhesive": "Synthetic resin glue under heat and pressure",
        "core_types": "Refined wood fibers",
        "advantages": [
            "Smooth, flawless mirror-flat surface ideal for high-gloss PU and Duco painting",
            "No wood grain or knots; clean CNC precision carving",
            "Budget-friendly"
        ],
        "disadvantages": [
            "Poor resistance to moisture and water; swells rapidly when wet",
            "Lower screw holding compared to marine plywood"
        ],
        "applications": ["PU painted cabinet shutters", "Wall acoustic fluted panels", "Decorative moldings"],
        "durability_years": "8–12 years",
        "maintenance": "Keep away from any water contact",
        "cost_tier": "Budget (₹45–₹60 per sq ft for 18mm)"
    },
    "particle_board": {
        "name": "Particle Board (Pre-laminated Chipboard)",
        "full_form": "Low Density Wood Chipboard",
        "standard": "IS:3087",
        "density": "550–650 kg/m³",
        "adhesive": "UF resin binder",
        "core_types": "Coarse wood shavings, sawdust, and flakes",
        "advantages": [
            "Lowest cost among all engineered wood boards",
            "Lightweight and pre-laminated at factory for fast flat-pack assembly"
        ],
        "disadvantages": [
            "Weakest screw-holding strength; screws cannot be refastened in the same hole",
            "Swells dramatically upon moisture exposure",
            "Sagging over spans greater than 2.5 feet under heavy load"
        ],
        "applications": ["Temporary rental furniture", "Low-budget office desks", "Shoe rack shelves"],
        "durability_years": "5–7 years",
        "maintenance": "Zero water exposure",
        "cost_tier": "Economy (₹35–₹50 per sq ft for 18mm)"
    }
}

# ==============================================================================
# 2. SURFACE FINISHES REPOSITORY
# ==============================================================================

SURFACE_FINISHES: Dict[str, Dict[str, Any]] = {
    "laminate": {
        "name": "High-Pressure Laminate (HPL)",
        "thickness": "0.8mm (interior liner) to 1.0mm (exterior shutters) / 1.2mm (compact)",
        "brands": "Merino, CenturyLaminates, Greenlam, Royalé Touche",
        "types": ["Suede Finish (SF)", "High Gloss (GL)", "Textured Woodgrain", "Anti-Fingerprint Silk Matte"],
        "advantages": [
            "High scratch, heat, and stain resistance",
            "Massive variety of colors, woodgrains, and stone patterns",
            "Cost-effective, highly durable, and very easy to maintain",
            "Color does not fade over time"
        ],
        "disadvantages": [
            "Visible joint seam along edges (reduced with modern matching PVC edge-banding)",
            "Cannot be curved around intricate 3D routed profiles"
        ],
        "applications": ["Wardrobes", "Kitchen base/wall cabinets", "Study tables", "Internal cabinet lining"],
        "cost_index": "₹800 to ₹3,500 per 8x4 sheet (₹25–₹110/sqft)"
    },
    "acrylic": {
        "name": "High-Gloss Acrylic Sheets",
        "thickness": "1.5mm to 2.0mm high-grade PMMA sheet",
        "brands": "Euro Pratik, Rehau, Century Acrylic, Alkosign",
        "types": ["Solid High Gloss", "Metallic Sparkle", "Scratch-Resistant Matte Acrylic"],
        "advantages": [
            "Unrivalled mirror-like glass reflection and depth of color",
            "100% waterproof and UV-resistant; will not chip or crack easily",
            "Seamless edge-banding with zero-joint hot-air technology (Rehau)"
        ],
        "disadvantages": [
            "High gloss shows fingerprints easily (requires regular microfiber wiping)",
            "Prone to fine hairline scratches if wiped with abrasive scrubbers",
            "Higher cost than standard laminate"
        ],
        "applications": ["Modern modular kitchen shutters", "Foyer accent cabinets", "Luxury bedroom wardrobes"],
        "cost_index": "₹3,500 to ₹7,000 per 8x4 sheet (₹110–₹220/sqft)"
    },
    "veneer": {
        "name": "Natural Wood Veneer",
        "thickness": "0.5mm to 4.0mm real sliced timber on backing ply",
        "species": "American Walnut, Smoked Oak, Teak, Ash, Ebony, Rosewood",
        "polishes": ["Melamine Polish", "PU Polyurethane Polish (Matte / Gloss)", "Polyester Open-Pore Polish"],
        "advantages": [
            "100% natural, authentic luxury wood grain with unique organic beauty",
            "Can be re-polished and restored after several years",
            "Adds substantial resale value and timeless warmth to residential spaces"
        ],
        "disadvantages": [
            "Requires skilled polishing labor and periodic re-coating every 5–7 years",
            "Susceptible to scratches and water stains if liquid is left standing",
            "Significantly higher cost than synthetic laminates"
        ],
        "applications": ["Living room feature walls", "Main entrance doors", "Dining consoles", "Master bed headboards"],
        "cost_index": "₹1,200 to ₹10,000+ per 8x4 sheet (plus ₹80–₹150/sqft polishing)"
    },
    "pu_finish": {
        "name": "PU (Polyurethane) & Duco Coating",
        "types": ["High-Gloss PU", "Dead Matte PU", "Satin Pearl PU", "Metallic PU"],
        "brands": "Sirca (Italy), ICA (Italy), Asian Paints WoodTech PU",
        "advantages": [
            "Completely seamless finish with zero edge joints or tape lines",
            "Can be sprayed over intricate 3D grooved/routed shaker doors",
            "Non-yellowing, chemical resistant, and exceptionally smooth to the touch"
        ],
        "disadvantages": [
            "Requires dust-free spray booth and highly skilled applicators",
            "Can chip under sharp impact from metal utensils",
            "High material and application cost"
        ],
        "applications": ["European handle-less kitchens", "Shaker style wardrobe doors", "Bespoke vanity cabinets"],
        "cost_index": "₹200 to ₹450 per sq ft (material + multi-coat labor)"
    }
}

# ==============================================================================
# 3. ARCHITECTURAL HARDWARE REPOSITORY
# ==============================================================================

HARDWARE_CATALOG: Dict[str, Dict[str, Any]] = {
    "blum": {
        "brand": "Blum (Austria)",
        "market_position": "Top-tier global gold standard in motion fittings",
        "key_products": [
            "CLIP top BLUMOTION Hinges: Integrated soft-close in hinge boss, 200,000 cycle tested (25+ years)",
            "TANDEMBOX Antaro / LEGRABOX: Ultra-smooth concealed drawer runners, 30kg–65kg dynamic load rating",
            "AVENTOS Lift Systems (HF, HK, HL): Bi-fold overhead lift doors with effortless finger-touch stop at any angle",
            "SERVO-DRIVE: Electronic touch-to-open system for handle-less luxury cabinetry"
        ],
        "warranty": "Lifetime functional warranty",
        "cost_bracket": "Luxury / Premium (approx ₹600–₹1,200 per pair of hinges; ₹4,500–₹9,000 per drawer box)"
    },
    "hettich": {
        "brand": "Hettich (Germany)",
        "market_position": "Premier German engineering, most popular premium brand in India",
        "key_products": [
            "Sensys Hinges: Integrated Silent System soft-close, operates reliably from 35° wide angle",
            "InnoTech Atira / ArciTech: Double-walled steel drawer systems with customizable railing profiles",
            "Quadro Runners: Concealed undermount runners for wooden drawers",
            "WingLine Sliding/Folding Systems: Panoramic folding door fittings for wardrobes"
        ],
        "warranty": "10 to 15 years functional warranty",
        "cost_bracket": "Upper Mid to Premium (approx ₹350–₹750 per pair of hinges; ₹2,800–₹5,500 per drawer box)"
    },
    "hafele": {
        "brand": "Hafele (Germany)",
        "market_position": "Comprehensive premium architectural hardware and kitchen smart accessories",
        "key_products": [
            "Metalla Hinges: Robust soft-close hinges for residential casework",
            "Matrix Box P: Premium slim-profile drawer systems with synchronised motion",
            "Slido Wardrobe Systems: Heavy-duty soft-close sliding mechanisms for 50kg–100kg wardrobe doors",
            "Corner Optimizers: LeMans corner shelves, Magic Corner pullouts"
        ],
        "warranty": "10 years warranty",
        "cost_bracket": "Upper Mid to Premium"
    },
    "ebco": {
        "brand": "Ebco (India)",
        "market_position": "India's leading value-for-money dependable hardware manufacturer",
        "key_products": [
            "Soft-close 3D adjustable concealed hinges",
            "Pro-Motion tandem drawer boxes and telescopic channels",
            "Overbed mechanisms and wall bed fittings for space-saving homes"
        ],
        "warranty": "5 to 7 years warranty",
        "cost_bracket": "Budget to Mid-Market (approx ₹150–₹300 per pair of hinges; ₹1,200–₹2,500 per drawer)"
    }
}

# ==============================================================================
# 4. KITCHEN COUNTERTOPS REPOSITORY
# ==============================================================================

COUNTERTOPS: Dict[str, Dict[str, Any]] = {
    "quartz": {
        "material": "Engineered Composite Quartz (93% natural quartz stone + 7% polymer resins)",
        "brands": "KalingaStone, Caesarstone, AGL, Silestone",
        "advantages": [
            "Non-porous: Zero liquid absorption; impervious to turmeric, tea, coffee, wine, or lemon stains",
            "Exceptional uniform color consistency with sleek modern marble-veined designs",
            "No chemical sealing or periodic polishing ever required; highly hygienic"
        ],
        "disadvantages": [
            "Sensitive to extreme thermal shock (do not place smoking hot cast-iron pans directly without a trivet)",
            "Higher cost than natural granite"
        ],
        "price_range": "₹350 to ₹1,400 per sq ft (material only, plus ₹150–₹250/sqft fabrication & moulding)",
        "recommendation": "Top recommended choice for modern luxury kitchens in Bangalore & Hyderabad."
    },
    "granite": {
        "material": "Natural Igneous Granite Stone",
        "popular_varieties": "Black Galaxy, Jet Black (Khammam), Tan Brown, Steel Grey, Kashmir White",
        "advantages": [
            "Immense heat resistance: withstands boiling hot pots and pans directly without scorching",
            "Extremely hard and scratch-resistant against heavy Indian vessel cooking",
            "Cost-effective and widely available locally across South India"
        ],
        "disadvantages": [
            "Slightly porous: light-colored granites can absorb oil/turmeric if not sealed properly",
            "Natural slab variations mean seams may be visually visible"
        ],
        "price_range": "₹120 to ₹500 per sq ft",
        "recommendation": "Best value-for-money, virtually indestructible countertop for heavy-duty cooking."
    }
}

# ==============================================================================
# 5. KNOWLEDGE SEARCH & COMPARISON API
# ==============================================================================

def compare_materials(mat1_name: str, mat2_name: str) -> str:
    """Generates an objective, structured comparison between two interior materials."""
    m1_key = mat1_name.lower().strip().replace(" ", "_")
    m2_key = mat2_name.lower().strip().replace(" ", "_")

    # Check in boards
    b1 = CORE_BOARDS.get(m1_key)
    b2 = CORE_BOARDS.get(m2_key)

    if b1 and b2:
        return (
            f"### ⚖️ Material Comparison: {b1['name']} vs. {b2['name']}\n\n"
            f"| Attribute | {b1['name']} | {b2['name']} |\n"
            f"|:---|:---|:---|\n"
            f"| **Density** | {b1['density']} | {b2['density']} |\n"
            f"| **Adhesive/Resin** | {b1['adhesive']} | {b2['adhesive']} |\n"
            f"| **Water Resistance** | {'⭐⭐⭐⭐⭐ (100% Waterproof)' if 'bwp' in m1_key else '⭐⭐⭐ (Moisture Resistant)'} | {'⭐⭐⭐⭐⭐ (100% Waterproof)' if 'bwp' in m2_key else '⭐⭐⭐ (Moisture Resistant)'} |\n"
            f"| **Cost Tier** | `{b1['cost_tier']}` | `{b2['cost_tier']}` |\n"
            f"| **Durability** | {b1['durability_years']} | {b2['durability_years']} |\n"
            f"| **Ideal Use** | {', '.join(b1['applications'][:2])} | {', '.join(b2['applications'][:2])} |\n\n"
            f"**Key Recommendation:** Use **{b1['name']}** for wet zones (kitchen sink, vanities) and **{b2['name']}** for dry cabinetry."
        )

    # Check in finishes
    f1 = SURFACE_FINISHES.get(m1_key)
    f2 = SURFACE_FINISHES.get(m2_key)
    if f1 and f2:
        return (
            f"### ⚖️ Finish Comparison: {f1['name']} vs. {f2['name']}\n\n"
            f"- **{f1['name']}:** Cost `{f1['cost_index']}`. Advantages: {', '.join(f1['advantages'][:2])}. Disadvantage: {f1['disadvantages'][0]}.\n"
            f"- **{f2['name']}:** Cost `{f2['cost_index']}`. Advantages: {', '.join(f2['advantages'][:2])}. Disadvantage: {f2['disadvantages'][0]}.\n\n"
            f"**Recommendation:** Acrylic provides superior high-gloss depth for kitchens, while Laminate offers maximum scratch-resistance for wardrobes and kids' rooms."
        )

    return f"Detailed technical comparison between '{mat1_name}' and '{mat2_name}' is available. Please specify whether you are comparing core boards (Plywood vs HDHMR), finishes (Acrylic vs Laminate), or countertops (Quartz vs Granite)."


def search_material_knowledge(query: str) -> str:
    """Searches materials, finishes, hardware, and countertops knowledge bases."""
    q_lower = query.lower()

    # 1. Compare intent
    if "vs" in q_lower or "compare" in q_lower or "difference" in q_lower:
        if "hdhmr" in q_lower and ("ply" in q_lower or "plywood" in q_lower):
            return compare_materials("bwp_plywood", "hdhmr")
        if "acrylic" in q_lower and "laminate" in q_lower:
            return compare_materials("acrylic", "laminate")
        if "quartz" in q_lower and "granite" in q_lower:
            q_data = COUNTERTOPS["quartz"]
            g_data = COUNTERTOPS["granite"]
            return (
                f"### ⚖️ Kitchen Countertop Comparison: Quartz vs. Granite\n\n"
                f"| Feature | Engineered Quartz | Natural Granite |\n"
                f"|:---|:---|:---|\n"
                f"| **Stain Resistance** | 100% Non-porous (Immune to turmeric/oil) | Requires sealing to prevent stains |\n"
                f"| **Heat Resistance** | Up to 150°C (Requires hot pad/trivet) | Exceptional (Direct hot pan safe) |\n"
                f"| **Aesthetics** | Modern, uniform veining, sleek white/grey | Natural, granular, traditional patterns |\n"
                f"| **Cost** | `{q_data['price_range']}` | `{g_data['price_range']}` |\n\n"
                f"**SHA Recommendation:** For contemporary modular kitchens with bright backsplashes, Quartz is superior. For heavy-duty traditional tadka cooking, Jet Black Granite is unbeatable."
            )

    # 2. Check Core Boards
    for k, b in CORE_BOARDS.items():
        if k in q_lower or b["name"].lower() in q_lower or b["full_form"].lower() in q_lower:
            advs = "\n".join([f"- {a}" for a in b["advantages"]])
            dis = "\n".join([f"- {d}" for d in b["disadvantages"]])
            return (
                f"### 🪵 {b['name']}\n\n"
                f"**Technical Standard:** {b['standard']} | **Density:** {b['density']} | **Bonding Resin:** {b['adhesive']}\n\n"
                f"**Key Advantages:**\n{advs}\n\n"
                f"**Limitations:**\n{dis}\n\n"
                f"**Recommended Applications:** {', '.join(b['applications'])}\n"
                f"**Expected Lifespan:** {b['durability_years']} | **Cost Range:** `{b['cost_tier']}`"
            )

    # 3. Check Finishes
    for k, f in SURFACE_FINISHES.items():
        if k in q_lower or f["name"].lower() in q_lower:
            advs = "\n".join([f"- {a}" for a in f["advantages"]])
            return (
                f"### 🎨 {f['name']}\n\n"
                f"**Specifications:** Thickness {f.get('thickness', 'N/A')}\n\n"
                f"**Key Advantages:**\n{advs}\n\n"
                f"**Applications:** {', '.join(f['applications'])}\n"
                f"**Indicative Cost Range:** `{f['cost_index']}`"
            )

    # 4. Check Hardware
    for k, h in HARDWARE_CATALOG.items():
        if k in q_lower or h["brand"].lower() in q_lower:
            prods = "\n".join([f"- **{p.split(':')[0]}:** {p.split(':')[1] if ':' in p else ''}" for p in h["key_products"]])
            return (
                f"### 🔩 {h['brand']}\n\n"
                f"**Reputation:** {h['market_position']}\n\n"
                f"**Flagship Systems:**\n{prods}\n\n"
                f"**Warranty:** {h['warranty']} | **Pricing Bracket:** `{h['cost_bracket']}`"
            )

    # Fallback catalog
    return (
        f"**Interior Materials & Specifications Knowledge Base:**\n\n"
        f"- **Core Substrates:** BWP Marine Plywood (IS 710), BWR Plywood (IS 303), Commercial Ply, HDHMR, MDF, Particle Board.\n"
        f"- **Surface Finishes:** 1.0mm High Pressure Laminates, Acrylic 2.0mm, Natural Wood Veneer, PU Paint, Lacquered Glass.\n"
        f"- **Fittings & Hardware:** Blum Austria, Hettich Germany, Hafele Germany, Ebco.\n"
        f"- **Countertops:** Engineered Quartz vs Natural Granite.\n\n"
        f"Try asking: *'Compare Plywood vs HDHMR'*, *'What is the difference between Acrylic and Laminate?'*, or *'Why choose Blum hinges for kitchen?'*"
    )
