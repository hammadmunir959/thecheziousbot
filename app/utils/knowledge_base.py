"""
app/utils/knowledge_base.py
"""

import difflib
from typing import Any, Dict, List, Optional, Union

# ── Data ──────────────────────────────────────────────────────────────────────

MENU: Dict[str, List[Dict]] = {
    "pizzas": [
        {"name": "Tikka Pizza",        "sizes": {"Small": 690, "Regular": 1250, "Large": 1650, "Party": 2700}, "description": "Local flavor: Tikka pizza."},
        {"name": "Fajita Pizza",       "sizes": {"Small": 690, "Regular": 1250, "Large": 1650, "Party": 2700}, "description": "Local flavor: Fajita pizza."},
        {"name": "Lover Pizza",        "sizes": {"Small": 690, "Regular": 1250, "Large": 1650, "Party": 2700}, "description": "Local flavor: Lover pizza."},
        {"name": "Tandoori Pizza",     "sizes": {"Small": 690, "Regular": 1250, "Large": 1650, "Party": 2700}, "description": "Local flavor: Tandoori pizza."},
        {"name": "Spicy Pizza",        "sizes": {"Small": 690, "Regular": 1250, "Large": 1650, "Party": 2700}, "description": "Local flavor: Spicy pizza."},
        {"name": "Veg Pizza",          "sizes": {"Small": 690, "Regular": 1250, "Large": 1650, "Party": 2700}, "description": "Local flavor: Veg pizza."},
        {"name": "Supreme Pizza",      "sizes": {"Small": 690, "Regular": 1350, "Large": 1750, "Party": 2850}, "description": "Sooper flavor: Supreme pizza."},
        {"name": "Black Pepper Pizza", "sizes": {"Small": 690, "Regular": 1350, "Large": 1750, "Party": 2850}, "description": "Sooper flavor: Black Pepper pizza."},
        {"name": "Sausage Pizza",      "sizes": {"Small": 690, "Regular": 1350, "Large": 1750, "Party": 2850}, "description": "Sooper flavor: Sausage pizza."},
        {"name": "Cheese Pizza",       "sizes": {"Small": 690, "Regular": 1350, "Large": 1750, "Party": 2850}, "description": "Sooper flavor: Cheese pizza."},
        {"name": "Pepperoni Pizza",    "sizes": {"Small": 690, "Regular": 1350, "Large": 1750, "Party": 2850}, "description": "Sooper flavor: Pepperoni pizza."},
        {"name": "Mushroom Pizza",     "sizes": {"Small": 690, "Regular": 1350, "Large": 1750, "Party": 2850}, "description": "Sooper flavor: Mushroom pizza."},
        {"name": "Special Pizza",      "sizes": {"Small": 790, "Regular": 1550, "Large": 2050, "Party": 3200}, "description": "Cheezy Treat: Special pizza."},
        {"name": "Behari Pizza",       "sizes": {"Small": 790, "Regular": 1550, "Large": 2050, "Party": 3200}, "description": "Cheezy Treat: Behari pizza."},
        {"name": "Extreme Pizza",      "sizes": {"Small": 790, "Regular": 1550, "Large": 2050, "Party": 3200}, "description": "Cheezy Treat: Extreme pizza."},
        {"name": "Malai Crust",        "price": 1200, "description": "Crust upgrade for Regular/Large."},
        {"name": "Stuffed Crust",      "price": 1450, "description": "Crust upgrade for Regular/Large."},
        {"name": "Crown Crust",        "price": 1550, "description": "Crust upgrade for Regular/Large."},
        {"name": "Thin Crust",         "price": 1550, "description": "Crust upgrade for Regular/Large."},
    ],
    "burgers": [
        {"name": "Reggy Burger",    "price": 390,  "description": "Regular burger."},
        {"name": "Bazinga Burger",  "price": 560,  "description": "Bazinga burger."},
        {"name": "Bazooka Burger",  "price": 630,  "description": "Bazooka burger."},
        {"name": "Supreme Burger",  "price": 730,  "description": "Supreme burger."},
        {"name": "Mexican Sandwich","price": 600,  "description": "Mexican sandwich."},
        {"name": "Euro Sandwich",   "price": 920,  "description": "Euro sandwich."},
        {"name": "Pizza Stacker",   "price": 920,  "description": "Pizza stacker."},
    ],
    "sides": [
        {"name": "Baked Wings (6pc)",  "price": 600,  "description": "Baked chicken wings."},
        {"name": "Flaming Wings (6pc)","price": 650,  "description": "Flaming chicken wings."},
        {"name": "Sticks",             "price": 630,  "description": "Chicken sticks."},
        {"name": "Calzone",            "price": 1150, "description": "Cheezy calzone."},
        {"name": "Rolls",              "price": 690,  "description": "Rolls."},
        {"name": "Nuggets (5pc)",      "price": 450,  "description": "Chicken nuggets."},
        {"name": "Fries",              "price": 220,  "description": "Regular fries."},
    ],
    "pastas": [
        {"name": "Alfredo Pasta", "price": 1050, "description": "Alfredo pasta."},
        {"name": "Crunchy Pasta", "price": 950,  "description": "Crunchy pasta."},
    ],
}

