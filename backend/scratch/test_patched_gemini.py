import os
import asyncio
from dotenv import load_dotenv
load_dotenv()

# Import cascadeflow components
import cascadeflow
from cascadeflow import CascadeAgent, ModelConfig
from cascadeflow.providers.base import BaseProvider, ModelResponse
import cascadeflow.providers as cf_providers

# Define custom GeminiProvider
class GeminiProvider(BaseProvider):
    def __init__(self, api_key=None, retry_config=None, http_config=None):
        super().__init__(api_key=api_key, retry_config=retry_config, http_config=http_config)
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        
    def _load_api_key(self):
        return os.getenv("GEMINI_API_KEY")
        
    def _check_logprobs_support(self):
        return False
        
    def estimate_cost(self, tokens: int, model: str) -> float:
        return (tokens / 1000) * 0.000075
        
    async def _stream_impl(self, prompt: str, model: str, max_tokens: int = 4096, temperature: float = 0.7, system_prompt=None, **kwargs):
        res = await self._complete_impl(prompt=prompt, model=model, max_tokens=max_tokens, temperature=temperature, system_prompt=system_prompt, **kwargs)
        yield res.content
        
    async def _complete_impl(self, prompt=None, model="", max_tokens=4096, temperature=0.7, system_prompt=None, messages=None, **kwargs):
        import httpx
        import time
        
        msgs = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})
        if messages:
            msgs.extend(messages)
        elif prompt:
            msgs.append({"role": "user", "content": prompt})
            
        gemini_contents = []
        system_instruction = None
        
        for m in msgs:
            role = m["role"]
            if role == "system":
                system_instruction = {"parts": [{"text": m["content"]}]}
                continue
            if role == "assistant":
                role = "model"
            gemini_contents.append({
                "role": role,
                "parts": [{"text": m["content"]}]
            })
            
        payload = {
            "contents": gemini_contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens
            }
        }
        if system_instruction:
            payload["systemInstruction"] = system_instruction
            
        gemini_model = model or "gemini-3.1-flash-lite"
        if "/" in gemini_model:
            gemini_model = gemini_model.split("/")[-1]
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent?key={self.api_key}"
        
        start_time = time.time()
        async with httpx.AsyncClient(timeout=180.0) as client:
            resp = await client.post(url, json=payload, headers={"Content-Type": "application/json"})
            resp.raise_for_status()
            resp_data = resp.json()
            
            parts = resp_data["candidates"][0]["content"]["parts"]
            actual_text = ""
            for part in parts:
                if not part.get("thought", False):
                    actual_text += part.get("text", "")
            
            latency_ms = (time.time() - start_time) * 1000
            prompt_text = "".join(m["content"] for m in msgs)
            prompt_tokens = len(prompt_text) // 4
            completion_tokens = len(actual_text) // 4
            tokens_used = prompt_tokens + completion_tokens
            
            cost = self.estimate_cost(tokens_used, gemini_model)
            
            response = ModelResponse(
                content=actual_text.strip(),
                model=gemini_model,
                provider="gemini",
                cost=cost,
                tokens_used=tokens_used,
                confidence=0.85,
                latency_ms=latency_ms,
                metadata={"finish_reason": "stop"}
            )
            return response

# Register in PROVIDER_REGISTRY under "custom"
cf_providers.PROVIDER_REGISTRY["custom"] = GeminiProvider

async def test():
    import logging
    logging.getLogger("cascadeflow").setLevel(logging.WARNING)

    # Initialize CascadeAgent
    agent = CascadeAgent(models=[
        ModelConfig(
            name="gemini-3.1-flash-lite",
            provider="custom",
            cost=0.000075,
            api_key=os.getenv("GEMINI_API_KEY")
        ),
        ModelConfig(
            name="llama-3.3-70b-versatile",
            provider="groq",
            cost=0.00015,
            api_key=os.getenv("GROQ_API_KEY")
        )
    ])
    
    print("Running CascadeAgent...")
    res = await agent.run("State the capital of Italy in one word.")
    print("Result content:", res.content)
    print("Model used:", res.model_used)
    print("Cost:", res.total_cost)

asyncio.run(test())
