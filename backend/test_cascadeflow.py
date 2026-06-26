import os
import asyncio
from cascadeflow import CascadeAgent, ModelConfig

# GROQ_API_KEY should be set in the environment or .env file

async def test():
    try:
        # Define CascadeAgent
        agent = CascadeAgent(models=[
            ModelConfig(name="qwen/qwen3.6-27b", provider="groq", cost=0.0001),
            ModelConfig(name="openai/gpt-oss-120b", provider="groq", cost=0.0005)
        ])
        
        print("Running agent...")
        res = await agent.run("State the capital of France in one word.")
        print("Result content:", res.content)
        print("Model used:", res.model_used)
        print("Cost:", res.total_cost)
    except Exception as e:
        print("Error:", e)

asyncio.run(test())
