"""
utils.py — Helpers for order validation, cart management, and prompt building.
"""

from __future__ import annotations

import difflib
import logging
import re
from functools import lru_cache

from ..schemas.schemas import MenuItem
from .knowledge_base import get_all_items

logger = logging.getLogger(__name__)


_CRUST_UPGRADES = {"malai crust", "stuffed crust", "crown crust", "thin crust"}

_GENERIC_CATEGORIES = frozenset({
    "burger", "burgers", "pizza", "pizzas", "drink", "drinks",
    "beverage", "beverages", "dessert", "desserts", "sandwich",
    "sandwiches", "pasta", "pastas", "wing", "wings",
})


_CITY_ALIASES: dict[str, str] = {
    "lhr": "lahore",
    "isb": "islamabad",
    "rwp": "rawalpindi",
    "pesh": "peshawar",
    "ksr": "kasur",
    "swl": "sahiwal",
    "okr": "okara",
    "fsd": "faisalabad",
    "ptk": "pattoki",
    "mcn": "mian channu",
}




def format_order_summary(items: list, total: int, address: str, payment: str) -> str:
    """Renders the final order details for user review."""
    item_lines_list = []
    for i in items:
        line = f"  • {i.quantity}x {i.item} ({i.size or 'Standard'})"
        if i.quantity > 1:
            line += f" — ₨{i.price} each = ₨{i.quantity * i.price}"
        else:
            line += f" — ₨{i.price}"
        item_lines_list.append(line)
    
    item_lines = "\n".join(item_lines_list)
    
    return (
        "### [Order Summary]\n\n"
        f"{item_lines}\n\n"
        "---\n"
        f"Address: {address}\n"
        f"Payment: {payment.upper()}\n"
        "---\n"
        f"TOTAL BILL: ₨{total}\n\n"
        "Please reply with **'confirm'** to place your order, or **'cancel'** to abort."
    )


def _resolve_items(raw_items: list[MenuItem], price_map: dict, size_based: set) -> tuple[list[MenuItem], list[str]]:
    """Pre-validate LLM-extracted items against live menu. Returns (resolved, warnings)."""
    resolved: list[MenuItem] = []
    warnings: list[str] = []
    all_keys = list(price_map.keys())
    
    #  
    for mi in raw_items:
        name = (mi.item or "").strip().lower()
        sz   = (mi.size or "").strip().lower()
        if sz in ("no size", "none", "null", ""):
            sz = None
            
        if not name:
            continue

        found_sz = None
        
        # 1. Strict Generic Item Filtering
        # If the user specifically asks for generalized items (e.g. "burger", "pizza", "drinks"), 
        # do not aggressively attempt to match them against the menu yet. They require user clarification.
        if name in _GENERIC_CATEGORIES:
            resolved.append(MenuItem(item=name.title(), size=sz.title() if sz else None, quantity=mi.quantity, price=0))
            warnings.append(f"'{mi.item}' is a little broad. Could you specify which one you would like?")
            continue
        
        # 2. Handle inline sizes (e.g. 'Large Pizza')
        for s in ["small", "regular", "large", "party"]:
            if s in name:
                found_sz = s
                # Strip the size from the name
                name = name.replace(f"({s})", "").replace(s, "").replace("()", "").strip()
                break
        
        if found_sz and not sz:
            sz = found_sz

        if name in _CRUST_UPGRADES:
            warnings.append(
                f"'{mi.item}' is a crust upgrade add-on, not a standalone item. "
                "To add a crust upgrade, please order a pizza first and mention the crust type."
            )
            continue

        # Strip common suffixes for cleaner base name matching
        stripped = name
        for suffix in [" pizza", " burger", " sandwich", " pasta"]:
            if name.endswith(suffix):
                stripped = name[: -len(suffix)].strip()
                break

        # Check if base item is size-based (pizzas etc)
        base = name if (name in size_based) else (stripped if stripped in size_based else None)

        if base:
            # If size is provided, try exact match or fuzzy match valid sizes
            if sz:
                key = f"{base} {sz}"
                if key in price_map:
                    resolved.append(MenuItem(item=base.title(), size=sz.title(), quantity=mi.quantity, price=price_map[key]))
                    continue
                # Try fuzzy matching the size if it's slightly off
                valid_sizes = [k[len(base):].strip() for k in price_map if k.startswith(base + " ")]
                close = difflib.get_close_matches(sz, valid_sizes, n=1, cutoff=0.5)
                if close:
                    corrected_key = f"{base} {close[0]}"
                    warnings.append(f"Size '{sz}' for '{base.title()}' corrected to '{close[0].title()}'.")
                    resolved.append(MenuItem(item=base.title(), size=close[0].title(), quantity=mi.quantity, price=price_map[corrected_key]))
                else:
                    # No size match, keep it as size=None for validation_node to handle
                    resolved.append(MenuItem(item=base.title(), size=None, quantity=mi.quantity, price=0))
            else:
                # No size provided but it's a size-based item
                resolved.append(MenuItem(item=base.title(), size=None, quantity=mi.quantity, price=0))
            continue

        # Flat-price lookup
        found = False
        # 1. Exact or suffixed match
        for lookup in [name, stripped]:
            if lookup in price_map:
                resolved.append(MenuItem(item=lookup.title(), size=None, quantity=mi.quantity, price=price_map[lookup]))
                found = True
                break
        
        # 2. Substring match or Portional recomposition (handles 'baked wings' -> 'Baked Wings (6pc)' or splitting)
        if not found:
            for k, p in price_map.items():
                # Check if name matches base, and sz matches content in parentheses OR name matches base with portion stripped
                base_in_menu = k.split(" (")[0]
                portion_in_menu = k.split("(")[1].split(")")[0] if "(" in k and ")" in k else None
                
                # Match 1: name matches base, sz is None or matches portion
                if (name == base_in_menu or stripped == base_in_menu):
                    if not sz or (portion_in_menu and sz == portion_in_menu.lower()):
                        resolved.append(MenuItem(item=k.title(), size=None, quantity=mi.quantity, price=p))
                        found = True
                        break

        if not found:
            # Fuzzy match the item name since it wasn't a direct hit
            search_key = f"{name} {sz}".strip() if sz else name
            close = difflib.get_close_matches(search_key, all_keys, n=3, cutoff=0.5)
            if close:
                alts = ", ".join(c.title() for c in close)
                warnings.append(f"'{mi.item}' is not on our menu. Did you mean one of these? {alts}")
            else:
                warnings.append(f"'{mi.item}' is not on our menu and has been removed.")

    return resolved, warnings


