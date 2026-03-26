"""
test_info_node.py — Test suite for info_node.py.
Run: $env:PYTHONPATH="d:/AIIT/Docs/my-project"; python app/agent/tests/test_info_node.py
"""

import sys
import os
import time
import json
from langchain_core.messages import HumanMessage

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.agent.nodes.info_node import info_node

# ── Test Cases ──────────────────────────────────────────────────────────────
TEST_CASES = [
    # MENU
    {"msg": "how much is tikka pizza?", "expected_contains": "Tikka Pizza"},
    {"msg": "show me the burgers", "expected_contains": "Reggy Burger"},
    {"msg": "do you have pasta?", "expected_contains": "Alfredo Pasta"},
    {"msg": "what sizes do you have for pizzas?", "expected_contains": "sizes"},
    
    # LOCATIONS
    {"msg": "where are you located in lahore?", "expected_contains": "Gulberg"},
    {"msg": "do you have a branch in DHA Islamabad?", "expected_contains": "DHA Islamabad"},
    {"msg": "is there a branch in Rawalpindi?", "expected_contains": "Saddar"},
    
    # POLICIES
    {"msg": "is delivery free?", "expected_contains": "Free"},
    {"msg": "what are your hours?", "expected_contains": "11AM-3AM"},
    {"msg": "how can I contact you?", "expected_contains": "111-44-66-99"},
    {"msg": "what is your return policy?", "expected_contains": "refund"},
    
    # FUZZY SEARCH
    {"msg": "how much is tika piza?", "expected_contains": "Tikka Pizza"},
    {"msg": "tell me about bazinga burgir", "expected_contains": "Bazinga Burger"},
    {"msg": "do you have alfredo pastaaa?", "expected_contains": "Alfredo Pasta"},
    
    # CATEGORY SEARCH
    {"msg": "show me the menu", "expected_contains": "pizzas"},
    {"msg": "where are your branches?", "expected_contains": "lahore"},
]

# ── Helpers ──────────────────────────────────────────────────────────────────

def build_state(msg: str) -> dict:
    return {"messages": [HumanMessage(content=msg)]}


def run_tests():
    passed, failed, failures = 0, 0, []

    print("=" * 60)
    print(f"  INFO NODE — {len(TEST_CASES)} TEST CASES")
    print("=" * 60)

    for i, case in enumerate(TEST_CASES, 1):
        expected_kw = case["expected_contains"]

        start = time.time()
        result = info_node(build_state(case["msg"]))
        elapsed = round(time.time() - start, 2)

        info_data = result.get("info_data", "")
        ok = expected_kw.lower() in info_data.lower()

        if ok:
            passed += 1
            status = "PASS"
        else:
            failed += 1
            status = "FAIL"
            failures.append({**case, "actual": info_data})

        print(f"[{i:02d}] {status} | expected_kw={expected_kw:<15} ({elapsed}s)")

    # ── Summary ──────────────────────────────────────────────────────────────
    accuracy = round((passed / len(TEST_CASES)) * 100, 1)
    print()
    print("=" * 60)
    print(f"  PASSED : {passed}/{len(TEST_CASES)}")
    print(f"  FAILED : {failed}/{len(TEST_CASES)}")
    print(f"  ACCURACY: {accuracy}%")
    print("=" * 60)

    if failures:
        print(f"\n  ── FAILURES ({len(failures)}) ──\n")
        for f in failures:
            print(f"  msg      : \"{f['msg']}\"")
            print(f"  expected : contains \"{f['expected_contains']}\"")
            print(f"  actual   : {f['actual'][:200]}...") # truncate for readability
            print()

    return failed


if __name__ == "__main__":
    run_tests()
