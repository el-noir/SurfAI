import asyncio
import os
import json
import uvicorn
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from contextlib import asynccontextmanager
from src.agent import create_browser_agent, SYSTEM_PROMPT
from src.browser_manager import browser_instance

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: logic before application starts
    print("[SERVER] Starting up...")
    yield
    # Shutdown: logic after application stops
    print("[SERVER] Shutting down...")
    await browser_instance.close()

app = FastAPI(title="BrowserAgent Chat", lifespan=lifespan)

# Serve static files
STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def root():
    """Serve the chat UI."""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return HTMLResponse(content=index_path.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>Chat UI not found</h1>", status_code=404)


@app.get("/health")
async def health():
    """Health check endpoint for deployment platforms."""
    return {"status": "ok", "port": os.getenv("PORT", "8000")}


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    """Handle real-time chat via WebSocket."""
    await ws.accept()
    print(f"[WS] Connection accepted from {ws.client}")
    
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
    # Don't close the browser here — it should persist across sessions


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print(f"[SERVER] Launching on port {port}...")
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False, log_level="info")