from typing import Dict, List

LOCATIONS: Dict[str, List[str]] = {
    "lahore": [
        "Baghbanpura Branch, GT Rd, Baghbanpura, Lahore, Punjab 54000",
        "Jail Road Branch, Plot No 394, 1 Shadman Colony, opposite Kinnaird College, Jail Road, Lahore 54000",
        "Johar Town Branch, 446, Block G3, Phase 2, Johar Town, Lahore, Punjab",
        "Shadbagh Branch, 4 Qamar Park, Shad Bagh, Lahore, Punjab 05450",
        "Nespak Branch, 1A Canal Bank Road, Block A, Nespak Housing Society Phase 2, Lahore, Punjab 54770",
        "DHA Phase 4 Branch, 223-FF, DHA Phase 4, Lahore, Pakistan",
        "Gulshan-e-Ravi Branch, 416, Main Blvd, Gulshan-e-Ravi, Block C, Lahore, Punjab 54500",
    ],
    "islamabad": [
        "Centaurus Branch, 4th Floor, Centaurus Mall, Food Court, F 8/4, Islamabad 44000",
        "Giga Mall Branch, Food Court, 2nd Floor, Giga Mall, Islamabad 44000",
        "G-13 Branch, Shop 1, Khawaja Plaza, G-13/1, Islamabad",
        "Golra Mor Branch, Riphah International Uni Road, Golra Morr, Islamabad 46000",
        "Taramri Branch, Street A3, Lehtrar Rd, Chowk, Taramri, Islamabad 45550",
        "F-7 Markaz Branch, 6b Bhittai Rd, F-7 Markaz, Islamabad 46000",
        "F-11 Markaz Branch, Liberty Square Plaza, Hilal Road, F-11 Markaz, Islamabad 44000",
        "I-8 Markaz Branch, Shop #26, Pakland Plaza, I-8 Markaz, Islamabad 46000",
        "Ghouri Town Branch, Al-Kareem Plaza, Street 8B, Main Double Road, Ghouri Phase 5 Town, Islamabad",
        "G-15 Markaz Branch, Shop G-01/02, Rehman Plaza, G-15 Markaz, Islamabad 46000",
        "E-11 Branch, Shop No. 4, Imperial Plaza, Services Society SCHS, E-11/2, Islamabad",
    ],
    "rawalpindi": [
        "Wah Cantt Branch, Main Grand Trunk Rd, near Sadat PSO Pump, Wah Cantt, Rawalpindi, Punjab",
        "Commercial Market Branch, Nadir Plaza, 4th Rd, opp. New Town Police Station, Commercial Block D Market, Rawalpindi",
        "Adyala Road Branch, H346+WFQ, Adyala Rd, Rawalpindi, Punjab 46000",
        "Scheme 3 Branch, Plot 52, Commercial Area Rd, Chaklala Housing Scheme 3, Rawalpindi 46000",
        "Bahria Phase 7 Branch, D-ONE Plaza, near Green Valley Parking, Bahria Town Intellectual Village, Phase 7, Rawalpindi",
        "Bahria Phase 7 (2) Branch, Plot 21-Food Street, Spring North Bahria, Phase 7, Rawalpindi",
        "Saddar Branch, M65, 6/A Adam Jee Rd, near GTS Adda, Saddar, Rawalpindi, Punjab 46000",
        "PWD Branch, 342-G, NPF, A-Block Main PWD Rd, PWD, Rawalpindi",
        "Kalma Chowk Branch, Plot No. CB-369/370, Main Dhamial Road, Kalma Chowk, Rawalpindi",
    ],
    "peshawar": [
        "HBK Branch, XFFF+P9R, Achini Payan, Peshawar, Khyber Pakhtunkhwa",
        "Tehkal Branch, Tehkal, Peshawar, Khyber Pakhtunkhwa",
        "Hayatabad Branch, SuperMarket, Phase-1, Hayatabad, Peshawar, Khyber Pakhtunkhwa 25000",
    ],
    "sahiwal": [
        "Pilot School Branch, Gujjar Ahata Chowk, Mazdoor Pulli Road, Gujar Ahata, Sahiwal District, Punjab 57000",
        "Palm View Branch, Palm View Market, Sahiwal, Sahiwal District, Punjab",
    ],
    "faisalabad": [
        "Rehmat Chowk Branch, 191 Rehmat Chowk, W Canal Rd, Raza Town, Faisalabad 38000",
        "Samanabad Branch, Block A Samanabad, Faisalabad, Punjab",
    ],
    "okara": [
        "Okara Branch, Tehsil Rd, Aamir Colony, Okara, Punjab 56300",
    ],
    "pattoki": [
        "Pattoki Branch, Shahrah-e-Quaid-e-Azam Rd, Faisal Colony, Pattoki, Kasur, Punjab",
    ],
    "mian_channu": [
        "Mian Channu Branch, Multan Mian Channu Road, Amin Trade Center, Mian Channu, Khanewal, Punjab",
    ],
}

