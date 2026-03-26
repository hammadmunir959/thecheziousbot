"""
classify_intent_node.py — Lightweight intent classification.
Classifies user intent as: ORDER / INFO / SPAM.
"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from ..llm_client import llm, advanced_llm
from ..state import State
from ...schemas.schemas import IntentClassification
from ..prompts.prompts import INTENT_CLASSIFICATION_PROMPT
from ...config.settings import settings

# ----------------------------------------------------------------------------------------- 

_prompt = ChatPromptTemplate([
    ("system", INTENT_CLASSIFICATION_PROMPT),
    MessagesPlaceholder("history"),        # recent conversation context
    ("human", "Classify this: {user_msg}"), # explicit last message to classify
])


_primary = advanced_llm.bind(temperature=0).with_structured_output(IntentClassification).with_retry(stop_after_attempt=settings.MAX_LLM_RETRIES)
_secondary = llm.bind(temperature=0).with_structured_output(IntentClassification).with_retry(stop_after_attempt=settings.MAX_LLM_RETRIES)

_chain = _prompt | _primary.with_fallbacks([_secondary])


def classify_intent_node(state: State) -> dict:
    """Classify user intent as ORDER, INFO, or SPAM."""
    messages = state.get("messages", [])
    recent = messages[-settings.RECENT_CONTEXT_MESSAGES:-1] 
    user_msg = messages[-1].content

    try:
        result = _chain.invoke({
            "history": recent,
            "user_msg": user_msg,
        })

        return {"intent": result.intent}

    except Exception as e:
        print(f"Fallback due to classification error or safety filter trigger. {e}")
        return {"intent": "SPAM"}
        