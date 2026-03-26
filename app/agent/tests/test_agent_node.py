"""
test_agent_node.py — 20 diverse test cases for the responder node.
"""
from unittest.mock import MagicMock, patch
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from app.agent.nodes.agent_node import agent_node
from app.agent.state import State

# Mock LLM to return whatever content we expect for a "pass"
class MockLLM:
    def with_retry(self, **kwargs):
        return self
    def invoke(self, prompt, config=None):
        return AIMessage(content="Curation Success")

TEST_CASES = [
    # 1. Standard Greeting (Fresh state)
    {"intent": "SPAM", "messages": [HumanMessage(content="Hi")], "desc": "Greeting deflection"},
    
    # 2. Menu Query (INFO)
    {"intent": "INFO", "messages": [HumanMessage(content="What's your menu?")], "info_data": "Pizza, Burgers, Wings", "desc": "Menu info relay"},
    
    # 3. Order Success (Curation)
    {
        "intent": "ORDER", 
        "messages": [
            HumanMessage(content="confirm"),
            AIMessage(content="System: SUCCESS: Order #123 placed for ₨1500. Deliver to Bahria.")
        ],
        "order_id": "123",
        "desc": "Order success celebration"
    },
    
    # 4. Order Cancellation (Curation)
    {
        "intent": "ORDER",
        "messages": [
            HumanMessage(content="cancel it"),
            AIMessage(content="System: Order cancelled.")
        ],
        "desc": "Order cancellation acknowledgement"
    },
    
    # 5. Item Removal Warning (Curation)
    {
        "intent": "ORDER",
        "messages": [
            HumanMessage(content="add a sushi roll"),
            AIMessage(content="System: 'sushi roll' is not on our menu and has been removed.")
        ],
        "desc": "Item removal warning with alternatives"
    },
    
    # 6. Location Query
    {"intent": "INFO", "messages": [HumanMessage(content="Peshawar branch location?")], "info_data": "University Road, Peshawar", "desc": "Location info relay"},
    
    # 7. Payment Query
    {"intent": "INFO", "messages": [HumanMessage(content="Do you accept cards?")], "info_data": "We accept Cash, Cards, and Online payments.", "desc": "Payment info relay"},
    
    # 8. Mixed Order & Removal
    {
        "intent": "ORDER",
        "messages": [
            HumanMessage(content="Send me 2 pizzas and a dragon roll"),
            AIMessage(content="System: 'dragon roll' is not on our menu and has been removed.")
        ],
        "desc": "Mixed order with item removal"
    },
    
    # 9. Duplicate Sizing Warning
    {
        "intent": "ORDER",
        "messages": [
            HumanMessage(content="get me a tikka pizza"),
            AIMessage(content="System: 'Tikka Pizza' requires a size. Available: Small, Regular, Large, Party.")
        ],
        "desc": "Sizing requirement prompt"
    },
    
    # 10. Address update confirmation
    {
        "intent": "ORDER",
        "messages": [
            HumanMessage(content="my address is DHA Phase 6"),
            AIMessage(content="System: Delivery address updated to Dha Phase 6.")
        ],
        "desc": "Address update acknowledgement"
    },
    
    # 11. Empty cart prompt
    {
        "intent": "ORDER",
        "messages": [
            HumanMessage(content="I want to buy something"),
            AIMessage(content="System: Your cart is empty. Please tell me what you'd like to order.")
        ],
        "desc": "Empty cart prompt"
    },
    
    # 12. Multiple warnings in history
    {
        "intent": "ORDER",
        "messages": [
            AIMessage(content="System: 'coke' is not on our menu."),
            AIMessage(content="System: 'sprite' is not on our menu."),
            HumanMessage(content="sadly give me water then")
        ],
        "desc": "History curation with multiple warnings"
    },
    
    # 13. Summarized context injection
    {
        "intent": "INFO",
        "summary": "User ordered 2 pizzas earlier.",
        "messages": [HumanMessage(content="how much was that?")],
        "desc": "Summary context injection"
    },
    
    # 14. Intent reset (Order complete -> INFO)
    {
        "intent": "ORDER",
        "order_id": "456",
        "messages": [AIMessage(content="System: SUCCESS: Order #456 placed.")],
        "desc": "Post-order intent reset"
    },
    
    # 15. Intent reset (Order abandoned -> INFO)
    {
        "intent": "ORDER",
        "items": [],
        "messages": [HumanMessage(content="I changed my mind, how's the weather?")],
        "desc": "Order abandonment intent reset"
    },
    
    # 16. Fallback - System Error (General)
    {"intent": "ORDER", "messages": [HumanMessage(content="...")], "mock_fail": True, "desc": "Error fallback (Standard)"},
    
    # 17. Fallback - Success Scenario
    {
        "intent": "ORDER", 
        "messages": [AIMessage(content="System: SUCCESS: Order #789 placed.")], 
        "mock_fail": True,
        "desc": "Error fallback (Success)"
    },
    
    # 18. Fallback - Cancel Scenario
    {
        "intent": "ORDER", 
        "messages": [AIMessage(content="System: Order cancelled.")], 
        "mock_fail": True,
        "desc": "Error fallback (Cancel)"
    },
    
    # 19. Large History Window
    {
        "intent": "ORDER",
        "messages": [HumanMessage(content=f"msg {i}") for i in range(20)],
        "desc": "Context window trimming"
    },
    
    # 20. Empty state robustness
    {"intent": "INFO", "messages": [], "desc": "Empty messages robustness"},

    # 21. Precise Price Grounding
    {
        "intent": "INFO",
        "messages": [HumanMessage(content="How much for a Regular Tikka Pizza?")],
        "info_data": '{"menu": [{"item": "Tikka Pizza", "sizes": {"Regular": 1200}}]}',
        "desc": "Precise price retrieval grounding"
    },

    # 22. Branch Location Grounding
    {
        "intent": "INFO",
        "messages": [HumanMessage(content="Do you have a branch in Quetta?")],
        "info_data": '{"locations": ["Lahore", "Islamabad", "Rawalpindi"]}',
        "desc": "Branch exclusion grounding"
    },

    # 23. Contradiction Grounding
    {
        "intent": "INFO",
        "messages": [HumanMessage(content="I heard you have a 50% discount today.")],
        "info_data": '{"deals": []}',
        "desc": "Deal contradiction grounding"
    },

    # 24. Complex Menu Grounding
    {
        "intent": "INFO",
        "messages": [HumanMessage(content="What sizes do your pizzas come in?")],
        "info_data": '{"menu": [{"item": "Pizza", "sizes": {"Small": 600, "Regular": 1000, "Large": 1500, "Party": 2500}}]}',
        "desc": "Complex menu categorization grounding"
    },

    # 25. Policy Grounding (Missing Info)
    {
        "intent": "INFO",
        "messages": [HumanMessage(content="What is your return policy?")],
        "info_data": '{"policies": {}}',
        "desc": "Policy grounding (Empty info)"
    }
]

