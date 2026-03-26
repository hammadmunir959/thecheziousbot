import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.utils.knowledge_base import search_knowledge_base, get_menu_item, get_policy

def run_tests():
    print("Testing Exact Match...")
    res = search_knowledge_base("menu", "tikka pizza")
    assert res is not None, "Expected result for 'tikka pizza'"
    assert isinstance(res, list), "Expected list of matches"
    assert len(res) > 0, "Expected at least one match"
    assert res[0]["name"] == "Tikka Pizza", f"Expected 'Tikka Pizza', got {res[0]['name']}"
    print("OK")

    print("Testing Fuzzy Match...")
    res = search_knowledge_base("menu", "tika piza")
    assert res is not None, "Expected result for 'tika piza'"
    assert isinstance(res, list), "Expected list of matches"
    assert len(res) > 0, "Expected at least one match"
    assert res[0]["name"] == "Tikka Pizza", f"Expected 'Tikka Pizza', got {res[0]['name']}"
    print("OK")

    print("Testing Category Match...")
    res = search_knowledge_base("menu", "pizzas")
    assert res is not None, "Expected result for 'pizzas'"
    assert isinstance(res, list), "Expected list of items for category 'pizzas'"
    assert len(res) > 10, "Expected multiple pizzas in the list"
    print("OK")

    print("Testing Location Match...")
    res = search_knowledge_base("locations", "rawalpindi")
    assert res is not None, "Expected result for 'rawalpindi'"
    assert isinstance(res, list), "Expected list of locations"
    assert "Saddar" in res, "Expected 'Saddar' in rawalpindi locations"
    print("OK")

    print("Testing Policy Match...")
    res = get_policy("delivery")
    assert res is not None, "Expected result for 'delivery' policy"
    assert "Free" in res, "Expected 'Free' in delivery policy"
    print("OK")

    print("Testing Global Search...")
    res = search_knowledge_base(None, "cheezious.com")
    assert res is not None, "Expected result for global search"
    assert "cheezious.com" in str(res), "Expected URL in search results"
    print("OK")
    
    print("\nAll tests passed successfully!")

if __name__ == "__main__":
    run_tests()