# ---------------------------------------------------------------------------
# Price map
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def build_price_map() -> tuple[dict[str, int], set[str]]:
    """Return (price_map, size_based_keys) from the live menu KB."""
    flat_menu = get_all_items()
    price_map: dict[str, int] = {}
    size_based: set[str] = set()

    for name, value in flat_menu.items():
        name_lower = name.strip().lower()
        if name_lower in _CRUST_UPGRADES:
            continue

        aliases = [name_lower]
        for suffix in [" pizza", " burger", " sandwich", " pasta"]:
            if name_lower.endswith(suffix):
                aliases.append(name_lower[: -len(suffix)].strip())

        if isinstance(value, int):
            for alias in aliases:
                price_map[alias] = value
        elif isinstance(value, dict):
            for alias in aliases:
                size_based.add(alias)
                for size, price in value.items():
                    key = f"{alias} {size.strip().lower()}"
                    try:
                        price_map[key] = int(price)
                    except (TypeError, ValueError):
                        continue

    return price_map, size_based


# ---------------------------------------------------------------------------
# Cart validation & merging
# ---------------------------------------------------------------------------

def merge_items(items: list[MenuItem]) -> list[MenuItem]:
    """Merge duplicate items (case-insensitive name + size match)."""
    merged: dict[tuple[str, str], MenuItem] = {}
    for mi in items:
        if not mi.item:
            continue
        name = mi.item.strip().lower()
        sz   = (mi.size or "").strip().lower()
        key  = (name, sz)
        if key in merged:
            merged[key].quantity += mi.quantity
        else:
            merged[key] = MenuItem(
                item=mi.item.strip().title(),
                size=mi.size.strip().title() if mi.size else None,
                quantity=mi.quantity,
                price=mi.price,
            )
    return list(merged.values())




# ---------------------------------------------------------------------------
# Order-level field validation
# ---------------------------------------------------------------------------

def normalize_address(address: str) -> str:
    """Expand known city abbreviations in an address string."""
    if not address:
        return address
    result = address
    for alias, full in _CITY_ALIASES.items():
        result = re.sub(rf'\b{re.escape(alias)}\b', full.title(), result, flags=re.IGNORECASE)
    return result




# ---------------------------------------------------------------------------
# Total
# ---------------------------------------------------------------------------

def compute_total(items: list[MenuItem]) -> int:
    return sum(mi.price * mi.quantity for mi in items)


# ---------------------------------------------------------------------------
# Menu summary for extraction prompt
# ---------------------------------------------------------------------------

def build_menu_summary() -> str:
    """Render a compact, LLM-readable menu grouped by category."""
    from .knowledge_base import get_menu_by_category
    menu  = get_menu_by_category()
    lines: list[str] = []
    for category, items in menu.items():
        lines.append(f"\n{category.upper()}:")
        for item in items:
            name = item["name"]
            if name.lower() in _CRUST_UPGRADES:
                lines.append(f"  - {name}: ₨{item['price']} [CRUST ADD-ON — not a standalone item]")
            elif "price" in item:
                lines.append(f"  - {name}: ₨{item['price']}")
            elif "sizes" in item:
                sizes = ", ".join(item["sizes"].keys())
                lines.append(f"  - {name} [Sizes: {sizes}]")
    return "\n".join(lines).strip()


# ---------------------------------------------------------------------------
# Order Cancellation Helpers
# ---------------------------------------------------------------------------

def is_cancel_command(text: str) -> bool:
    """Check if the user input is a cancellation keyword."""
    if not text:
        return False
    text_lower = text.strip().lower()
    keywords = {"cancel", "abort", "cancel order", "cancel my order"}
    return text_lower in keywords


def is_confirmed(text: str) -> bool:
    """Check if the user input is a confirmation keyword."""
    if not text:
        return False
    text_lower = text.strip().lower()
    keywords = {"confirm", "yes", "okay", "correct", "place order", "done", "confirmed"}
    return text_lower in keywords



