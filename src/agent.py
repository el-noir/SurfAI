import asyncio
import base64
import json
import os
from datetime import datetime
from typing import Annotated, List, Optional, TypedDict, Union, Dict, Any

from langchain_groq import ChatGroq
from langchain_core.messages import (
    BaseMessage, 
    HumanMessage, 
    AIMessage, 
    SystemMessage,
    ToolMessage
)
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner

from .browser_manager import browser_instance
from .tools import BROWSER_TOOLS
from .config import MODEL, GROQ_API_KEY

# --- Constants & Config ---
CONSOLE = Console()
SYSTEM_PROMPT = """You are a professional browser automation agent with VISION capabilities.
You help users accomplish tasks by navigating the web, clicking on elements, and typing text.

CORE RULES:
1. VISION: You will receive screenshots of the current page. Use them to identify element coordinates (x, y). 
   - The viewport is 1280x800.
   - Elements are visible in the screenshot.
2. COORDINATES: Always provide precise x, y coordinates for clicking.
3. ACTIONS: 
   - Navigate to a URL first.
   - Click input fields before typing.
   - Use 'press_key' with 'Enter' to submit forms.
4. MEMORY: You have:
   - Short-term memory: Current conversation history.
   - Long-term memory: Persistent facts about the user (use 'save_memory' and 'get_memory' tools).
5. REASONING: Briefly explain your thoughts before each group of actions.

Goal: Execute the user's request efficiently and accurately."""

# --- State Definition ---
class AgentState(TypedDict):
    """The state of the browser agent."""
    messages: Annotated[List[BaseMessage], add_messages]
    last_screenshot: Optional[str]
    task: str

# --- Nodes ---
async def call_model(state: AgentState, config: RunnableConfig):
    """Calls the vision-capable LLM with current messages and screen context."""
    # Use a vision-capable model via Groq
    model = ChatGroq(model=MODEL, api_key=GROQ_API_KEY, temperature=0)
    model_with_tools = model.bind_tools(BROWSER_TOOLS)
    
    messages = state["messages"]
    
    # Inject screenshot as a context hint if available
    if state.get("last_screenshot"):
        # We wrap the screenshot in a HumanMessage to provide visual context
        vision_context = HumanMessage(content=[
            {"type": "text", "text": "Screenshot of current page state:"},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{state['last_screenshot']}"}}
        ])
        # Only inject if the last message isn't already a tool result with screenshot
        # For simplicity, we just add it to the message list for the LLM call
        messages = messages + [vision_context]

    response = await model_with_tools.ainvoke(messages, config)
    return {"messages": [response]}

async def capture_screen(state: AgentState):
    """Captures the current browser state."""
    screenshot = await browser_instance.screenshot_base64()
    return {"last_screenshot": screenshot}

# --- Router ---
def should_continue(state: AgentState):
    """Route based on whether the message has tool calls."""
    last_message = state["messages"][-1]
    if not last_message.tool_calls:
        return END
    return "tools"

# --- Graph Construction ---
def create_browser_agent():
    workflow = StateGraph(AgentState)

    # Add Nodes
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolNode(BROWSER_TOOLS))
    workflow.add_node("capture", capture_screen)

    # Set Edges
    workflow.add_edge(START, "capture")
    workflow.add_edge("capture", "agent")
    
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            END: END
        }
    )
    
    workflow.add_edge("tools", "capture")

    # Memory
    checkpointer = MemorySaver()
    
    return workflow.compile(checkpointer=checkpointer)

# --- CLI Execution Wrapper ---
async def run_agent(task: str, thread_id: str = "default"):
    """Main entry point to run the agent from CLI."""
    agent = create_browser_agent()
    config = {"configurable": {"thread_id": thread_id}}
    
    initial_state = {
        "messages": [
            SystemMessage(content=SYSTEM_PROMPT), 
            HumanMessage(content=f"TASK: {task}")
        ],
        "task": task,
        "last_screenshot": None
    }
    
    CONSOLE.print(f"\n[bold green]🚀 Starting task:[/bold green] {task}\n")
    
    try:
        async for event in agent.astream(initial_state, config=config, stream_mode="values"):
            if "messages" in event:
                last_msg = event["messages"][-1]
                
                if isinstance(last_msg, AIMessage):
                    if last_msg.content:
                        CONSOLE.print(f"[bold cyan]Agent:[/bold cyan] {last_msg.content}")
                    if last_msg.tool_calls:
                        for tc in last_msg.tool_calls:
                            CONSOLE.print(f"  [dim]🔨 Tool Call: {tc['name']} {tc['args']}[/dim]")
                
                elif isinstance(last_msg, ToolMessage):
                    success = "✅" if not last_msg.status == "error" else "❌"
                    content_preview = str(last_msg.content)[:100]
                    CONSOLE.print(f"    [dim]{success} Result: {content_preview}...[/dim]")
        
        CONSOLE.print(f"\n[bold green]✓ Task completed.[/bold green]")
        
    finally:
        await browser_instance.close()

if __name__ == "__main__":
    # For testing: uv run python -m src.agent "search for langgraph on google"
    import sys
    task = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Navigate to google.com"
    asyncio.run(run_agent(task))