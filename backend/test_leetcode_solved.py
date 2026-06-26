import httpx
import asyncio

async def test():
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get("https://alfa-leetcode-api.onrender.com/karthikeya3342/solved")
            print("LeetCode solved status:", resp.status_code)
            print("LeetCode solved body:", resp.text)
        except Exception as e:
            print("LeetCode error:", e)

asyncio.run(test())
