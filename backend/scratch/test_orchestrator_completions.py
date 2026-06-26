import asyncio
from agent_orchestrator import safe_groq_only_completion, safe_groq_completion

async def test():
    messages = [
        {"role": "system", "content": "You are a helpful assistant. Reply in one word."},
        {"role": "user", "content": "What is the capital of France?"}
    ]
    
    print("Testing safe_groq_only_completion...")
    res1 = await safe_groq_only_completion(messages)
    print("Result 1:", res1)
    
    print("Testing safe_groq_completion...")
    res2 = await safe_groq_completion(None, messages)
    print("Result 2:", res2)

asyncio.run(test())
