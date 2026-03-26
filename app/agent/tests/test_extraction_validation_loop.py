import sys
import os
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from langchain_core.messages import HumanMessage
from langgraph.types import Command
from app.agent.graphs.graph import workflow

TEST_CASES = [
    {
        "name": "Generic Item -> Clarification -> Address/Payment",
        "messages": [
            "I want 2 pizzas",
            "make them large tikka pizzas",
            "deliver to office 44 blue area, I'll pay by cash"
        ],
        "expected_items": [("Tikka Pizza", "Large", 2)],
        "expected_address_contains": "blue area",
        "expected_payment": "cash",
        "expected_status": "extracted"
    },
    {
        "name": "Missing Size -> Provide Size -> Location/Payment",
        "messages": [
            "give me one fajita pizza",
            "regular please",
            "f-7 islamabad, pay online"
        ],
        "expected_items": [("Fajita Pizza", "Regular", 1)],
        "expected_address_contains": "f-7 islamabad",
        "expected_payment": "online",
        "expected_status": "extracted"
    },
    {
        "name": "Complete Item -> missing Address -> missing Payment",
        "messages": [
            "1 party lover pizza",
            "bahria town rwp",
            "card"
        ],
        "expected_items": [("Lover Pizza", "Party", 1)],
        "expected_address_contains": "bahria town",
        "expected_payment": "card",
        "expected_status": "extracted"
    },
    {
        "name": "Add items -> Change quantity -> Complete order",
        "messages": [
            "2 zinger burgers and 1 fries",
            "actually make it 3 zingers",
            "cash, G-13"
        ],
        "expected_items": [("Bazinga Burger", None, 3), ("Fries", None, 1)],
        "expected_address_contains": "g-13",
        "expected_payment": "cash",
        "expected_status": "extracted"
    },
    {
        "name": "Out of bounds item -> Correction -> Complete order",
        "messages": [
            "I want a sushi",
            "sorry, I mean a beef burger",
            "sadapay, dha phase 2"
        ],
        "expected_items": [("Bazooka Burger", None, 1)],
        "expected_address_contains": "dha phase 2",
        "expected_payment": "online",
        "expected_status": "extracted"
    },
    {
        "name": "Add item -> Change Size -> Complete order",
        "messages": [
            "1 tandoori pizza small",
            "make the pizza a large one instead",
            "E-11 islamabad, online"
        ],
        "expected_items": [("Tandoori Pizza", "Large", 1)],
        "expected_address_contains": "e-11 islamabad",
        "expected_payment": "online",
        "expected_status": "extracted"
    },
    {
        "name": "Initial Request -> Cancel Order",
        "messages": [
            "I want pasta",
            "cancel my order"
        ],
        "expected_items": [],
        "expected_address_contains": None,
        "expected_payment": None,
        "expected_status": "cancelled" # Test that interrupting loop can lead to cancellation
    },
    {
        "name": "Crust Upgrade (Warning) -> Resolve by ordering Pizza -> Complete order",
        "messages": [
            "add stuffed crust",
            "oh, I also want a regular supreme pizza",
            "cash to iqbal town lahore"
        ],
        "expected_items": [("Stuffed Crust", None, 1), ("Supreme Pizza", "Regular", 1)],
        "expected_address_contains": "iqbal town lahore",
        "expected_payment": "cash",
        "expected_status": "extracted"
    },
    {
        "name": "Unrecognized Size (size:null) -> Clarify Size -> Complete order",
        "messages": [
            "I want a huge cheese pizza",
            "party size",
            "johar town, card"
        ],
        "expected_items": [("Cheese Pizza", "Party", 1)],
        "expected_address_contains": "johar town",
        "expected_payment": "card",
        "expected_status": "extracted"
    },
    {
        "name": "Item Swap Mid-Order",
        "messages": [
            "regular veg pizza",
            "swap it for a large spicy pizza",
            "cash saddar rawalpindi"
        ],
        "expected_items": [("Spicy Pizza", "Large", 1)],
        "expected_address_contains": "saddar rawalpindi",
        "expected_payment": "cash",
        "expected_status": "extracted"
    }
]

def run_suite():
    print("=" * 60)
    print(f"  EXTRACTION & VALIDATION LOOP SUITE — {len(TEST_CASES)} CASES")
    print("=" * 60)

    passed = 0

    for idx, case in enumerate(TEST_CASES, 1):
        print(f"\n[{idx:02d}] 🚀 RUNNING: {case['name']}")
        
        # Unique thread for each testcase
        config = {"configurable": {"thread_id": f"test_loop_{idx}_{int(time.time())}"}}
        messages = case["messages"]
        
        try:
            # 1. Start the first message
            state_input = {"messages": [HumanMessage(content=messages[0])]}
            for event in workflow.stream(state_input, config=config):
                pass
            
            # 2. Feed remaining messages responding to interrupts
            for i in range(1, len(messages)):
                state = workflow.get_state(config)
                # Ensure we hit an interrupt before sending the next message
                if state.tasks and state.tasks[0].interrupts:
                    resume_val = messages[i]
                    for event in workflow.stream(Command(resume=resume_val), config=config):
                        pass
                else:
                    # If it wasn't interrupted but order is cancelled, that's fine
                    if state.values.get("order_status") != "cancelled":
                        print(f"  ❌ Failed to interrupt at message {i}: {messages[i]}")
                        break
            
            # 3. Assertions
            final_state = workflow.get_state(config).values
            items = final_state.get('items', [])
            addr = final_state.get('delivery_address')
            pay = final_state.get('payment_method')
            status = final_state.get('order_status')

            # Build actual items tuple list
            actual_items = []
            for item in items:
                actual_items.append((item.item, item.size, item.quantity))
            
            success = True
            
            # Check items softly (fuzzy name matches, etc)
            exp_items = case["expected_items"]
            if len(actual_items) != len(exp_items):
                success = False
            else:
                for exp in exp_items:
                    found = False
                    for act in actual_items:
                        if exp[0].lower() in act[0].lower() or act[0].lower() in exp[0].lower():
                            # Check size
                            if str(exp[1]).lower() == str(act[1]).lower():
                                # Check quantity
                                if exp[2] == act[2]:
                                    found = True
                    if not found:
                        success = False
                        break

            # Check address
            if case["expected_address_contains"]:
                if not addr or case["expected_address_contains"].lower() not in addr.lower():
                    success = False
            elif addr is not None:
                success = False

            # Check payment
            if pay != case["expected_payment"]:
                success = False

            # Check status
            if case["expected_status"] == "extracted":
                if status not in ("extracted", "validated", "extracting"):
                    success = False
            elif status != case["expected_status"]:
                success = False

            if success:
                print(f"[{idx:02d}] ✅ PASS")
                passed += 1
            else:
                print(f"[{idx:02d}] ❌ FAIL")
                print(f"  Expected Items: {exp_items} | Actual: {actual_items}")
                print(f"  Expected Addr: {case['expected_address_contains']} | Actual: {addr}")
                print(f"  Expected Pay: {case['expected_payment']} | Actual: {pay}")
                print(f"  Expected Status: {case['expected_status']} | Actual: {status}")

        except Exception as e:
            print(f"[{idx:02d}] ❌ ERROR | {str(e)}")

    print("-" * 60)
    print(f"FINAL SUITE ACCURACY: {passed}/{len(TEST_CASES)} ({(passed/len(TEST_CASES))*100:.0f}%)")
    print("=" * 60)

if __name__ == "__main__":
    run_suite()
