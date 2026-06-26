import asyncio
from hindsight_client import Hindsight

async def main():
    client = Hindsight(
        base_url="https://api.hindsight.vectorize.io",
        api_key="hsk_4f6be8344c78c821af2d0acf69e0a480_186211b302780c78"
    )

    bank_id = "career_os_bank"
    try:
        print("Creating bank...")
        # Since client.create_bank is async (or maps to _acreate_bank), let's await it!
        # Let's inspect the method: if it returns a coroutine, we await it.
        # Let's check if client.create_bank is async:
        res = client.create_bank(
            bank_id=bank_id,
            name="CareerOS Central Memory",
            mission="I am CareerOS, the central memory and adaptive learning engine for career tracking, resumes, and job matches.",
            disposition={"skepticism": 1, "literalism": 1, "empathy": 4}
        )
        if asyncio.iscoroutine(res):
            await res
            print("Bank created (awaited)")
        else:
            print("Bank created (sync)")

        print("Retaining memory...")
        ret_res = client.retain(
            bank_id=bank_id,
            content="Candidate SATISH is a CSE student graduating in 2028 with a CGPA of 8.8 and is highly interested in PyTorch, ROS, and computer vision.",
            document_id="onboarding_static",
            context="user_profile",
            tags=["userId:satish"]
        )
        if asyncio.iscoroutine(ret_res):
            await ret_res
            print("Retained memory (awaited)")
        else:
            print("Retained memory (sync)")

        print("Recalling memory...")
        rec_res = client.recall(
            bank_id=bank_id,
            query="Tell me about Satish",
            tags=["userId:satish"],
            tags_match="any_strict",
            max_tokens=1000
        )
        if asyncio.iscoroutine(rec_res):
            rec = await rec_res
            print("Recalled memory (awaited)")
        else:
            rec = rec_res
            print("Recalled memory (sync)")
        
        print("Recall result:", rec)

    except Exception as e:
        print("Error in main:", e)
    finally:
        try:
            client.close()
        except Exception:
            pass

asyncio.run(main())
