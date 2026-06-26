from groq import Groq

import os
client = Groq()

try:
    models = client.models.list()
    print("Available Groq Models:")
    for m in models.data:
        print(f"- {m.id}")
except Exception as e:
    print("Error:", e)
