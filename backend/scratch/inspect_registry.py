import cascadeflow
# Let's inspect where PROVIDER_REGISTRY is in cascadeflow
for attr in dir(cascadeflow):
    if "REGISTRY" in attr or "registry" in attr.lower():
        print(f"Attr: {attr}")

# Let's inspect cascadeflow.agent
import cascadeflow.agent as agent
if hasattr(agent, "PROVIDER_REGISTRY"):
    print("Found PROVIDER_REGISTRY in cascadeflow.agent:")
    for k, v in agent.PROVIDER_REGISTRY.items():
        print(f"  {k} -> {v.__name__}")
elif hasattr(cascadeflow, "PROVIDER_REGISTRY"):
    print("Found PROVIDER_REGISTRY in cascadeflow:")
    for k, v in cascadeflow.PROVIDER_REGISTRY.items():
        print(f"  {k} -> {v.__name__}")
