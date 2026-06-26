from hindsight_client import Hindsight
import inspect

client = Hindsight(
    base_url="https://api.hindsight.vectorize.io",
    api_key="hsk_4f6be8344c78c821af2d0acf69e0a480_186211b302780c78"
)

methods = [name for name, val in inspect.getmembers(client) if not name.startswith('_')]
print("Methods in Hindsight client:", methods)
