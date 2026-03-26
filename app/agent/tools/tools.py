"""
tools.py — Tools for CheziousBot agent.
"""

import json
from typing import Optional
from langchain_core.tools import tool
from ...utils.knowledge_base import search_knowledge_base


@tool
def info_tool(
    category: Optional[str] = "menu",
    query: Optional[str] = None,
) -> str:
    """Retrieve Cheezious restaurant information (menu, locations, or policies).

    Args:
        category: Type of info — "menu", "locations", or "policies".
        query: Optional search term to filter results.
    """
    data = search_knowledge_base(category or "", query)
    return json.dumps(data, indent=2, ensure_ascii=False)


ALL_TOOLS = [info_tool]
