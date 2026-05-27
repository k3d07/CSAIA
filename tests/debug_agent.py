"""Bypass FastAPI to surface the full traceback from the agent."""
import asyncio
import sys
import traceback

sys.path.append(".")

from app.agent import run_agent


async def main():
    try:
        result = await run_agent(
            message="What is your refund policy?",
            conversation_history=[],
        )
        print("---- SUCCESS ----")
        print(result)
    except Exception:
        print("---- FAILURE ----")
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