POLICIES: Dict[str, str] = {
    "delivery":            "Free home delivery on all orders. Place orders via the Cheezious app, website (cheezious.com), phone, or Foodpanda.",
    "delivery_time":       "Standard delivery takes approximately 30–45 minutes depending on branch and location.",
    "hours":               "Daily: 12:00 PM – 12:00 AM (most branches). Late-night service available till 3:00 AM at select branches.",
    "ramadan_hours":       "Ramadan Timing: 5:00 PM – 3:00 AM.",
    "ordering_methods":    "1) Cheezious App (exclusive discounts & offers). 2) Website: cheezious.com. 3) Phone: (city code) 111-44-66-99. 4) Foodpanda (select areas only).",
    "payment":             "Currently Cash on Delivery only. Online payments (credit/debit card, JazzCash, EasyPaisa) are NOT accepted as of 2026.",
    "returns_and_refunds": "Refunds are transferred back via your selected payment method. Contact support within a reasonable time of delivery for incorrect or unsatisfactory orders.",
    "halal":               "All food is prepared with 100% Halal-certified meat, freshly sourced and compliant with Islamic dietary guidelines.",
    "reservations":        "Table reservations are available by calling your nearest branch directly.",
    "privacy":             "Personal data (name, contact, address) is collected for order processing only. Data is never sold or rented to third parties. Security measures are in place to prevent unauthorized access.",
    "contact":             "UAN: (city code) 111-44-66-99 | Email: support@cheezious.com | Web: cheezious.com | Instagram: @cheeziouspakistan",
}

ESSENTIAL_INFO: Dict[str, Any] = {
    "hours": POLICIES["hours"],
    "contact": POLICIES["contact"],
    "delivery": POLICIES["delivery"],
    "locations": {
        "cities": list(LOCATIONS.keys()),
        "summary": "We have multiple branches in Lahore, Islamabad, and Rawalpindi."
    },
    "menu_categories": list(MENU.keys()),
    "menu_info": "We serve different types of Pizzas, Burgers, Sides, and Pastas. Ask me for the menu to see all items."
}

# ── Search ────────────────────────────────────────────────────────────────────

_KB = {"menu": MENU, "locations": LOCATIONS, "policies": POLICIES}

def get_all_items() -> Dict[str, Union[int, Dict[str, int]]]:
    """Flatten the menu into a single dict mapping item names to prices or size dicts."""
    flat: Dict[str, Union[int, Dict[str, int]]] = {}
    for category, items in MENU.items():
        for item in items:
            if isinstance(item, dict) and "name" in item:
                name = item["name"]
                if "price" in item:
                    flat[name] = item["price"]
                elif "sizes" in item:
                    flat[name] = item["sizes"]
    return flat

def get_menu_by_category() -> Dict[str, List[Dict]]:
    """Return the menu grouped by category."""
    return MENU


