import re
from typing import Dict, Any, List, Set

# Domain Stopwords to avoid spurious product/category matches
STOPWORDS = {
    "i", "we", "a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "of",
    "with", "by", "is", "are", "was", "were", "be", "been", "have", "has", "had",
    "manufacture", "manufacturing", "manufacturer", "make", "producing", "produce",
    "sell", "selling", "distribute", "fabricate", "our", "my", "company", "business",
    "want", "need", "standard", "standards", "bis", "indian", "india", "which",
    "what", "please", "help", "suggest", "recommend", "give", "me", "tell", "show",
    "official", "clause", "exist", "knowledge", "base", "information", "details",
    "that", "does", "not", "applicable", "apply", "applies", "requirement", "requirements",
    "some", "any", "how", "can", "could", "would", "about"
}

# Industry Domain Taxonomy Mapping
DOMAIN_TAXONOMY = {
    "lighting": ["led", "light", "lights", "luminaire", "luminaires", "lamp", "lantern", "emergency light", "bulb"],
    "battery": ["battery", "batteries", "cell", "cells", "lithium", "li-ion", "rechargeable", "power bank", "accumulator"],
    "electronics": ["laptop", "computer", "mobile", "phone", "tablet", "adapter", "charger", "monitor", "display"],
    "electrical": ["plug", "plugs", "socket", "sockets", "switch", "switches", "cable", "wire", "iron", "appliance"],
    "water": ["water", "drinking water", "bottled water", "mineral water", "jar", "potable", "tap water"],
    "automotive safety": ["helmet", "helmets", "two wheeler", "motorcycle", "rider", "protective headgear"],
    "civil & construction": ["cement", "portland", "opc", "concrete", "steel", "rebar", "rebars", "tmt", "iron rod"],
    "precious metals": ["gold", "silver", "jewellery", "ornament", "bangle", "ring", "hallmark", "huid", "karat", "carat"],
    "child safety": ["toy", "toys", "doll", "game", "plush", "child", "children"]
}

TECHNICAL_TERMS = {
    "led", "emergency", "luminaire", "rechargeable", "luminous", "photometric",
    "dielectric", "insulation", "creepage", "flammability", "tensile", "yield",
    "compressive", "proof stress", "fe 500d", "opc 53", "coliform", "pesticide",
    "microbial", "fire assay", "xrf", "titration", "huid", "fineness", "cml",
    "qco", "isi", "crs", "lithium-ion", "short circuit", "overcharge"
}

def analyze_product_description(description: str) -> Dict[str, Any]:
    """
    Analyzes natural-language product descriptions to extract:
    - cleaned product text
    - inferred product entities
    - matched category candidates
    - extracted domain keywords
    - relevant technical terms
    """
    if not description:
        return {
            "product": "",
            "category": "Unspecified",
            "keywords": [],
            "technical_terms": []
        }

    raw_lower = description.lower().strip()
    # Normalize punctuation
    cleaned = re.sub(r'[^\w\s\-]', ' ', raw_lower)
    tokens = [t.strip() for t in cleaned.split() if t.strip()]

    # Extract informative keywords
    keywords = [t for t in tokens if t not in STOPWORDS and len(t) > 2]

    # Extract technical terms
    matched_tech = [t for t in tokens if t in TECHNICAL_TERMS]
    # Check multi-word technical terms
    for phrase in ["emergency light", "emergency lights", "rechargeable led", "lithium ion", "fe 500d", "opc 53", "fire assay", "drinking water"]:
        if phrase in raw_lower and phrase not in matched_tech:
            matched_tech.append(phrase)

    # Infer primary category and candidate product name using word-boundary matching
    matched_categories = []
    for category_name, category_keywords in DOMAIN_TAXONOMY.items():
        score = 0
        for ck in category_keywords:
            if re.search(r'\b' + re.escape(ck) + r'\b', raw_lower):
                score += 1
        if score > 0:
            matched_categories.append((category_name.title(), score))

    matched_categories.sort(key=lambda x: x[1], reverse=True)
    inferred_category = matched_categories[0][0] if matched_categories else "General Industrial Goods"

    # Inferred product entity: reconstruct salient product phrase
    product_tokens = [k for k in keywords if k not in ["type", "model", "supply", "production", "good", "quality"]]
    inferred_product = " ".join(product_tokens) if product_tokens else description.strip()

    return {
        "product": inferred_product,
        "category": inferred_category,
        "category_candidates": [c[0] for c in matched_categories],
        "keywords": keywords,
        "technical_terms": list(set(matched_tech))
    }
