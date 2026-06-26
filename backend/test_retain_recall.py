import asyncio
from hindsight_client import Hindsight

async def main():
    client = Hindsight(
        base_url="https://api.hindsight.vectorize.io",
        api_key="hsk_4f6be8344c78c821af2d0acf69e0a480_186211b302780c78"
    )

    bank_id = "career_os_bank"
    try:
        # Create bank or update it
        print("Creating bank...")
        # create_or_update_bank args: bank_id, bank (model/dict) or create_bank. Let's see client.create_bank or client.banks.create_or_update_bank
        # The docs say: client.create_bank or client.banks.create_or_update_bank
        # Let's inspect create_or_update_bank signature:
        # The inspect output was client.banks: 'create_or_update_bank'
        # Let's try client.create_bank or client.banks.create_or_update_bank
        try:
            await client.create_bank(
                bank_id=bank_id,
                name="CareerOS Central Memory",
                mission="I am CareerOS, the central memory and adaptive learning engine for career tracking, resumes, and job matches.",
                disposition={"skepticism": 1, "literalism": 1, "empathy": 4}
            )
            print("Bank created using client.create_bank")
        except Exception as err:
            print("client.create_bank failed, trying client.banks.create_or_update_bank:", err)
            # Try client.banks.create_or_update_bank
            from hindsight_client_api.models.bank import Bank
            bank_obj = Bank(
                id=bank_id,
                name="CareerOS Central Memory",
                mission="I am CareerOS, the central memory and adaptive learning engine for career tracking, resumes, and job matches.",
                disposition={"skepticism": 1, "literalism": 1, "empathy": 4}
            )
            await client.banks.create_or_update_bank(bank_id=bank_id, bank=bank_obj)
            print("Bank created using banks.create_or_update_bank")

        # Let's try client.retain or client.memory.retain
        # In inspect client methods: ['retain', 'recall', 'reflect']
        print("Retaining memory...")
        res = await client.retain(
            bank_id=bank_id,
            content="Candidate SATISH is a CSE student graduating in 2028 with a CGPA of 8.8 and is highly interested in PyTorch, ROS, and computer vision.",
            document_id="onboarding_static",
            context="user_profile",
            tags=["userId:satish"]
        )
        print("Retain result:", res)

        print("Recalling memory...")
        rec = await client.recall(
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
        await client.close()

asyncio.run(main())
