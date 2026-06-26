import os
import cascadeflow

path = os.path.join(os.path.dirname(cascadeflow.__file__), "providers", "__init__.py")
if os.path.exists(path):
    print(open(path, errors="ignore").read())
else:
    print("providers/__init__.py not found.")