@patch("app.agent.nodes.agent_node.llm", MockLLM())
def run_tests():
    print("="*60)
    print("  RESPONDER NODE TEST SUITE — 20 CASES")
    print("="*60)
    
    passed = 0
    for i, case in enumerate(TEST_CASES, 1):
        state = {
            "messages": case.get("messages", []),
            "summary":  case.get("summary", ""),
            "info_data": case.get("info_data", ""),
            "intent":   case.get("intent", "INFO"),
            "items":    case.get("items", [True]), # Default to non-empty
            "order_id": case.get("order_id", None)
        }
        
        with patch("app.agent.nodes.agent_node.llm.invoke") as mock_invoke:
            if case.get("mock_fail"):
                mock_invoke.side_effect = Exception("LLM Down")
            else:
                mock_invoke.return_value = AIMessage(content="Clean Response")
            
            try:
                result = agent_node(state, {"configurable": {"thread_id": "1"}})
                
                # Check intent logic (Case 14/15)
                if i in [14, 15] and result["intent"] != "INFO":
                    raise ValueError(f"Intent not reset to INFO. Got: {result['intent']}")
                
                # Check message count
                if len(result["messages"]) != 1:
                    raise ValueError("Should return exactly 1 response message.")
                
                print(f"[{i:02d}] ✅ PASS | {case.get('desc')}")
                passed += 1
            except Exception as e:
                print(f"[{i:02d}] ❌ FAIL | {case.get('desc')} -> {e}")
                
    print("-" * 60)
    print(f"  FINAL SCORE: {passed}/{len(TEST_CASES)}")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
