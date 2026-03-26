#!/usr/bin/env python3
"""
CLI client for CheziousBot streaming API.
Streams live tokens and handles interrupts.
"""

import json
import sys
import requests

BASE_URL = "http://localhost:8000/api/v1"
USER_ID  = "429844b3-7ee1-4eed-a75f-c193ef222c48"
API_KEY  = "sk-abcd1234"
HEADERS  = {"Content-Type": "application/json", "x-api-key": API_KEY}


def stream(message: str, thread_id: str | None) -> tuple[str | None, bool]:
    """
    Send message to chat-stream endpoint and print live tokens.
    Returns: (thread_id, interrupted_flag)
    """
    payload = {"message": message, "user_id": USER_ID}
    if thread_id:
        payload["thread_id"] = thread_id

    try:
        resp = requests.post(
            f"{BASE_URL}/chat-stream",
            json=payload,
            headers=HEADERS,
            stream=True,
            timeout=(5, 60),
        )
    except requests.ConnectionError:
        print("\n[ERROR] Cannot connect to server.")
        return thread_id, False
    except requests.Timeout:
        print("\n[ERROR] Request timed out.")
        return thread_id, False

    if not resp.ok:
        print(f"\n[ERROR] HTTP {resp.status_code}: {resp.text}")
        return thread_id, False

    thread_id = resp.headers.get("X-Thread-ID", thread_id)
    event = None
    printing = False

    try:
        for line in resp.iter_lines(decode_unicode=True):
            if not line:
                event = None
                continue
            if line.startswith("event:"):
                event = line.removeprefix("event:").strip()
                continue
            if not line.startswith("data:"):
                continue

            try:
                data = json.loads(line.removeprefix("data:").strip())
            except json.JSONDecodeError:
                continue

            content = data.get("content", "")

            if event == "token":
                if not printing:
                    print("\nBOT: ", end="", flush=True)
                    printing = True
                print(content, end="", flush=True)

            elif event == "interrupt":
                print("\n", flush=True)
                print("\n[INTERRUPTED — reply to continue]\n")
                return thread_id, True

            elif event == "done":
                print("\n", flush=True)
                return thread_id, False

            elif event == "error":
                print(f"\n[ERROR] {data.get('detail', 'Unknown error')}", flush=True)
                return thread_id, False

    except requests.RequestException as e:
        print(f"\n[ERROR] Connection lost: {e}")

    return thread_id, False


def cli():
    """Runs the interactive CLI."""
    print("\n━━━ CHEZIOUSBOT CLI ━━━")
    print("/new → new session   /quit → exit\n")

    thread_id = None
    interrupted = False

    while True:
        try:
            prompt = "YOU (reply) >> " if interrupted else "YOU >> "
            msg = input(prompt).strip()
        except (KeyboardInterrupt, EOFError):
            print("\nBye!")
            sys.exit(0)

        if not msg:
            continue
        if msg.lower() in ("/quit", "quit", "exit"):
            sys.exit(0)
        if msg.lower() == "/new":
            thread_id, interrupted = None, False
            print("\n↺ New session.\n")
            continue

        prev_thread = thread_id
        thread_id, interrupted = stream(msg, thread_id)

        if thread_id and not prev_thread:
            print(f"\n[SESSION: {thread_id}]\n")
        else:
            print()


if __name__ == "__main__":
    cli()