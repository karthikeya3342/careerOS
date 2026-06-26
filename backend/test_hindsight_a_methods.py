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
        await client.acreate_bank(
            bank_id=bank_id,
            name="CareerOS Central Memory",
            mission="I am CareerOS, the central memory and adaptive learning engine for career tracking, resumes, and job matches.",
            disposition={"skepticism": 1, "literalism": 1, "empathy": 4}
        )
        print("Bank created")

        print("Retaining memory...")
        await client.aretain(
            bank_id=bank_id,
            content="Candidate SATISH is a CSE student graduating in 2028 with a CGPA of 8.8 and is highly interested in PyTorch, ROS, and computer vision.",
            document_id="onboarding_static",
            context="user_profile",
            tags=["userId:satish"]
        )
        print("Retained memory")

        print("Recalling memory...")
        rec = await client.arecall(
            bank_id=bank_id,
            query="Tell me about Satish",
            tags=["userId:satish"],
            tags_match="any_strict",
            max_tokens=1000
        )
        print("Recall result:", rec)

    except Exception as e:
        print("Error in main:", e)
    finally:
        try:
            await client.aclose()
        except Exception:
            pass

asyncio.run(main())
