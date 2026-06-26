import os
import cascadeflow
import inspect

cf_dir = os.path.dirname(cascadeflow.__file__)
print("Searching in:", cf_dir)

for root, dirs, files in os.walk(cf_dir):
    for f in files:
        if f.endswith(".py"):
            path = os.path.join(root, f)
            content = open(path, errors="ignore").read()
            if "class CascadeAgent" in content:
                print("Found CascadeAgent in:", f)
                # Let's read lines where providers are initialized
                lines = content.splitlines()
                for idx, line in enumerate(lines):
                    if "Provider(" in line or "provider" in line.lower() and ("init" in line or "create" in line or "setup" in line):
                        print(f"  Line {idx+1}: {line.strip()}")
            if "class ModelConfig" in content:
                print("Found ModelConfig in:", f)
