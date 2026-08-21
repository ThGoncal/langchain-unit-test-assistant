"""
Chaînes LangChain et agent de chat, assemblés à partir de core/llm.py,
core/schemas.py et prompts/prompts.py.
"""

from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

from core.llm import get_llm
from core.schemas import CodeAnalysisResult, GeneratedTestResult, TestExplanationResult
from prompts.prompts import (
    CODE_ANALYSIS_PROMPT,
    TEST_GENERATION_PROMPT,
    TEST_EXPLANATION_PROMPT,
    CHAT_SYSTEM_PROMPT,
)

_checkpointer = InMemorySaver()

def get_analysis_chain():
    llm = get_llm(temperature=0.1)
    return (CODE_ANALYSIS_PROMPT | llm.with_structured_output(CodeAnalysisResult, method="json_mode")).with_config(
        {"run_name": "analyse_code"}
    )


def get_test_chain():
    llm = get_llm(temperature=0.1)
    return (TEST_GENERATION_PROMPT | llm.with_structured_output(GeneratedTestResult, method="json_mode")).with_config(
        {"run_name": "generation_test"}
    )


def get_explain_test_chain():
    llm = get_llm(temperature=0.3)
    return (TEST_EXPLANATION_PROMPT | llm.with_structured_output(TestExplanationResult, method="json_mode")).with_config(
        {"run_name": "explication_test"}
    )


def get_chat_agent():
    llm = get_llm(temperature=0.7)
    return create_agent(
        model=llm,
        tools=[],
        system_prompt=CHAT_SYSTEM_PROMPT,
        checkpointer=_checkpointer,
    ).with_config({"run_name": "agent_chat"})