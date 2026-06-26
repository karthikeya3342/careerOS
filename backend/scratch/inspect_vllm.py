from cascadeflow.providers.vllm import VLLMProvider
import inspect

# Let's inspect class VLLMProvider init and complete
print("VLLMProvider init signature:", inspect.signature(VLLMProvider.__init__))
print("VLLMProvider source code:")
try:
    print(inspect.getsource(VLLMProvider.__init__))
except Exception as e:
    print("Error getting source:", e)
