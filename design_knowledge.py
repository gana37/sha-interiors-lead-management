"""
design_knowledge.py - Interior Design Expertise & Spatial Architecture Knowledge Base
SHA Interface Interiors - AI-Powered Lead Management System

Authoritative knowledge base for interior design styles, room-by-room space planning,
lighting architectures, Vastu considerations, color harmony, and commercial layouts.
"""

import sys
from typing import Dict, List, Optional, Any

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ==============================================================================
# 1. DESIGN STYLES REPOSITORY
# ==============================================================================

DESIGN_STYLES: Dict[str, Dict[str, Any]] = {
    "modern": {
        "title": "Modern Interior Design",
        "description": "Rooted in early-to-mid 20th century principles emphasizing crisp lines, simple color palettes, and materials including metal, glass, and steel.",
        "key_characteristics": [
            "Clean, straight architectural lines with minimal ornamentation",
            "Monochromatic or neutral base with bold single-color accents",
            "Open-plan layouts maximizing natural light",
            "Functional furniture with exposed legs and low profiles",
            "Absence of clutter and ornate moldings"
        ],
        "materials": ["Polished concrete", "Tempered glass", "Engineered quartz", "Satin chrome / matte black metal", "Laminate"],
        "color_palette": ["Crisp white", "Warm grey", "Charcoal", "Muted taupe", "Accent cobalt blue or mustard yellow"],
        "ideal_for": ["2BHK/3BHK urban apartments", "High-rise condominiums", "Studio flats"],
        "cost_tier": "Medium to High"
    },
    "contemporary": {
        "title": "Contemporary Interior Design",
        "description": "Reflects the design ethos of the 'here and now'. Fluid, constantly evolving, combining soft curves with sleek straight lines and high tactile richness.",
        "key_characteristics": [
            "Curved organic furniture paired with geometric architectural elements",
            "Layered textural depth (boucle, brushed brass, fluted panels, fluted glass)",
            "Integrated architectural ambient lighting (magnetic track, linear profile)",
            "Neutral base punctuated with rich jewel tones",
            "Seamless indoor-outdoor transitions"
        ],
        "materials": ["Fluted MDF panels", "Tinted lacquered glass", "Brushed gold/brass PVD metal", "Italian Statuario/Dyna marble", "Velvet & boucle fabrics"],
        "color_palette": ["Off-white", "Warm beige", "Olive green", "Terracotta", "Burnished copper"],
        "ideal_for": ["Luxury villas", "Premium 3BHK/4BHK residences", "Penthouse suites"],
        "cost_tier": "High to Luxury"
    },
    "minimalist": {
        "title": "Minimalist Interior Design",
        "description": "'Less is more' philosophy. Focuses on spatial serenity, functional purity, hidden storage, and pristine clean surfaces without visual noise.",
        "key_characteristics": [
            "Strictly decluttered spaces with handle-less flush cabinetry (push-to-open or Gola profiles)",
            "Concealed storage solutions eliminating visible clutter",
            "Abundant negative space and natural ventilation",
            "Multi-functional, highly purposeful furniture",
            "Emphasis on light, form, and exceptional craftsmanship over decoration"
        ],
        "materials": ["Seamless micro-cement / lime wash", "Ultra-matte anti-fingerprint laminates", "Natural light oak", "Plain quartz countertops"],
        "color_palette": ["Pure white", "Alabaster", "Soft ash grey", "Light stone", "Deep black accents"],
        "ideal_for": ["Urban compact homes", "Architectural penthouses", "Modern IT professionals"],
        "cost_tier": "Medium to Premium (precision detailing required)"
    },
    "scandinavian": {
        "title": "Scandinavian (Scandi) Design",
        "description": "Nordic concept of 'Hygge' prioritizing warmth, cozy simplicity, light-toned natural woods, functionality, and connection with nature.",
        "key_characteristics": [
            "Bright, airy spaces designed to reflect natural daylight",
            "Light-toned natural woods (Birch, Ash, White Oak)",
            "Cozy textiles (wool throws, linen drapes, cotton rugs)",
            "Indoor botanical integration (fiddle-leaf fig, monstera)",
            "Slender, tapered furniture legs and gentle organic silhouettes"
        ],
        "materials": ["Light oak / ash veneer", "White PU matte finishes", "Natural linen & cotton", "Rattan & cane accents", "Ceramic planters"],
        "color_palette": ["Snow white", "Pale sky blue", "Sage green", "Blush pink", "Light wood tones"],
        "ideal_for": ["1BHK/2BHK/3BHK family homes", "Naturally lit apartments", "Budget-to-mid renovations"],
        "cost_tier": "Budget to Medium"
    },
    "luxury": {
        "title": "Luxury & High-End Bespoke Interiors",
        "description": "Opulent, custom-crafted living environments characterized by rare natural stones, exotic veneers, bespoke metal joinery, and smart automation.",
        "key_characteristics": [
            "Book-matched Italian marble feature walls and flooring",
            "Exotic natural wood veneers finished with high-gloss polyester or PU",
            "PVD-coated stainless steel (rose gold, champagne, titanium) screens and inlays",
            "Full smart home lighting automation (DALI, KNX, Lutron control)",
            "Custom oversized furniture and walk-in dressing suites with backlit glass"
        ],
        "materials": ["Statuario / Michaelangelo marble", "Onyx back-lit panels", "Smoked eucalyptus veneer", "Top-grain Italian leather", "Crystal chandeliers"],
        "color_palette": ["Champagne gold", "Charcoal grey", "Deep emerald", "Royal navy", "Rich ivory"],
        "ideal_for": ["Luxury villas in Bangalore/Hyderabad", "Duplex penthouses", "Sprawling 4BHK apartments"],
        "cost_tier": "Ultra-Luxury"
    },
    "traditional_indian": {
        "title": "Traditional Indian / Classical Vernacular",
        "description": "Rich heritage aesthetics featuring solid carved teakwood, brass accents, handloom upholstery, jharokha niches, and vibrant ethnic accents.",
        "key_characteristics": [
            "Carved solid wood furniture (Teak, Sheesham, Rosewood)",
            "Brass and copper hardware, bells, and urlis",
            "Traditional Indian textiles (Ikat, Kalamkari, Silk, Brocade)",
            "Pooja mandir with intricate jali work and temple architecture",
            "Terracotta tiles, Athangudi patterns, or polished Kota stone"
        ],
        "materials": ["Solid Teakwood", "Antique brass fittings", "Cane weaving", "Hand-painted tiles", "Carved stone"],
        "color_palette": ["Deep maroon", "Mustard yellow", "Peacock blue", "Burnt orange", "Warm teak brown"],
        "ideal_for": ["Ancestral homes", "Spacious residential villas", "Dedicated pooja room suites"],
        "cost_tier": "Medium to High (handcrafted woodwork)"
    },
    "industrial": {
        "title": "Industrial Interior Design",
        "description": "Urban warehouse loft aesthetic celebrating exposed structural elements, raw brickwork, ductwork, metal pipes, and rustic distressed timber.",
        "key_characteristics": [
            "Exposed red brick walls or raw concrete plaster finishes",
            "Open ceilings with exposed black electrical conduits and HVAC ducts",
            "Distressed reclaimed timber paired with black wrought iron",
            "Edison filament bulb fixtures and caged track lights",
            "Expansive black grid crittall-style glass partitions"
        ],
        "materials": ["Exposed clay brick veneer", "Raw MS steel angles", "Reclaimed pine wood", "Distressed leather", "Concrete screed"],
        "color_palette": ["Rust terracotta", "Matte black", "Gunmetal grey", "Raw umber", "Tan leather"],
        "ideal_for": ["Duplex lofts", "Creative studios & startup offices", "Bachelor pads", "Cafes"],
        "cost_tier": "Medium"
    },
    "space_saving": {
        "title": "Space-Saving / Compact Urban Architecture",
        "description": "Ergonomically engineered for urban 1BHK & 2BHK apartments where every millimeter is maximized with convertible, multi-functional modularity.",
        "key_characteristics": [
            "Hydraulic lift-up beds with massive under-mattress storage",
            "Fold-down wall-mounted study/dining desks (Murphy desks)",
            "Sliding floor-to-ceiling wardrobes eliminating door swing clearance",
            "Modular kitchen pull-out larders and blind corner organizers",
            "Pocket doors and sliding glass partition screens"
        ],
        "materials": ["High-grade BWP marine plywood", "Durable 1mm scratch-resistant laminate", "Heavy-duty hydraulic mechanisms", "Sleek aluminum profiles"],
        "color_palette": ["Off-white & mirror reflections to amplify perceived space", "Pastel tones", "Light beech wood"],
        "ideal_for": ["Compact 1BHK & 2BHK apartments in Bangalore/Hyderabad/Mumbai", "Studio apartments"],
        "cost_tier": "Budget to Medium"
    },
    "vastu": {
        "title": "Vastu Shastra Principles for Interior Planning",
        "description": "Ancient Indian architectural science optimizing cosmic energy flows (Pancha Bhootas) through directional zoning and orientation.",
        "key_characteristics": [
            "North-East (Ishanya): Kept light, clutter-free; ideal for Pooja Mandir or Meditation corner",
            "South-East (Agni): Governed by Fire element; ideal for Kitchen cooking hob (face East while cooking)",
            "South-West (Nairutya): Governed by Earth; stability; ideal for Master Bedroom & heaviest wardrobes",
            "North-West (Vayu): Governed by Air; movement; ideal for Guest Bedroom, dining, or living lounge",
            "Central Core (Brahmasthan): Kept open, hollow, and free of heavy structural load"
        ],
        "materials": ["Natural brass for North-East", "Warm woods for South-West", "Cool stones for North"],
        "color_palette": ["NE: White, light yellow, light blue", "SE: Orange, soft red, peach", "SW: Earthy brown, almond, tan", "NW: Silver, white, cream"],
        "ideal_for": ["All residential interior planning across South India"],
        "cost_tier": "Applicable across all tiers"
    }
}