def search(
    category: Optional[str] = None,
    query: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Search the knowledge base and always return ESSENTIAL_INFO alongside results.

    Returns:
        {
            "results": <matched data or None>,
            "essential_info": ESSENTIAL_INFO
        }
    """

    # ── Normalize ─────────────────────────────────────────────────────────
    category = category.lower().strip() if category else None
    query    = query.lower().strip()    if query    else None

    _META_QUERIES = {"menu", "locations", "policies", "branches", "all", "everything"}
    
    if query in _META_QUERIES:
        query = None

    # ── Early exit: no intent ─────────────────────────────────────────────
    if not category and not query:
        return _response(results=None)

    # ── Pick sources ──────────────────────────────────────────────────────
    sources: Dict[str, Any] = (
        {category: _KB[category]}
        if category and category in _KB
        else dict(_KB)
    )

    # ── No query: return the whole category (or all sources) ──────────────
    if not query:
        results = _single_value(sources) if len(sources) == 1 else sources
        return _response(results)

    # ── Run search ────────────────────────────────────────────────────────
    q = query.replace("-", " ").strip()
    hits = _search_all(sources, q)

    results = _flatten(hits) if hits else None
    return _response(results)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _response(results: Any) -> Dict[str, Any]:
    return {"results": results, "essential_info": ESSENTIAL_INFO}


def _single_value(d: dict) -> Any:
    return next(iter(d.values()))


def _fuzzy(a: str, b: str) -> bool:
    return difflib.SequenceMatcher(None, a, b).ratio() > 0.6


def _item_name(item: Any) -> str:
    raw = item.get("name", "") if isinstance(item, dict) else str(item)
    return raw.lower().replace("-", " ")


def _to_text(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(_to_text(v) for v in value.values())
    if isinstance(value, list):
        return " ".join(_to_text(v) for v in value)
    return str(value).lower().replace("-", " ")


def _search_all(sources: Dict[str, Any], q: str) -> Dict[str, Any]:
    """Dispatch each source to its dedicated search function."""
    hits: Dict[str, Any] = {}

    for src, data in sources.items():
        if src == "locations":
            result = _search_locations(data, q)
        elif src == "policies":
            result = _search_policies(data, q)
        else:
            result = _search_menu(data, q)

        if result:
            hits[src] = result

    return hits


def _search_locations(data: Dict[str, list], q: str) -> Dict[str, list]:
    """
    Match against city keys directly.
    Priority: exact → prefix → fuzzy.
    """
    if q in data:
        return {q: data[q]}

    return {
        city: branches
        for city, branches in data.items()
        if city.startswith(q) or _fuzzy(q, city)
    }


def _search_policies(data: Dict[str, str], q: str) -> Dict[str, str]:
    """Match against policy keys and their string values."""
    return {
        key: val
        for key, val in data.items()
        if isinstance(val, str) and (q in key or q in val.lower() or _fuzzy(q, key))
    }


def _search_menu(data: Dict[str, list], q: str) -> Dict[str, list]:
    """
    Match menu subcategories (e.g. "pizzas") or individual items.
    Priority: subcat name → exact item → prefix → substring → fuzzy.
    """
    hits: Dict[str, list] = {}

    for subcat, items in data.items():
        if not isinstance(items, list):
            continue

        # Subcat-level match (handles "pizza" → "pizzas" via strip-s)
        if subcat == q or subcat.rstrip("s") == q.rstrip("s"):
            hits[subcat] = items
            continue

        # Item-level match
        matched = (
            [i for i in items if _item_name(i) == q]
            or [i for i in items if _item_name(i).startswith(q)]
            or [i for i in items if q in _to_text(i)]
            or [i for i in items if _fuzzy(q, _item_name(i))]
        )
        if matched:
            hits[subcat] = matched

    return hits


def _flatten(hits: Dict[str, Any]) -> Any:
    """
    Unwrap single-entry dicts for cleaner output.
    Preserves structure when there are multiple sources or subcategories.
    """
    if len(hits) == 1:
        src, subcats = next(iter(hits.items()))
        if isinstance(subcats, dict) and len(subcats) == 1:
            return _single_value(subcats)  # single src, single subcat → raw value
        return subcats                     # single src, multiple subcats → subcat dict

    return hits                            # multiple srcs → full nested dict
