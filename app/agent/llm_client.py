"""
llm_client.py — Configured LLM instances for the CheziousBot agent.
"""

import logging
from langchain_groq import ChatGroq
from ..config.settings import settings

logger = logging.getLogger(__name__)

# Primary LLM (Standard: llama-3.1-8b-instant)
llm = ChatGroq(
    api_key=settings.GROQ_API_KEY,
    model=settings.GROQ_MODEL or settings.ADVANCE_GROQ_MODEL,
    temperature=0.1,
    max_tokens=1024,
    max_retries=settings.MAX_LLM_RETRIES,
)

# Advanced LLM (Advanced: llama-3.3-70b-versatile)
advanced_llm = ChatGroq(
    api_key=settings.GROQ_API_KEY,
    model=settings.ADVANCE_GROQ_MODEL or settings.GROQ_MODEL,
    temperature=0.1,
    max_tokens=1024,
    max_retries=settings.MAX_LLM_RETRIES,
)
