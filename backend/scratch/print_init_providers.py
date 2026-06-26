from cascadeflow import CascadeAgent
import inspect

source = inspect.getsource(CascadeAgent._init_providers)
print(source)
