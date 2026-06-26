from hindsight_client import Hindsight
import inspect
import asyncio

client = Hindsight(
    base_url="https://api.hindsight.vectorize.io",
    api_key="hsk_4f6be8344c78c821af2d0acf69e0a480_186211b302780c78"
)

sig = inspect.signature(client.create_mental_model)
print("create_mental_model signature:", sig)

async def test():
    bank_id = "career_os_bank"
    # Let's try creating a mental model
    try:
        # In Hindsight, create_mental_model takes: bank_id, name, source_query, tags, trigger
        # Or it might take mental_model schema. Let's see what happens.
        res = client.create_mental_model(
            bank_id=bank_id,
            name="satish_preferences",
            source_query="What are this user's preferences regarding startups, remote vs on-site work, and roles?",
            tags=["userId:satish"],
            trigger={"refresh_after_consolidation": True}
        )
        if asyncio.iscoroutine(res):
            mm = await res
        else:
            mm = res
        print("Mental model created:", mm)
    except Exception as e:
        print("Error creating mental model:", e)

asyncio.run(test())
