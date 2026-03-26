"""
test_info_parsing.py — Baseline test for category/query extraction.
"""

import sys
import os
import time
from langchain_core.messages import HumanMessage

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.agent.nodes.info_node import _chain

# ── Test Cases ──────────────────────────────────────────────────────────────
TEST_CASES = [
    # GREETINGS/NONE
    {"msg": "Hi there!", "cat": None, "qenv": None},
    {"msg": "Hello, how are you?", "cat": None, "qenv": None},
    
    # MENU
    {"msg": "whats on the menu?", "cat": "menu", "qenv": None},
    {"msg": "how much is tikka pizza?", "cat": "menu", "qenv": "tikka pizza"},
    {"msg": "show me your burgers", "cat": "menu", "qenv": "burgers"},
    {"msg": "do you have any spicy deals?", "cat": "menu", "qenv": "deals"},
    {"msg": "ingredients for fajita pizza", "cat": "menu", "qenv": "fajita pizza"},
    
    # LOCATIONS
    {"msg": "where are your branches?", "cat": "locations", "qenv": None},
    {"msg": "do you have a branch in Lahore?", "cat": "locations", "qenv": "lahore"},
    {"msg": "is there a branch near DHA Islamabad?", "cat": "locations", "qenv": "DHA Islamabad"},
    
    # POLICIES
    {"msg": "what are your opening hours?", "cat": "policies", "qenv": "hours"},
    {"msg": "is delivery free?", "cat": "policies", "qenv": "delivery"},
    {"msg": "how can I contact support?", "cat": "policies", "qenv": "contact"},
    {"msg": "what is your refund policy?", "cat": "policies", "qenv": "refund"},
    
    # AMBIGUOUS/EDGE
    {"msg": "tell me about yourself", "cat": None, "qenv": None},
    {"msg": "what is your best pizza?", "cat": "menu", "qenv": "pizza"},

    # NEW DIVERSE CASES (15+)
    {"msg": "yo, what pizzas you got?", "cat": "menu", "qenv": None}, # Map "what pizzas you got" to full cat menu for now or just None
    {"msg": "is your meat halal?", "cat": "policies", "qenv": "meat"},
    {"msg": "Can I pay with EasyPaisa?", "cat": "policies", "qenv": "payment"},
    {"msg": "how many branches in Rawalpindi?", "cat": "locations", "qenv": "rawalpindi"},
    {"msg": "price of small special pizza", "cat": "menu", "qenv": "special pizza"},
    {"msg": "I am in Saddar, where is the nearest one?", "cat": "locations", "qenv": "saddar"},
    {"msg": "do you have any vegetarian options?", "cat": "menu", "qenv": "veg pizza"},
    {"msg": "when do you close on weekends?", "cat": "policies", "qenv": "hours"},
    {"msg": "is there any discount for students?", "cat": "menu", "qenv": "deals"},
    {"msg": "what is the UAN number?", "cat": "policies", "qenv": "contact"},
    {"msg": "how long after ordering should I expect delivery?", "cat": "policies", "qenv": "delivery"},
    {"msg": "tell me about your burgers price list", "cat": "menu", "qenv": "burgers"},
    {"msg": "do you have any combo deals?", "cat": "menu", "qenv": "deals"},
    {"msg": "I got cold food, what to do?", "cat": "policies", "qenv": "refund"},
    {"msg": "where can I find the Johar Town branch?", "cat": "locations", "qenv": "johar town"},
    {"msg": "shukriya, bohut achay!", "cat": None, "qenv": None},
    {"msg": "kya haal hai?", "cat": None, "qenv": None},
]

def run_tests():
    passed = 0
    print("=" * 60)
    print(f"  INFO PARSING ACCURACY — {len(TEST_CASES)} CASES")
    print("=" * 60)

    for i, case in enumerate(TEST_CASES, 1):
        msg = case["msg"]
        expected_cat = case["cat"]
        expected_query = case["qenv"]

        time.sleep(10) # Delay to avoid rate limits
        try:
            result = _chain.invoke({"user_msg": msg})
            actual_cat = result.category
            actual_query = result.query
            
            # Allow case-insensitive and partial match for query if not None
            cat_ok = actual_cat == expected_cat
            if expected_query is None:
                query_ok = actual_query is None
            else:
                query_ok = actual_query is not None and expected_query.lower() in actual_query.lower()

            if cat_ok and query_ok:
                status = "✅ PASS"
                passed += 1
            else:
                status = "❌ FAIL"
            
            print(f"[{i:02d}] {status} | Msg: \"{msg}\"")
            if status == "❌ FAIL":
                print(f"     Expected: cat={expected_cat}, query={expected_query}")
                print(f"     Actual:   cat={actual_cat}, query={actual_query}")
        except Exception as e:
            print(f"[{i:02d}] ❌ ERR  | Msg: \"{msg}\" -> {str(e)}")

    accuracy = round((passed / len(TEST_CASES)) * 100, 2)
    print("-" * 60)
    print(f"  FINAL ACCURACY: {accuracy}%")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
