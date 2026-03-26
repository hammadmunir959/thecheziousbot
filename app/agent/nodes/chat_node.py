from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig

from app.agent.state import State
from app.agent.llm_client import llm, advanced_llm
from app.agent.prompts.prompts import SYSTEM_PROMPT_TEMPLATE, SPAM_PROMPT_TEMPLATE
from app.config.settings import settings
import json
from app.utils.knowledge_base import ESSENTIAL_INFO


_ERROR_MESSAGE = "I'm sorry, I'm having trouble connecting right now. Please try again in a moment."

# ── 1. LLMs ───────────────────────────────────────────────────────────────
_bound_llm = llm.bind(temperature=0).with_retry(stop_after_attempt=settings.MAX_LLM_RETRIES)
_fallback_llm = advanced_llm.bind(temperature=0).with_retry(stop_after_attempt=settings.MAX_LLM_RETRIES)
_chat_llm = _bound_llm.with_fallbacks([_fallback_llm])

# ── 2. Chains ─────────────────────────────────────────────────────────────
_spam_chain = SPAM_PROMPT_TEMPLATE | _chat_llm
_info_chain = SYSTEM_PROMPT_TEMPLATE | _chat_llm

# ── 3. Utilities ──────────────────────────────────────────────────────────
def prepare_input(state: State) -> dict:
    """Prepares the inputs needed by the prompt templates."""
    summary  = state.get("summary", "")
    info_data = state.get("info_data") or json.dumps(ESSENTIAL_INFO, indent=2)
    history  = state.get("messages", [])[-settings.RECENT_CONTEXT_MESSAGES:]

    context = (
        f"<summary>{summary}</summary>\n"
        f"<restaurant_info>{info_data}</restaurant_info>"
    )

    return {
        "context":  context,
        "messages": history,
    }

# ── 4. Node ───────────────────────────────────────────────────────────────
def chat_node(state: State, config: RunnableConfig) -> dict:
    """Conversational responder node for INFO and SPAM queries."""
    
    inputs = prepare_input(state)
    intent = state.get("intent", "INFO")
    chain = _spam_chain if intent == "SPAM" else _info_chain
    
    try:
        response = chain.invoke(inputs, config=config)
            
    except Exception :
        response = AIMessage(content=_ERROR_MESSAGE)

    return {"messages": [response]}