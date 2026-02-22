import asyncio
import sys
from rich.console import Console
from rich.panel import Panel
from src.agent import run_agent

async def main():
    console = Console()
    
    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
    else:
        console.print(Panel(
            "Welcome to [bold cyan]Surf AI[/bold cyan]!\n"
            "I can control your browser using Vision and LangGraph.",
            title="[bold blue]Surf AI[/bold blue]",
            border_style="blue"
        ))
        task = console.input("[bold yellow]What should I do? [/bold yellow]")
    
    if not task.strip():
        return

    try:
        await run_agent(task)
    except Exception as e:
        console.print(f"[bold red]Critical Error:[/bold red] {str(e)}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")
