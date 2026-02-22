import asyncio
import base64
import nest_asyncio
from playwright.async_api import async_playwright
from typing import Optional, Dict, Any

nest_asyncio.apply()

class BrowserManager:
    """Manages the Playwright browser instance and provides high-level control methods."""

    def __init__(self, headless: bool = False):
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.viewport = {"width": 1280, "height": 800}

    async def init_browser(self):
        """Initializes the playwright browser and page."""
        if self.page:
            return
            
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled"
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

# Global browser instance handled by tools
browser_instance = BrowserManager()
