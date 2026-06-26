from hindsight_client import Hindsight
import inspect

client = Hindsight(
    base_url="https://api.hindsight.vectorize.io",
    api_key="hsk_4f6be8344c78c821af2d0acf69e0a480_186211b302780c78"
)

sig = inspect.signature(client.mental_models.create_mental_model)
print("client.mental_models.create_mental_model signature:", sig)
