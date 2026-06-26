import asyncio
from hindsight_client import Hindsight

async def main():
    client = Hindsight(
        base_url="https://api.hindsight.vectorize.io",
        api_key="hsk_4f6be8344c78c821af2d0acf69e0a480_186211b302780c78"
    )

    try:
        # Let's see if list_banks is async
        res = await client.banks.list_banks()
        print("list response:", res)
    except Exception as e:
        print("Error:", e)

asyncio.run(main())
