import cascadeflow.core.cascade as cascade
import inspect

print("inspecting get_provider or similar functions in cascadeflow.core.cascade:")
funcs = [name for name, obj in inspect.getmembers(cascade) if inspect.isfunction(obj)]
print("Functions in cascade:", funcs)

# Let's inspect ModelConfig provider mapping if it exists
from cascadeflow.providers import BaseProvider
# Let's search cascadeflow/core/cascade.py source for 'provider' instantiations
# We can print code of _get_provider if it exists
if hasattr(cascade, "_get_provider"):
    print(inspect.getsource(cascade._get_provider))
elif hasattr(cascade, "CascadeAgent"):
    # let's look inside CascadeAgent methods
    methods = [name for name, obj in inspect.getmembers(cascade.CascadeAgent) if inspect.isfunction(obj)]
    print("Methods in CascadeAgent:", methods)
