# ---------------------------------------------------------
# This file defines all CrewAI agents used in the system:
# - Controller Agent: oversees the process and ensures quality.
# - Research Agent: finds relevant information using web search.
# - Analysis Agent: summarizes and extracts claims/evidence.
# - Writer Agent: writes the final Markdown answer.
#
# All agents share the same OpenAI LLM (gpt-4o-mini).
# Tools are attached per-agent based on their responsibility.
# ---------------------------------------------------------
from typing import Tuple

from crewai import Agent
from langchain_openai import ChatOpenAI

from tools.web_search import web_search_tool
from tools.summarizer import summarizer_tool
from tools.formatter import formatter_tool
from tools.claim_extractor import claim_extractor_tool
from tools.vector_memory_tool import vector_memory_retrieve_tool


# --- This block builds the shared LLM used by all agents ---
def make_llm() -> ChatOpenAI:
    """
    Create a shared OpenAI chat model for all agents.
    Requires OPENAI_API_KEY to be set in your environment.
    """
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.2,
    )


# --- This block constructs all 4 agents and returns them as a tuple ---
def build_agents() -> Tuple[Agent, Agent, Agent, Agent]:
    """
    Build and configure:
    - controller_agent
    - research_agent
    - analysis_agent
    - writer_agent
    """
    llm = make_llm()

    controller_agent = Agent(
        role="Controller",
        goal="Plan the research flow and ensure high-quality answers.",
        backstory=(
            "You are a senior research coordinator. You coordinate the other agents "
            "and make sure the final answer is coherent, helpful, and well-structured."
        ),
        llm=llm,
        allow_delegation=False,
        verbose=True,
        tools=[
            # Controller mainly reads outputs, but can also use tools for checks.
            vector_memory_retrieve_tool,
        ],
    )

    research_agent = Agent(
        role="Researcher",
        goal="Find high-quality, relevant information for the given query.",
        backstory=(
            "You specialize in using web search to gather useful snippets and sources. "
            "You focus on quality over quantity."
        ),
        llm=llm,
        allow_delegation=False,
        verbose=True,
        tools=[web_search_tool],
    )

    analysis_agent = Agent(
        role="Analyst",
        goal="Summarize research results and extract key claims and evidence.",
        backstory=(
            "You analyze all the information collected by the researcher and turn it "
            "into structured insights: summaries, claims, and supporting evidence."
        ),
        llm=llm,
        allow_delegation=False,
        verbose=True,
        tools=[summarizer_tool, claim_extractor_tool, vector_memory_retrieve_tool],
    )

    writer_agent = Agent(
        role="Writer",
        goal="Write a clear, structured Markdown answer for the user.",
        backstory=(
            "You are a technical writer. You turn analysis into a reader-friendly "
            "Markdown response with headings, bullet points, and source sections."
        ),
        llm=llm,
        allow_delegation=False,
        verbose=True,
        tools=[formatter_tool],
    )

    return controller_agent, research_agent, analysis_agent, writer_agent
