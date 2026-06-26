"""
Utility functions for LLM providers.
"""

import logging
from typing import Any, Dict, Optional
from models import ModelProvider, OllamaProvider, GeminiProvider
from prompt import MODEL_PROVIDER_MAPPING, GEMINI_API_KEY

logger = logging.getLogger(__name__)


def extract_json_from_response(response_text: str) -> str:
    """
    Extract JSON content from markdown code blocks.

    Args:
        response_text: Text that may contain JSON wrapped in markdown code blocks

    Returns:
        Text with markdown code block syntax removed
    """

    response_text = response_text.strip()
    if "<think>" in response_text:
        think_start = response_text.find("<think>")
        think_end = response_text.find("</think>")
        if think_start != -1 and think_end != -1:
            response_text = response_text[:think_start] + response_text[think_end + 8 :]

    # Remove leading ```json if present
    if response_text.startswith("```json"):
        response_text = response_text[7:]
    # Remove trailing ``` if present
    if response_text.endswith("```"):
        response_text = response_text[:-3]
    return response_text


def initialize_llm_provider(model_name: str) -> Any:
    """
    Initialize the appropriate LLM provider based on the model name.
    Modified to always return a Gemini REST API provider using gemma-4-31b-it.
    """
    class GeminiProvider:
        def chat(self, model: str, messages: list, options: dict = None, **kwargs) -> dict:
            import time
            import requests
            import os
            
            system_content = next((msg["content"] for msg in messages if msg["role"] == "system"), "")
            is_extraction = "parser" in system_content.lower() or "extract" in system_content.lower()
            
            temperature = 0.1
            if options:
                temperature = options.get("temperature", 0.1)

            if is_extraction:
                # Fast route: Groq llama-3.3-70b-versatile for simple parsing
                try:
                    from groq import Groq
                    groq_key = os.environ.get("GROQ_API_KEY")
                    client = Groq(api_key=groq_key)
                    for attempt in range(3):
                        try:
                            completion = client.chat.completions.create(
                                model="llama-3.3-70b-versatile",
                                messages=messages,
                                temperature=temperature
                            )
                            content = completion.choices[0].message.content.strip()
                            return {"message": {"role": "assistant", "content": content}}
                        except Exception as e:
                            wait_time = (2 ** attempt) * 2.0
                            print(f"[Hiring-Agent] Groq error: {e}. Retrying in {wait_time}s...")
                            time.sleep(wait_time)
                except Exception as e:
                    print(f"[Hiring-Agent] Failed to route to Groq: {e}. Falling back to Gemini...")
            
            api_key = os.getenv("GEMINI_API_KEY")
            
            gemini_contents = []
            for msg in messages:
                role = msg["role"]
                if role == "assistant":
                    role = "model"
                gemini_contents.append({
                    "role": role,
                    "parts": [{"text": msg["content"]}]
                })
                
            payload = {
                "contents": gemini_contents,
                "generationConfig": {
                    "temperature": temperature
                }
            }
            
            for attempt in range(5):
                gemini_model = "gemma-4-26b-a4b-it"
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent?key={api_key}"
                try:
                    resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=120.0)
                    if resp.status_code == 200:
                        resp_data = resp.json()
                        parts = resp_data["candidates"][0]["content"]["parts"]
                        actual_text = ""
                        for part in parts:
                            if not part.get("thought", False):
                                actual_text += part.get("text", "")
                        return {"message": {"role": "assistant", "content": actual_text.strip()}}
                    elif resp.status_code == 429:
                        wait_time = (2 ** attempt) * 4.0
                        print(f"[Hiring-Agent] Gemini API 429. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        print(f"[Hiring-Agent] Gemini HTTP Error {resp.status_code}: {resp.text[:200]}")
                        wait_time = (2 ** attempt) * 3.0
                        time.sleep(wait_time)
                except Exception as e:
                    print(f"[Hiring-Agent] Gemini network error: {e}")
                    wait_time = (2 ** attempt) * 3.0
                    time.sleep(wait_time)
            raise Exception("Hiring-Agent Gemini API call failed after retries.")
            
    return GeminiProvider()

