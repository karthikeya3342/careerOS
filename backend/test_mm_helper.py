import asyncio
from hindsight_helper import HindsightMemoryManager

async def test():
    mgr = HindsightMemoryManager()
    await mgr.initialize_bank()
    
    print("Creating mental model via helper...")
    res = await mgr.create_user_mental_model("satish")
    print("Result:", res)

    print("Fetching mental model...")
    content = await mgr.fetch_user_mental_model("satish")
    print("Content:", content)

    await mgr.close()

asyncio.run(test())
