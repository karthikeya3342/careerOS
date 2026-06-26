import os
from hindsight_client import Hindsight

client = Hindsight(
    base_url="https://api.hindsight.vectorize.io",
    api_key="hsk_4f6be8344c78c821af2d0acf69e0a480_186211b302780c78"
)

try:
    print("Testing connection...")
    banks = client.list_banks()
    print("Banks list:", banks)
except Exception as e:
    print("Error:", e)
