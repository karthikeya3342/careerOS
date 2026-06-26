import cascadeflow.providers as providers
import inspect

for name, obj in inspect.getmembers(providers):
    if inspect.isclass(obj):
        print(f"Class: {name}, module: {obj.__module__}")
