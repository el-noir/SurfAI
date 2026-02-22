import asyncio
import os
import base64
import nest_asyncio
from playwright.async_api import async_playwright
from typing import Optional, Dict, Any

nest_asyncio.apply()

class BrowserManager:
    """Manages the Playwright browser instance and provides high-level control methods."""

    def __init__(self, headless: Optional[bool] = None):
        # Default to headless in cloud (no GUI), allow override via env or param
        env_headless = os.getenv("HEADLESS", "true").lower() == "true"
        self.headless = headless if headless is not None else env_headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.viewport = {"width": 1280, "height": 800}

    async def init_browser(self):
        """Initializes the playwright browser and page."""
        # Check if browser is still alive
        if self.page and self.browser and self.browser.is_connected():
            return
        
        # Clean up stale state if any
        if self.browser:
            try:
                await self.browser.close()
            except Exception:
                pass
        if self.playwright:
            try:
                await self.playwright.stop()
            except Exception:
                pass
            
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-gpu",
                "--hide-scrollbars",
                "--mute-audio"
            ]
        )
        self.context = await self.browser.new_context(
            viewport=self.viewport,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        self.page = await self.context.new_page()

    async def navigate(self, url: str) -> str:
        """Navigates to a specific URL."""
        await self.init_browser()
        try:
            # Add protocol if missing
            if not url.startswith("http"):
                url = "https://" + url
            await self.page.goto(url, wait_until="networkidle", timeout=30000)
            # Extra wait for dynamic content
            await asyncio.sleep(2)
            return f"Successfully navigated to {url}"
        except Exception as e:
            return f"Error navigating to {url}: {str(e)}"

    async def screenshot_base64(self) -> str:
        """Captures a screenshot and returns it as a base64 string."""
        if not self.page:
            return ""
        try:
            # Brief wait for page stability
            await asyncio.sleep(0.5)
            screenshot_bytes = await self.page.screenshot(type="jpeg", quality=60)
            return base64.b64encode(screenshot_bytes).decode("utf-8")
        except Exception:
            return ""

    async def click(self, x: int, y: int) -> str:
        """Clicks at the specified coordinates."""
        await self.init_browser()
        try:
            # Ensure coordinates are within viewport
            x = max(0, min(x, self.viewport["width"]))
            y = max(0, min(y, self.viewport["height"]))
            
            await self.page.mouse.click(x, y)
            await asyncio.sleep(1) # Wait for potential transition
            return f"Clicked at coordinates ({x}, {y})"
        except Exception as e:
            return f"Failed to click at ({x}, {y}): {str(e)}"

    async def type(self, text: str, append_enter: bool = False) -> str:
        """Types text into the currently focused element."""
        await self.init_browser()
        try:
            await self.page.keyboard.type(text, delay=50)
            if append_enter:
                await self.page.keyboard.press("Enter")
                await asyncio.sleep(1)
            return f"Typed: '{text}'" + (" and pressed Enter" if append_enter else "")
        except Exception as e:
            return f"Failed to type: {str(e)}"

    async def press(self, key: str) -> str:
        """Presses a keyboard key."""
        await self.init_browser()
        try:
            await self.page.keyboard.press(key)
            await asyncio.sleep(1)
            return f"Pressed key: {key}"
        except Exception as e:
            return f"Failed to press key {key}: {str(e)}"

    async def scroll(self, direction: str = "down") -> str:
        """Scrolls the page."""
        await self.init_browser()
        try:
            amount = 500 if direction == "down" else -500
            await self.page.evaluate(f"window.scrollBy(0, {amount})")
            await asyncio.sleep(0.5)
            return f"Scrolled {direction}"
        except Exception as e:
            return f"Failed to scroll {direction}: {str(e)}"

    async def close(self):
        """Closes the browser and stops playwright."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        self.browser = None
        self.playwright = None
        self.page = None
        self.context = None

    async def get_page_info(self) -> str:
        """Returns the current URL and title of the page."""
        if not self.page:
            return "No page loaded"
        try:
            url = self.page.url
            title = await self.page.title()
            return f"Current URL: {url}\nPage Title: {title}"
        except Exception:
            return "Could not retrieve page info"

    async def hover(self, x: int, y: int) -> str:
        """Hovers the mouse over the specified coordinates."""
        await self.init_browser()
        try:
            x = max(0, min(x, self.viewport["width"]))
            y = max(0, min(y, self.viewport["height"]))
            await self.page.mouse.move(x, y)
            await asyncio.sleep(0.5)
            return f"Hovered at ({x}, {y})"
        except Exception as e:
            return f"Failed to hover at ({x}, {y}): {str(e)}"

    async def right_click(self, x: int, y: int) -> str:
        """Right-clicks at the specified coordinates."""
        await self.init_browser()
        try:
            x = max(0, min(x, self.viewport["width"]))
            y = max(0, min(y, self.viewport["height"]))
            await self.page.mouse.click(x, y, button="right")
            await asyncio.sleep(1)
            return f"Right-clicked at ({x}, {y})"
        except Exception as e:
            return f"Failed to right-click at ({x}, {y}): {str(e)}"

    async def double_click(self, x: int, y: int) -> str:
        """Double-clicks at the specified coordinates."""
        await self.init_browser()
        try:
            x = max(0, min(x, self.viewport["width"]))
            y = max(0, min(y, self.viewport["height"]))
            await self.page.mouse.dblclick(x, y)
            await asyncio.sleep(1)
            return f"Double-clicked at ({x}, {y})"
        except Exception as e:
            return f"Failed to double-click at ({x}, {y}): {str(e)}"

    async def drag_and_drop(self, from_x: int, from_y: int, to_x: int, to_y: int) -> str:
        """Drags from one position to another."""
        await self.init_browser()
        try:
            await self.page.mouse.move(from_x, from_y)
            await self.page.mouse.down()
            await asyncio.sleep(0.2)
            await self.page.mouse.move(to_x, to_y, steps=20)
            await self.page.mouse.up()
            await asyncio.sleep(0.5)
            return f"Dragged from ({from_x}, {from_y}) to ({to_x}, {to_y})"
        except Exception as e:
            return f"Failed to drag: {str(e)}"

    async def select_option(self, selector: str, value: str) -> str:
        """Selects an option from a <select> dropdown by value or label."""
        await self.init_browser()
        try:
            await self.page.select_option(selector, value, timeout=5000)
            await asyncio.sleep(0.5)
            return f"Selected '{value}' from '{selector}'"
        except Exception as e:
            return f"Failed to select option: {str(e)}"

    async def extract_text(self) -> str:
        """Extracts all visible text content from the current page."""
        if not self.page:
            return "No page loaded"
        try:
            text = await self.page.evaluate("() => document.body.innerText")
            # Truncate to avoid overwhelming the LLM context
            if len(text) > 3000:
                text = text[:3000] + "\n\n... [truncated]"
            return text
        except Exception as e:
            return f"Failed to extract text: {str(e)}"

    async def open_new_tab(self, url: str = "") -> str:
        """Opens a new browser tab, optionally navigating to a URL."""
        await self.init_browser()
        try:
            new_page = await self.context.new_page()
            self.page = new_page
            if url:
                if not url.startswith("http"):
                    url = "https://" + url
                await self.page.goto(url, wait_until="networkidle", timeout=30000)
                await asyncio.sleep(1)
                return f"Opened new tab and navigated to {url}"
            return "Opened new blank tab"
        except Exception as e:
            return f"Failed to open new tab: {str(e)}"

    async def switch_tab(self, index: int) -> str:
        """Switches to a tab by its index (0-based)."""
        await self.init_browser()
        try:
            pages = self.context.pages
            if 0 <= index < len(pages):
                self.page = pages[index]
                await self.page.bring_to_front()
                title = await self.page.title()
                return f"Switched to tab {index}: {title} ({self.page.url})"
            return f"Tab index {index} out of range. {len(pages)} tabs open."
        except Exception as e:
            return f"Failed to switch tab: {str(e)}"

    async def close_tab(self) -> str:
        """Closes the current tab and switches to the previous one."""
        await self.init_browser()
        try:
            await self.page.close()
            pages = self.context.pages
            if pages:
                self.page = pages[-1]
                await self.page.bring_to_front()
                return f"Closed tab. Now on: {self.page.url}"
            return "Closed last tab. No tabs remaining."
        except Exception as e:
            return f"Failed to close tab: {str(e)}"

    async def list_tabs(self) -> str:
        """Lists all open tabs with their index, URL, and title."""
        await self.init_browser()
        try:
            pages = self.context.pages
            lines = []
            for i, page in enumerate(pages):
                title = await page.title()
                current = " ← current" if page == self.page else ""
                lines.append(f"[{i}] {title} ({page.url}){current}")
            return "\n".join(lines) if lines else "No tabs open."
        except Exception as e:
            return f"Failed to list tabs: {str(e)}"

    async def handle_dialog(self, accept: bool = True, text: str = "") -> str:
        """Sets up a handler for the next browser dialog (alert/confirm/prompt)."""
        await self.init_browser()
        try:
            async def on_dialog(dialog):
                if text and dialog.type == "prompt":
                    await dialog.accept(text)
                elif accept:
                    await dialog.accept()
                else:
                    await dialog.dismiss()
            self.page.once("dialog", on_dialog)
            action = "accept" if accept else "dismiss"
            return f"Dialog handler set to {action}" + (f" with text '{text}'" if text else "")
        except Exception as e:
            return f"Failed to set dialog handler: {str(e)}"

    async def set_file_input(self, selector: str, file_path: str) -> str:
        """Sets a file on a file input element."""
        await self.init_browser()
        try:
            await self.page.set_input_files(selector, file_path, timeout=5000)
            return f"Set file '{file_path}' on '{selector}'"
        except Exception as e:
            return f"Failed to set file: {str(e)}"

    async def wait_for_element(self, text: str, timeout: int = 5000) -> str:
        """Waits for an element containing specific text to appear on the page."""
        await self.init_browser()
        try:
            await self.page.get_by_text(text).first.wait_for(timeout=timeout)
            return f"Element with text '{text}' found"
        except Exception as e:
            return f"Timed out waiting for '{text}': {str(e)}"


# Global browser instance handled by tools
browser_instance = BrowserManager()
