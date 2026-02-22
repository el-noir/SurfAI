import asyncio
import os
import json
from langchain_core.tools import tool
from .browser_manager import browser_instance

@tool
async def navigate(url: str) -> str:
    """Navigate to a specified URL in the browser."""
    return await browser_instance.navigate(url)

@tool
async def click_at_location(x: int, y: int) -> str:
    """Clicks at specific x, y coordinates on the current page."""
    return await browser_instance.click(x, y)

@tool
async def type_text(text: str, press_enter: bool = True) -> str:
    """Types the provided text into the currently focused element, optionally pressing Enter."""
    return await browser_instance.type(text, append_enter=press_enter)

@tool
async def press_key(key: str) -> str:
    """Presses a specific key on the keyboard (e.g., 'Enter', 'Tab', 'ArrowDown')."""
    return await browser_instance.press(key)

@tool
async def scroll_page(direction: str = "down") -> str:
    """Scrolls the current page up or down."""
    return await browser_instance.scroll(direction)

@tool
async def get_page_info() -> str:
    """Returns the current page URL and title."""
    return await browser_instance.get_page_info()

@tool
async def go_back() -> str:
    """Navigates back to the previous page in history."""
    return await browser_instance.go_back()

@tool
async def save_memory(key: str, value: str) -> str:
    """Saves a piece of information to long-term memory. Use this for user preferences or learned facts."""
    memory_path = "memory.json"
    data = {}
    if os.path.exists(memory_path):
        try:
            with open(memory_path, "r") as f:
                data = json.load(f)
        except: pass
    data[key] = value
    with open(memory_path, "w") as f:
        json.dump(data, f, indent=2)
    return f"Saved memory: {key} = {value}"

@tool
async def get_memory(key: str) -> str:
    """Retrieves information from long-term memory by key."""
    memory_path = "memory.json"
    if not os.path.exists(memory_path):
        return "No memory found."
    try:
        with open(memory_path, "r") as f:
            data = json.load(f)
        return data.get(key, f"Key '{key}' not found in memory.")
    except Exception as e:
        return f"Error reading memory: {str(e)}"

BROWSER_TOOLS = [
    navigate,
    click_at_location,
    type_text,
    press_key,
    scroll_page,
    get_page_info,
    go_back,
    save_memory,
    get_memory
]
