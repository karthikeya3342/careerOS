from hindsight_client import Hindsight
import traceback
import asyncio

async def test():
    client = Hindsight(
        base_url="https://api.hindsight.vectorize.io",
        api_key="hsk_4f6be8344c78c821af2d0acf69e0a480_186211b302780c78"
    )
    bank_id = "career_os_bank"
    try:
        # Await the coroutine directly
        res = await client.create_mental_model(
            bank_id=bank_id,
            name="satish_preferences",
            source_query="What are this user's preferences regarding startups, remote vs on-site work, and roles?",
            tags=["userId:satish"],
            trigger={"refresh_after_consolidation": True}
        )
        print("Success:", res)
    except Exception as e:
        print("Error:")
        traceback.print_exc()

asyncio.run(test())
