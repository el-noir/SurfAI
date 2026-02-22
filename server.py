import asyncio
import json
import uvicorn
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from src.agent import create_browser_agent, SYSTEM_PROMPT
from src.browser_manager import browser_instance

app = FastAPI(title="BrowserAgent Chat")

# Serve static files
STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def root():
    """Serve the chat UI."""
    index_path = STATIC_DIR / "index.html"
    return HTMLResponse(content=index_path.read_text(encoding="utf-8"))


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    """Handle real-time chat via WebSocket."""
    await ws.accept()
    
    agent = create_browser_agent()
    thread_id = "web-session"
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        while True:
            # Wait for user message
            data = await ws.receive_text()
            user_msg = json.loads(data)
            task = user_msg.get("message", "")
            
            if not task.strip():
                continue
            
            # Build initial state
            initial_state = {
                "messages": [
                    SystemMessage(content=SYSTEM_PROMPT),
                    HumanMessage(content=f"TASK: {task}")
                ],
                "task": task,
                "last_screenshot": None
            }
            
            # Stream agent events back to client
            try:
                async for event in agent.astream(initial_state, config=config, stream_mode="values"):
                    if "messages" in event:
                        last_msg = event["messages"][-1]
                        
                        if isinstance(last_msg, AIMessage):
                            if last_msg.content:
                                await ws.send_json({
                                    "type": "thinking",
                                    "content": last_msg.content
                                })
                            if last_msg.tool_calls:
                                for tc in last_msg.tool_calls:
                                    await ws.send_json({
                                        "type": "tool_call",
                                        "name": tc["name"],
                                        "args": tc["args"]
                                    })
                        
                        elif isinstance(last_msg, ToolMessage):
                            success = last_msg.status != "error" if hasattr(last_msg, "status") else True
                            await ws.send_json({
                                "type": "tool_result",
                                "name": last_msg.name if hasattr(last_msg, "name") else "unknown",
                                "content": str(last_msg.content)[:200],
                                "success": success
                            })
                    
                    # Send latest screenshot if available
                    if event.get("last_screenshot"):
                        await ws.send_json({
                            "type": "screenshot",
                            "data": event["last_screenshot"]
                        })
                
                await ws.send_json({"type": "done"})
                
            except Exception as e:
                await ws.send_json({
                    "type": "error",
                    "content": str(e)
                })
    
    except WebSocketDisconnect:
        pass
    finally:
        await browser_instance.close()


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)
