import inspect
from cascadeflow.providers.vllm import VLLMProvider

source = inspect.getsource(VLLMProvider)
lines = source.splitlines()
for idx, line in enumerate(lines):
    if "ModelError" in line:
        print(f"Line {idx+1}: {line.strip()}")
        # print some surrounding lines
        start = max(0, idx - 10)
        end = min(len(lines), idx + 10)
        print("Surrounding lines:")
        for i in range(start, end):
            print(f"  {i+1}: {lines[i]}")
        print("-" * 40)
