import uuid
import logging
from pprint import pprint
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from .graph import workflow

logging.getLogger("httpx").setLevel(logging.WARNING)


def _is_interrupted(config: dict) -> bool:
    state = workflow.get_state(config)
    return bool(state.next and state.tasks and state.tasks[0].interrupts)


def _get_reply(config: dict) -> str:
    state = workflow.get_state(config)

    if state.next and state.tasks and state.tasks[0].interrupts:
        return str(state.tasks[0].interrupts[0].value)

    for msg in reversed(state.values.get("messages", [])):
        if msg.type == "ai" and msg.content.strip():
            return msg.content.strip()

    return ""


def _stream_run(graph_input, config: dict):
    print("\n--- STREAM START ---")

    for update in workflow.stream(graph_input, config=config, stream_mode="updates"):
        for node, data in update.items():
            if node == "__interrupt__":
                continue
            print(f"\n[NODE: {node}]")
            pprint(data, indent=2, width=80)
            print("-" * 30)

    print("--- STREAM END ---\n")

def run_cli():
    print("\n--- CHEZIOUS DEBUG CLI ---")

    user_id = "429844b3-7ee1-4eed-a75f-c193ef222c48"
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"user_id": user_id, "thread_id": thread_id}}

    print(f"SESSION: {thread_id} | USER: {user_id}\n")

    while True:
        try:
            if _is_interrupted(config):
                print(f"INTERRUPT: {_get_reply(config)}")
                user_input = input("USER (resume) >> ").strip()
                if user_input.lower() in ("exit", "quit"):
                    break
                graph_input = Command(resume=user_input)
            else:
                user_input = input("USER >> ").strip()
                if user_input.lower() in ("exit", "quit"):
                    break
                if not user_input:
                    continue
                graph_input = {"messages": [HumanMessage(content=user_input)]}

            _stream_run(graph_input, config)
            print(f"BOT: {_get_reply(config)}\n")

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            import traceback
            print(f"\n[ERROR]: {e}")
            traceback.print_exc()
            break

    print("Bye!")


if __name__ == "__main__":
    run_cli()