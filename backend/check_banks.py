from hindsight_client import Hindsight

client = Hindsight(
    base_url="https://api.hindsight.vectorize.io",
    api_key="hsk_4f6be8344c78c821af2d0acf69e0a480_186211b302780c78"
)

try:
    print("type of client.banks:", type(client.banks))
    # Let's inspect methods of client.banks
    import inspect
    print("methods in client.banks:", [name for name, _ in inspect.getmembers(client.banks) if not name.startswith('_')])
    # Let's list banks
    res = client.banks.list()
    print("list response:", res)
except Exception as e:
    print("Error:", e)
