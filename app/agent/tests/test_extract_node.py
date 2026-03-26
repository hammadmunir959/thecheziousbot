"""
test_extract_node.py — Comprehensive test for order extraction accuracy.
"""

import sys
import os
import time
from langchain_core.messages import HumanMessage, AIMessage

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.agent.nodes.extract_node import  _chain
from app.utils.utils import build_menu_summary

# ── Test Cases ──────────────────────────────────────────────────────────────
TEST_CASES = [
    # 3. Explicit Item Removal (Cart Update)
    {
        "msg": "Remove the pasta and just give me 3 beef burgers instead",
        "cart": [{"item": "Alfredo Pasta", "size": None, "quantity": 1, "price": 1050}],
        "expected_items": [{"item": "Bazooka Burger", "size": None, "quantity": 3}],
    },
    # 4. Correcting Quantity Mid-Sentence
    {
        "msg": "Get me 2 pepperonis, wait no, make that 5 pepperoni pizzas",
        "expected_items": [{"item": "Pepperoni Pizza", "size": None, "quantity": 5}],
    },
    # 5. Complex Address + Landmark Extraction
    {
        "msg": "Deliver it to DHA Phase 5, right behind the Jalal Sons. I'll pay cash.",
        "expected_items": [],
        "payment": "cash",
        "address": "DHA Phase 5, behind Jalal Sons"
    },
    # 6. Size Upgrade of Existing Item
    {
        "msg": "Actually, make that pizza a Large one",
        "cart": [{"item": "Fajita Pizza", "size": "Small", "quantity": 1, "price": 690}],
        "expected_items": [{"item": "Fajita Pizza", "size": "Large", "quantity": 1}],
    },
    # 7. Multi-Category Extraction (Slang)
    {
        "msg": "1 crown crust pizza and 2 large cokes",
        "expected_items": [
            {"item": "Crown Crust", "size": None, "quantity": 1},
            {"item": "Coke", "size": "Large", "quantity": 2}
        ],
    },
    # 8. Negation and Preference (Hallucination Check)
    {
        "msg": "I don't want any mushrooms, just give me a cheese pizza",
        "expected_items": [{"item": "Cheese Pizza", "size": None, "quantity": 1}],
    },
    # 9. Payment Method Switching
    {
        "msg": "Change my payment to Bank Transfer and send it to F-11 markaz",
        "initial_payment": "cash",
        "expected_items": [],
        "payment": "online",
        "address": "F-11 markaz"
    },
    # 10. Indirect Quantity (Relative to Cart)
    {
        "msg": "Add one more of the same burger",
        "cart": [{"item": "Bazooka Burger", "size": None, "quantity": 1, "price": 630}],
        "expected_items": [{"item": "Bazooka Burger", "size": None, "quantity": 2}],
    },
    # 11. Ambiguous Intent (Query + Order)
    {
        "msg": "How much is the Alfredo? Okay, add two of those to my order",
        "expected_items": [{"item": "Alfredo Pasta", "size": None, "quantity": 2}],
    },
    # 12. Full Cart Clearance
    {
        "msg": "Forget everything, I want to start a new order with just fries",
        "cart": [
            {"item": "Tikka Pizza", "size": "Large", "quantity": 2},
            {"item": "Bazinga Burger", "size": None, "quantity": 1}
        ],
        "expected_items": [{"item": "Fries", "size": None, "quantity": 1}],
    },
    # 13. Heavy Typo / Phonetic Matching
    {
        "msg": "mujhe ek beari piza chahye small",
        "expected_items": [{"item": "Behari Pizza", "size": "Small", "quantity": 1}],
    },
    # 14. Split Quantities
    {
        "msg": "Give me 2 small and 1 large tandoori pizzas",
        "expected_items": [
            {"item": "Tandoori Pizza", "size": "Small", "quantity": 2},
            {"item": "Tandoori Pizza", "size": "Large", "quantity": 1}
        ],
    },
    # 15. Address Update Only (Maintain Cart)
    {
        "msg": "I'm at the office now, send it to Blue Area instead",
        "cart": [{"item": "Veg Pizza", "size": "Regular", "quantity": 1}],
        "expected_items": [{"item": "Veg Pizza", "size": "Regular", "quantity": 1}],
        "address": "Blue Area"
    }
]

def parse_cart(cart: list[dict]) -> list:
    """Convert test-case cart dicts to MenuItem objects."""
    from app.schemas.schemas import MenuItem
    items = []
    for entry in cart:
        items.append(MenuItem(
            item=entry["item"],
            size=entry.get("size"),
            quantity=entry.get("quantity", 1),
            price=entry.get("price", 0),
        ))
    return items


def run_tests():
    from app.agent.nodes.nodes_utils import prepare_extraction_input
    from app.agent.state import State

    passed = 0
    
    print("=" * 60)
    print(f"  EXTRACT NODE ACCURACY — {len(TEST_CASES)} CASES")
    print("=" * 60)

    for i, case in enumerate(TEST_CASES, 1):
        msg      = case["msg"]
        cart     = case.get("cart", [])        # Use real cart items now
        time.sleep(2)

        try:
            mock_state = State(
                messages=[HumanMessage(content=msg)],
                items=parse_cart(cart),
                summary="",
                delivery_address=case.get("initial_address", ""),
                payment_method=case.get("initial_payment", ""),
                order_errors=[],
                order_status=case.get("order_status"),
            )

            inputs = prepare_extraction_input(mock_state)
            result = _chain.invoke(inputs)

            # ── Validate items ──────────────────────────────────────────
            expected_items = case.get("expected_items", [])
            actual_items   = result.items or []

            items_ok = len(expected_items) == len(actual_items)
            if items_ok:
                for exp in expected_items:
                    found = any(
                        (exp["item"].lower() in act.item.lower() or act.item.lower() in exp["item"].lower())
                        and (str(exp["size"]).lower() == str(act.size).lower() if exp["size"] else not act.size or act.size.lower() in ("none", "null", ""))
                        and exp["quantity"] == act.quantity
                        for act in actual_items
                    )
                    if not found:
                        items_ok = False
                        break

            # ── Validate payment ────────────────────────────────────────
            payment_ok = True
            if case.get("payment"):
                payment_ok = (result.payment_method or "").lower() == case["payment"]

            # ── Validate address ────────────────────────────────────────
            address_ok = True
            if case.get("address"):
                address_ok = case["address"].lower() in (result.delivery_address or "").lower()

            if items_ok and payment_ok and address_ok:
                print(f"[{i:02d}] ✅ PASS | {msg}")
                passed += 1
            else:
                print(f"[{i:02d}] ❌ FAIL | {msg}")
                if not items_ok:
                    print(f"     Items - Expected: {expected_items}")
                    print(f"             Actual:   {[(it.item, it.size, it.quantity) for it in actual_items]}")
                if not payment_ok:
                    print(f"     Payment - Expected: {case['payment']}, Actual: {result.payment_method}")
                if not address_ok:
                    print(f"     Address - Expected: {case['address']}, Actual: {result.delivery_address}")

        except Exception as e:
            print(f"[{i:02d}] ❌ ERR  | {msg} -> {e}")

    accuracy = round((passed / len(TEST_CASES)) * 100, 2)
    print("-" * 60)
    print(f"  FINAL EXTRACTION ACCURACY: {accuracy}%  ({passed}/{len(TEST_CASES)})")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()
