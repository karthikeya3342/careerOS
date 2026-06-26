from hindsight_client import Hindsight
import inspect
import asyncio

client = Hindsight(
    base_url="https://api.hindsight.vectorize.io",
    api_key="hsk_4f6be8344c78c821af2d0acf69e0a480_186211b302780c78"
)

print("Methods in client.mental_models:", [name for name, _ in inspect.getmembers(client.mental_models) if not name.startswith('_')])
