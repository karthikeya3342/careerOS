from cascadeflow.providers.groq import GroqProvider
import inspect

source = inspect.getsource(GroqProvider)
lines = source.splitlines()
print("GroqProvider source (first 100 lines):")
for i in range(min(100, len(lines))):
    print(lines[i].encode("ascii", errors="replace").decode("ascii"))
