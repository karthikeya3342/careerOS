import os
import asyncio
from dotenv import load_dotenv
from hindsight_client import Hindsight
from hindsight_client_api.models import create_mental_model_request, mental_model_trigger_input

# Load environment variables
load_dotenv()

BANK_ID = "career_os_bank"

class HindsightMemoryManager:
    def __init__(self):
        hindsight_url = os.getenv("HINDSIGHT_URL", "https://api.hindsight.vectorize.io")
        hindsight_key = os.getenv("HINDSIGHT_API_KEY")
        self.client = Hindsight(
            base_url=hindsight_url,
            api_key=hindsight_key
        )
        self.bank_id = BANK_ID

    async def initialize_bank(self):
        """Creates the CareerOS memory bank if it doesn't exist."""
        try:
            # We call arecreate_bank or similar, but wait: is there an 'acreate_bank'?
            # Let's inspect signature: client.acreate_bank
            await self.client.acreate_bank(
                bank_id=self.bank_id,
                name="CareerOS Central Memory",
                mission="I am CareerOS, the central memory and adaptive learning engine for career tracking, resumes, and job matches.",
                disposition={"skepticism": 1, "literalism": 1, "empathy": 4}
            )
            print("Memory bank initialized.")
        except Exception as e:
            # Bank might already exist
            print("Bank init message (might exist):", e)

    async def retain_memory(self, content: str, doc_id: str, context: str, tags: list):
        """Retain a memory block (using upsert by doc_id)"""
        try:
            res = await self.client.aretain(
                bank_id=self.bank_id,
                content=content,
                document_id=doc_id,
                context=context,
                tags=tags
            )
            return res
        except Exception as e:
            print(f"Error retaining memory {doc_id}:", e)
            return None

    async def recall_memories(self, query: str, tags: list, max_tokens: int = 10000) -> list:
        """Recall relevant memories matching the query and tags"""
        try:
            res = await self.client.arecall(
                bank_id=self.bank_id,
                query=query,
                tags=tags,
                tags_match="any_strict",
                max_tokens=max_tokens
            )
            if hasattr(res, "results") and res.results:
                return [r.text for r in res.results]
            return []
        except Exception as e:
            print(f"Error recalling memories for query '{query}':", e)
            return []

    async def create_user_mental_model(self, user_id: str):
        """Creates the candidate preferences mental model if it doesn't exist"""
        try:
            # Check if it already exists to avoid duplicate key exceptions
            try:
                existing = await self.client._mental_models_api.get_mental_model(self.bank_id, f"{user_id}-preferences")
                if existing:
                    print(f"Mental model {user_id}-preferences already exists.")
                    return existing
            except Exception:
                pass # Model doesn't exist, proceed to create

            trigger_obj = mental_model_trigger_input.MentalModelTriggerInput(refresh_after_consolidation=True)
            request_obj = create_mental_model_request.CreateMentalModelRequest(
                id=f"{user_id}-preferences",
                name=f"{user_id} Career Preferences",
                source_query="What are this user's preferences regarding startups, remote vs on-site work, and role types based on applications or feedback?",
                tags=[f"userId:{user_id}"],
                trigger=trigger_obj,
            )
            res = await self.client._mental_models_api.create_mental_model(self.bank_id, request_obj)
            return res
        except Exception as e:
            err_str = str(e)
            if "already exists" in err_str or "duplicate key" in err_str:
                print(f"Mental model for {user_id} already exists.")
            else:
                print(f"Error creating mental model for {user_id}:", e)
            return None

    async def fetch_user_mental_model(self, user_id: str) -> str:
        """Fetches the user's mental model preferences"""
        try:
            res = await self.client._mental_models_api.get_mental_model(self.bank_id, f"{user_id}-preferences")
            if hasattr(res, "content") and res.content:
                return res.content
            return ""
        except Exception as e:
            print(f"Error fetching mental model for {user_id}:", e)
            return "No preferences recorded yet."

    async def refresh_user_mental_model(self, user_id: str):
        """Manually trigger refresh of the user mental model"""
        try:
            res = await self.client._mental_models_api.refresh_mental_model(self.bank_id, f"{user_id}-preferences")
            return res
        except Exception as e:
            print(f"Error refreshing mental model for {user_id}:", e)
            return None

    async def close(self):
        try:
            await self.client.aclose()
        except Exception:
            pass
