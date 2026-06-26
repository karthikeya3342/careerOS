import httpx
import asyncio

async def test():
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Check LeetCode
        try:
            resp = await client.get("https://alfa-leetcode-api.onrender.com/karthikeya3342")
            print("LeetCode raw status:", resp.status_code)
            print("LeetCode raw body:", resp.text)
        except Exception as e:
            print("LeetCode API error:", e)
            
        # Check Codeforces
        try:
            resp = await client.get("https://codeforces.com/api/user.info?handles=karthikeya3342")
            print("Codeforces raw status:", resp.status_code)
            print("Codeforces raw body:", resp.text)
        except Exception as e:
            print("Codeforces API error:", e)

asyncio.run(test())
