"""
test_agent_grounding.py — Evaluates LLM responses for info-grounding quality.
Shows actual LLM responses for manual judging.
"""
import sys
import json
import time
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig

from ..nodes.agent_node import agent_node
from ..state import State

# ── Grounding Test Cases ─────────────────────────────────────────────────────
TEST_CASES = [
    {
        "desc": "Case 01: Precise Price Check",
        "user_msg": "How much for a Regular Tikka Pizza?",
        "info_data": {"menu": [{"item": "Tikka Pizza", "sizes": {"Regular": 1200, "Large": 1800}}]},
        "grounding_point": "Should state Rs. 1200 or ₨1200 strictly."
    },
    {
        "desc": "Case 02: Location Denial",
        "user_msg": "Do you have a branch in Quetta?",
        "info_data": {"locations": ["Lahore", "Islamabad", "Rawalpindi"]},
        "grounding_point": "Should politely say no or only list Lhr/Isb/Rwp."
    },
    {
        "desc": "Case 03: Fake Deal Denial",
        "user_msg": "Is there a 'Buy 1 Get 2 Free' special today?",
        "info_data": {"deals": []},
        "grounding_point": "Should deny the deal as it's not in the info data."
    },
    {
        "desc": "Case 04: Multi-Item Menu Inquiry",
        "user_msg": "What burgers and pastas do you have?",
        "info_data": {
            "menu": [
                {"name": "Reggy Burger", "price": 400},
                {"name": "Alfredo Pasta", "price": 1100}
            ]
        },
        "grounding_point": "Should list Reggy Burger and Alfredo Pasta with prices."
    },
    {
        "desc": "Case 05: Delivery Policy Adherence",
        "user_msg": "How long does delivery take?",
        "info_data": {"policies": {"delivery": "45-60 minutes."}},
        "grounding_point": "Should state 45-60 minutes exactly as per data."
    },
    {
        "desc": "Case 06: Out-of-Menu Rejection",
        "user_msg": "Can I get a Pepperoni Pizza?",
        "info_data": {"menu": [{"name": "Tikka Pizza"}]},
        "grounding_point": "Should say Pepperoni is not available."
    },
    {
        "desc": "Case 07: Operating Hours Grounding",
        "user_msg": "Are you open at midnight?",
        "info_data": {"policies": {"hours": "11 AM to 11 PM"}},
        "grounding_point": "Should say closed or mention the 11 PM closing time."
    },
    {
        "desc": "Case 08: Empty Data Safety",
        "user_msg": "What is the smallest pizza size?",
        "info_data": {},
        "grounding_point": "Should admit no info vs guessing 'Small'."
    },
    {
        "desc": "Case 09: Conflicting Information",
        "user_msg": "I heard Tikka Pizza is ₨500. Correct?",
        "info_data": {"menu": [{"name": "Tikka Pizza", "price": 1500}]},
        "grounding_point": "Should correct user to ₨1500 based on data."
    },
    {
        "desc": "Case 10: Refund Policy",
        "user_msg": "Can I get a refund if my food is cold?",
        "info_data": {"policies": {"refunds": "Refunds only for burnt pizzas."}},
        "grounding_point": "Should state policy (only for burnt) vs general refund."
    },
    {
        "desc": "Case 11: Alternative Suggestion",
        "user_msg": "Do you have Sushi? If not, what else?",
        "info_data": {"menu": [{"name": "Tikka Pizza"}, {"name": "Euro Sandwich"}]},
        "grounding_point": "Refuse sushi, suggest Tikka Pizza/Euro Sandwich only."
    },
    {
        "desc": "Case 12: Contact Details",
        "user_msg": "How do I call you?",
        "info_data": {"policies": {"contact": "Call 051-1234567"}},
        "grounding_point": "Should give 051-1234567."
    },
    {
        "desc": "Case 13: Size Variant Grounding",
        "user_msg": "Do you have large size for all pizzas?",
        "info_data": {"menu": [{"name": "Special Pizza", "sizes": {"Small": 500}}]},
        "grounding_point": "Should say only Small is available for Special Pizza."
    },
    {
        "desc": "Case 14: Tracking Info",
        "user_msg": "Where is my order?",
        "info_data": {"order_status": "Out for delivery"},
        "grounding_point": "Should state 'Out for delivery'."
    },
    {
        "desc": "Case 15: Greeting + Grounding",
        "user_msg": "Hello! What's the best thing on the menu?",
        "info_data": {"menu": [{"name": "Euro Sandwich", "description": "Highly recommended"}]},
        "grounding_point": "Greet and suggest Euro Sandwich based on 'recommended' tag."
    }
]

def run_grounding_tests():
    print("=" * 80)
    print("  AGENT GROUNDING EVALUATION — RESPONSES FOR JUDGEMENT")
    print("=" * 80)

    for i, case in enumerate(TEST_CASES, 1):
        state = {
            "messages": [HumanMessage(content=case["user_msg"])],
            "info_data": json.dumps(case["info_data"], indent=2),
            "intent": "INFO",
            "summary": ""
        }
        
        print(f"\n[{i:02d}] CASE: {case['desc']}")
        print(f"     USER says: \"{case['user_msg']}\"")
        print(f"     DATA provided:")
        print(f"     {json.dumps(case['info_data'])}")
        print(f"     GOAL: {case['grounding_point']}")
        print("-" * 40)
        
        start = time.time()
        try:
            config = RunnableConfig(configurable={"thread_id": f"test_{i}"})
            result = agent_node(state, config)
            response = result["messages"][-1].content
            elapsed = round(time.time() - start, 2)
            
            print(f"     AI RESPONSE ({elapsed}s):")
            print(f"     {response}")
        except Exception as e:
            print(f"     ❌ ERROR: {str(e)}")
        
        print("-" * 80)

if __name__ == "__main__":
    run_grounding_tests()
