"""LangGraph state graph for the recruitment agent."""

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from src.agent.nodes import agent_node, schedule_node, tool_node
from src.agent.state import AgentState


def build_graph() -> StateGraph:
    """Build and compile the recruitment agent's state graph.

    Nodes use Command(goto=...) to handle all routing internally.
    A MemorySaver checkpointer enables human-in-the-loop approval.
    """
    workflow = StateGraph(AgentState)

    workflow.add_node("agent_node", agent_node)
    workflow.add_node("tool_node", tool_node)
    workflow.add_node("schedule_node", schedule_node)

    workflow.set_entry_point("agent_node")

    # Connect nodes — routing is handled by Command(goto=...) from each node
    workflow.add_edge("agent_node", "tool_node")
    workflow.add_edge("tool_node", "agent_node")
    workflow.add_edge("schedule_node", END)

    checkpointer = MemorySaver()

    graph = workflow.compile(checkpointer=checkpointer)

    return graph