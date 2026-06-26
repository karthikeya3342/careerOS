import cascadeflow
from cascadeflow import CascadeAgent, ModelConfig
import inspect

print("Cascadeflow version:", getattr(cascadeflow, "__version__", "unknown"))
print("ModelConfig parameters:", inspect.signature(ModelConfig.__init__))
print("CascadeAgent parameters:", inspect.signature(CascadeAgent.__init__))
