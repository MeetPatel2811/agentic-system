# ---------------------------------------------------------
# This file defines the CrewAI tasks assigned to each agent:
# - controller_task: sets the plan and expectations.
# - research_task: gathers relevant information and sources.
# - analysis_task: summarizes and extracts claims/evidence,
#                  and can leverage vector memory retrieval.
# - write_task: produces the final Markdown answer.
#
# Each task references `{query}`, which is injected at runtime
# by crew.kickoff(inputs={"query": "..."})
# ---------------------------------------------------------
from crewai import Task
from crewai import Agent


# --- This block builds tasks bound to the given agents ---
def make_tasks(controller: Agent, researcher: Agent, analyst: Agent, writer: Agent):
    """
    Construct all tasks that the CrewAI pipeline will execute in sequence.
    """

    controller_task = Task(
        description=(
            "You are coordinating a research pipeline for the user query: '{query}'. "
            "Make a short plan for how the team should proceed: research, analysis, "
            "then writing. Focus on clarity and completeness."
        ),
        expected_output=(
            "A short plan describing the overall steps the agents should take, "
            "including what to look for during research and what a good final answer "
            "should contain."
        ),
        agent=controller,
    )

    research_task = Task(
        description=(
            "Use web search to gather 3–7 relevant snippets for the query: '{query}'. "
            "Focus on authority, clarity, and diversity of sources. Include titles, "
            "short summaries, and URLs when possible."
        ),
        expected_output=(
            "A list or bullet-style text containing multiple sources. Each source "
            "should include title, short snippet, and (if available) URL."
        ),
        agent=researcher,
    )

    analysis_task = Task(
        description=(
            "Take the research results for '{query}' and:\n"
            "1) Produce a concise summary (4–6 sentences).\n"
            "2) Extract 2–5 key claims.\n"
            "3) Extract 2–5 pieces of supporting evidence.\n"
            "4) Optionally, consult vector memory to see if past knowledge is relevant.\n"
            "Return everything in a structured text format with sections: "
            "Summary, Claims, Evidence."
        ),
        expected_output=(
            "Structured text with three sections:\n"
            "Summary:\n- ...\n\nClaims:\n- ...\n\nEvidence:\n- ..."
        ),
        agent=analyst,
    )

    write_task = Task(
        description=(
            "Using the structured analysis (summary, claims, evidence) for '{query}', "
            "write a final answer in Markdown format with these sections:\n"
            "- Overview\n- Key Claims\n- Supporting Evidence\n- Sources Consulted\n\n"
            "Make sure the tone is clear, helpful, and concise."
        ),
        expected_output="A polished Markdown document suitable to show to the end user.",
        agent=writer,
    )

    return [controller_task, research_task, analysis_task, write_task]