# ==============================================================================
# 2. FUNCTIONAL AREAS REPOSITORY
# ==============================================================================

ROOM_GUIDELINES: Dict[str, Dict[str, Any]] = {
    "modular_kitchen": {
        "title": "Modular Kitchen Architecture",
        "work_triangle": "The Golden Work Triangle states the sum of distances between Sink, Hob, and Refrigerator should be between 12 to 26 feet for optimal cooking efficiency.",
        "common_layouts": {
            "L-Shape": "Ideal for small to medium square kitchens. Highly efficient work triangle leaving space for a small breakfast table.",
            "Parallel / Galley": "Most ergonomic layout preferred by professional chefs. Opposing counters separate wet (sink) and hot (hob) zones safely.",
            "U-Shape": "Maximum countertop workspace and storage. Best for large closed kitchen spaces.",
            "Island Kitchen": "Luxury open layout with freestanding central counter for prep, hob, or breakfast bar seating."
        },
        "cabinetry_zones": [
            "Base Units (Height 34-36 inches incl countertop): Tandem drawers for pots/pans, bottle pull-outs, under-sink dustbin unit.",
            "Wall Units (Depth 12-14 inches, height 24-30 inches): Crockery shelves, spices, microwave niche.",
            "Loft Units (Up to ceiling): Seasonal storage, large pressure cookers, festive dinnerware.",
            "Tall Pantry Unit: 6-tier swing or pull-out wire/glass baskets for grocery storage."
        ],
        "lighting": "Under-cabinet warm white LED strip (3000K-4000K, minimum CRI 90) to eliminate shadows on prep counters; anti-glare recessed ceiling downlights."
    },
    "living_room": {
        "title": "Living & Foyer Room Architecture",
        "key_zones": [
            "Foyer / Entryway: Shoe console with seating bench, coat hooks, accent mirror for final check, warm welcoming light.",
            "Seating Zone: Minimum 3-seater sofa + 2 accent chairs or L-shaped sectional. Coffee table clearance minimum 18 inches from sofa.",
            "TV Entertainment Unit: Wall-mounted console with concealed wiring, fluted acoustic panelling, floating bottom ledge.",
            "Partition Screen: CNC laser cut jali or metal-wooden display shelving to subtly delineate dining from living."
        ],
        "lighting_layers": "Layer 1: Ambient false ceiling cove (indirect warm 3000K). Layer 2: Accent spotlights on artwork/wall panels (15° beam). Layer 3: Task floor lamp by reading armchair."
    },
    "master_bedroom": {
        "title": "Master Bedroom Suite",
        "key_elements": [
            "King-Size Bed Placement: Position headboard against solid wall (South or West per Vastu), with 30 inches walkway clearance on both sides.",
            "Wardrobe Unit: Floor-to-ceiling (with loft). Sliding shutters for compact spaces (<12ft room width) or hinged shutters for wide rooms.",
            "Dressing Unit: Full-length mirror with vertical strip lighting, hidden vanity shelves for perfumes/cosmetics.",
            "Bedside Lighting: Low-hanging warm pendants or dual-switched reading goose-neck lights avoiding glare on sleeping partner."
        ],
        "ergonomics": "Wardrobe hanging rod at 60-66 inches height for long dresses/kurtas; 40 inches for shirts and trousers."
    },
    "wardrobe_systems": {
        "title": "Wardrobe Systems & Internal Ergonomics",
        "types": {
            "Hinged Shutter Wardrobes": "Doors open 90°-110°. Provides 100% full view of contents at once. Requires 30-36 inches clearance in front of wardrobe.",
            "Sliding Shutter Wardrobes": "Doors slide smoothly on top and bottom aluminum tracks. Zero swing space required—ideal for modern rooms. Only 50% open at a time.",
            "Walk-In Closets": "Dedicated dressing room with island jewellery drawer, glass display cabinets with motion-sensor LED strips."
        },
        "internal_configuration": [
            "Men's section: Double hanging (two 40-inch rods), tie/belt organizer pullout, 4 shallow drawers for watches/cufflinks.",
            "Women's section: Long hanging zone (60-64 inches) for sarees/gowns, saree pullout hangers, soft-close velvet jewellery tray.",
            "Top Loft: Large open compartments for duvets, suitcases, and extra blankets."
        ]
    },
    "false_ceiling": {
        "title": "False Ceiling Design & Acoustics",
        "materials": "Saint-Gobain Gyproc 12.5mm gypsum plasterboard mounted on GI galvanized steel framework.",
        "types": [
            "Perimeter Drop with Cove: 12-18 inch border dropped by 5-6 inches around room perimeter, concealing LED strip for soft indirect ambient wash.",
            "Geometric Minimal Drop: Flush ceiling with clean recessed linear profile magnetic tracks.",
            "Wooden Rafter Feature: Veneered or laminated MDF rafters spanning living or dining ceiling for organic warmth."
        ],
        "fan_and_ac_clearance": "Ensure minimum 12 inches clearance between ceiling fan blades and cove edges to avoid strobe/flicker effect."
    }
}

