import asyncio
from onboarding_agent import fetch_codeforces_data

async def test():
    res = await fetch_codeforces_data("https://codeforces.com/profile/karthikeya3342")
    print("Codeforces fetch result:", res)

asyncio.run(test())
