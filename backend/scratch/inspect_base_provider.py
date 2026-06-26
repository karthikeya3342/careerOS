from cascadeflow.providers.base import BaseProvider
import inspect

# Let's inspect abstract methods or required methods in BaseProvider
source = inspect.getsource(BaseProvider)
print("BaseProvider class definition:")
lines = source.splitlines()
for idx, line in enumerate(lines):
    if "def " in line:
        print(f"  Line {idx+1}: {line.strip()}")