# ==============================================================================
# 3. KNOWLEDGE LOOKUP API
# ==============================================================================

def get_style_info(style_name: str) -> Optional[Dict[str, Any]]:
    """Retrieves detailed knowledge for an interior design style."""
    key = style_name.lower().strip().replace(" ", "_").replace("-", "_")
    return DESIGN_STYLES.get(key)


def get_room_guidelines(room_name: str) -> Optional[Dict[str, Any]]:
    """Retrieves spatial planning guidelines for a functional area."""
    key = room_name.lower().strip().replace(" ", "_").replace("-", "_")
    for k, v in ROOM_GUIDELINES.items():
        if key in k or k in key:
            return v
    return None


def search_design_knowledge(query: str) -> str:
    """
    Searches the design knowledge base and formats a rich, structured answer.
    """
    q_lower = query.lower()

    # 1. Check style match
    for style_key, style_data in DESIGN_STYLES.items():
        if style_key in q_lower or style_data["title"].lower() in q_lower:
            chars = "\n".join([f"- {c}" for c in style_data["key_characteristics"]])
            mats = ", ".join(style_data["materials"])
            colors = ", ".join(style_data["color_palette"])
            return (
                f"### 🏛️ {style_data['title']}\n\n"
                f"{style_data['description']}\n\n"
                f"**Key Design Characteristics:**\n{chars}\n\n"
                f"**Signature Materials:** {mats}\n\n"
                f"**Recommended Color Palette:** {colors}\n\n"
                f"**Best Suited For:** {', '.join(style_data['ideal_for'])}\n"
                f"**Typical Cost Tier:** `{style_data['cost_tier']}`"
            )

    # 2. Check room guidelines match
    for room_key, room_data in ROOM_GUIDELINES.items():
        if room_key in q_lower or any(word in q_lower for word in room_key.split("_")):
            res = f"### 📐 {room_data['title']}\n\n"
            if "work_triangle" in room_data:
                res += f"**Golden Work Triangle:** {room_data['work_triangle']}\n\n"
            if "common_layouts" in room_data:
                res += "**Recommended Layouts:**\n"
                for lay, desc in room_data["common_layouts"].items():
                    res += f"- **{lay}:** {desc}\n"
                res += "\n"
            if "cabinetry_zones" in room_data:
                res += "**Cabinetry & Ergonomic Zones:**\n"
                for z in room_data["cabinetry_zones"]:
                    res += f"- {z}\n"
                res += "\n"
            if "key_elements" in room_data:
                res += "**Key Spatial Elements:**\n"
                for el in room_data["key_elements"]:
                    res += f"- {el}\n"
                res += "\n"
            if "lighting" in room_data:
                res += f"**Lighting Strategy:** {room_data['lighting']}\n"
            if "lighting_layers" in room_data:
                res += f"**Lighting Layers:** {room_data['lighting_layers']}\n"
            return res

    # 3. Vastu query
    if "vastu" in q_lower:
        vastu = DESIGN_STYLES["vastu"]
        chars = "\n".join([f"- {c}" for c in vastu["key_characteristics"]])
        return (
            f"### 🧭 {vastu['title']}\n\n"
            f"{vastu['description']}\n\n"
            f"**Core Directional Principles:**\n{chars}\n\n"
            f"**Recommended Colors by Direction:** {', '.join(vastu['color_palette'])}"
        )

    # Fallback catalog
    styles_list = ", ".join([v["title"] for v in DESIGN_STYLES.values()])
    rooms_list = ", ".join([v["title"] for v in ROOM_GUIDELINES.values()])
    return (
        f"**Interior Design Knowledge Base:**\n\n"
        f"I can advise on styles: *{styles_list}*.\n\n"
        f"I can also provide layout & ergonomic recommendations for: *{rooms_list}*.\n\n"
        f"Try asking: *'Explain Scandinavian design'*, *'What is the best layout for a modular kitchen?'*, or *'What are the Vastu rules for master bedroom?'*"
    )
