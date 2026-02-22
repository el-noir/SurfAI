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

# --- Advanced Interaction Tools ---

@tool
async def hover_at_location(x: int, y: int) -> str:
    """Hovers the mouse at specific x, y coordinates. Useful for revealing tooltips, dropdown menus, or hover-only content."""
    return await browser_instance.hover(x, y)

@tool
async def right_click_at_location(x: int, y: int) -> str:
    """Right-clicks at specific x, y coordinates. Opens context menus."""
    return await browser_instance.right_click(x, y)

@tool
async def double_click_at_location(x: int, y: int) -> str:
    """Double-clicks at specific x, y coordinates. Useful for selecting text or activating elements."""
    return await browser_instance.double_click(x, y)

@tool
async def drag_and_drop(from_x: int, from_y: int, to_x: int, to_y: int) -> str:
    """Drags an element from one position (from_x, from_y) to another (to_x, to_y)."""
    return await browser_instance.drag_and_drop(from_x, from_y, to_x, to_y)

@tool
async def select_dropdown(selector: str, value: str) -> str:
    """Selects an option from a <select> dropdown. Provide the CSS selector of the <select> element and the value or label to select."""
    return await browser_instance.select_option(selector, value)

# --- Page Content Tools ---

@tool
async def extract_page_text() -> str:
    """Extracts all visible text content from the current page. Returns the full text (truncated to 3000 chars if very long)."""
    return await browser_instance.extract_text()

@tool
async def wait_for_text(text: str, timeout: int = 5000) -> str:
    """Waits for an element containing specific text to appear on the page. Useful after navigating or submitting forms."""
    return await browser_instance.wait_for_element(text, timeout)

# --- Tab Management Tools ---

@tool
async def open_new_tab(url: str = "") -> str:
    """Opens a new browser tab, optionally navigating to a URL. The new tab becomes the active tab."""
    return await browser_instance.open_new_tab(url)

@tool
async def switch_tab(index: int) -> str:
    """Switches to a browser tab by its index (0-based). Use list_tabs to see all open tabs first."""
    return await browser_instance.switch_tab(index)

@tool
async def close_tab() -> str:
    """Closes the current browser tab and switches to the last remaining tab."""
    return await browser_instance.close_tab()

@tool
async def list_tabs() -> str:
    """Lists all open browser tabs with their index, title, and URL."""
    return await browser_instance.list_tabs()

# --- Dialog & File Tools ---

@tool
async def handle_dialog(accept: bool = True, text: str = "") -> str:
    """Prepares to handle the next browser dialog (alert, confirm, or prompt). Call this BEFORE triggering the action that causes the dialog. Set accept=False to dismiss, or provide text for prompt dialogs."""
    return await browser_instance.handle_dialog(accept, text)

@tool
async def upload_file(selector: str, file_path: str) -> str:
    """Uploads a file to a file input element. Provide the CSS selector of the file input and the absolute file path."""
    return await browser_instance.set_file_input(selector, file_path)


BROWSER_TOOLS = [
    # Core
    navigate,
    click_at_location,
    type_text,
    press_key,
    scroll_page,
    get_page_info,
    go_back,
    # Advanced interaction
    hover_at_location,
    right_click_at_location,
    double_click_at_location,
    drag_and_drop,
    select_dropdown,
    # Page content
    extract_page_text,
    wait_for_text,
    # Tab management
    open_new_tab,
    switch_tab,
    close_tab,
    list_tabs,
    # Dialogs & files
    handle_dialog,
    upload_file,
    # Memory
    save_memory,
    get_memory,
]
