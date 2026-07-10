"""Agent graph node functions for the recruitment agent."""

import json
from typing import Literal

from langgraph.types import Command

from src.schemas import TrajectoryStep
from src.tools.check_availability import check_availability
from src.tools.parse_resume import parse_resume
from src.tools.propose_interview import propose_interview
from src.tools.score_candidate import score_candidate
from src.agent.state import AgentState

TOOL_MAP = {
    "parse_resume": parse_resume,
    "score_candidate": score_candidate,
    "check_availability": check_availability,
    "propose_interview": propose_interview,
}

# Lazy LLM initialization — avoids crash at import time
_llm = None
_llm_with_tools = None


def _get_llm():
    global _llm, _llm_with_tools
    if _llm is None:
        from dotenv import load_dotenv
        load_dotenv()
        from langchain_anthropic import ChatAnthropic
        _llm = ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0)
        _llm_with_tools = _llm.bind_tools(list(TOOL_MAP.values()))
    return _llm_with_tools


def agent_node(state: AgentState) -> Command[Literal["tool_node", "__end__"]]:
    """Decide the next tool call given current state."""
    step_count = state.get("step_count", 0)

    candidates_info = "\n".join(
        f"- {c['name']}" for c in state.get("candidates", [])
    )
    scored = list(state.get("scorecards", {}).keys())
    unscored = [
        c["name"]
        for c in state.get("candidates", [])
        if c["name"] not in scored
    ]

    prompt_parts = [
        "You are a recruitment agent. Evaluate candidates and schedule interviews.",
        f"\nJob Description: {state.get('job_description', '')[:500]}...",
        f"\nCandidates: {candidates_info}",
    ]
    if unscored:
        prompt_parts.append(
            f"\nStill need to score: {', '.join(unscored)}. "
            "Call parse_resume then score_candidate for each."
        )
    elif scored:
        prompt_parts.append(
            "\nAll candidates scored. Check availability and propose interviews "
            "for the top candidate(s)."
        )
    prompt_parts.append(
        "\nAvailable tools: parse_resume, score_candidate, check_availability, propose_interview."
    )

    try:
        llm = _get_llm()
        response = llm.invoke("\n".join(prompt_parts))
    except Exception as e:
        # If LLM call fails, end the graph with an error message
        step = TrajectoryStep(
            step_number=step_count + 1,
            thought=f"Error calling LLM: {e}",
            action=None,
            action_input=None,
            observation=str(e),
        )
        trajectory = list(state.get("trajectory", []))
        trajectory.append(step)
        return Command(
            update={"trajectory": trajectory, "step_count": step_count + 1},
            goto="__end__",
        )

    thought_text = response.content if isinstance(response.content, str) else str(response.content)

    step = TrajectoryStep(
        step_number=step_count + 1,
        thought=thought_text,
        action=None,
        action_input=None,
        observation=None,
    )
    trajectory = list(state.get("trajectory", []))
    trajectory.append(step)

    if response.tool_calls:
        tc = response.tool_calls[0]
        trajectory[-1].action = tc["name"]
        trajectory[-1].action_input = tc["args"]
        return Command(
            update={"trajectory": trajectory, "step_count": step_count + 1},
            goto="tool_node",
        )

    return Command(
        update={"trajectory": trajectory, "step_count": step_count + 1},
        goto="__end__",
    )


def tool_node(state: AgentState) -> Command[Literal["agent_node", "schedule_node"]]:
    """Execute the chosen tool and record the observation."""
    trajectory = list(state.get("trajectory", []))
    current_step = trajectory[-1] if trajectory else None

    if current_step is None or current_step.action is None:
        return Command(update={"trajectory": trajectory}, goto="agent_node")

    tool_name = current_step.action
    tool_args = current_step.action_input or {}
    tool_fn = TOOL_MAP.get(tool_name)

    if tool_fn is None:
        observation = f"Unknown tool: {tool_name}"
    else:
        try:
            result = tool_fn.invoke(tool_args)
            observation = json.dumps(result, indent=2, default=str)
        except Exception as e:
            observation = f"Error calling {tool_name}: {e}"

    current_step.observation = observation
    trajectory[-1] = current_step

    if tool_name == "propose_interview" and "blocked_pending_approval" in observation:
        return Command(
            update={"trajectory": trajectory, "pending_approval": tool_args},
            goto="schedule_node",
        )

    return Command(update={"trajectory": trajectory}, goto="agent_node")


def schedule_node(state: AgentState) -> dict:
    """Set pending_approval state for human-in-the-loop."""
    pending = state.get("pending_approval")
    if pending is None:
        return {"pending_approval": None}
    return {"pending_approval": pending}