import inspect
from cascadeflow.providers.base import BaseProvider

# Let's print the methods
print("estimate_cost signature:", inspect.signature(BaseProvider.estimate_cost))
print("estimate_cost source:")
print(inspect.getsource(BaseProvider.estimate_cost))

print("\n_stream_impl signature:", inspect.signature(BaseProvider._stream_impl))
print("_stream_impl source:")
print(inspect.getsource(BaseProvider._stream_impl))
