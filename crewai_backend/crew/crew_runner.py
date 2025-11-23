# ---------------------------------------------------------
# This file wires everything together into a CrewAI `Crew`:
# - Builds agents
# - Builds tasks
# - Configures the crew to run in sequential process mode
#   (which is easier to debug and reason about for this project).
#
# The FastAPI layer calls build_crew() and then crew.kickoff().
# ---------------------------------------------------------
from crewai import Crew, Process

from .agents import build_agents
from .tasks import make_tasks


# --- This block builds and returns the configured crew ---
def build_crew() -> Crew:
    """
    Construct a CrewAI Crew with:
    - Controller, Researcher, Analyst, Writer
    - Tasks: controller → research → analysis → write
    """
    controller, researcher, analyst, writer = build_agents()
    tasks = make_tasks(controller, researcher, analyst, writer)

    crew = Crew(
        agents=[controller, researcher, analyst, writer],
        tasks=tasks,
        process=Process.sequential,  # simple and deterministic
        verbose=True,
    )
    return crew
