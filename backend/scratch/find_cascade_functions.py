import os
import json

log_dir = r"C:\Users\satis\.gemini\antigravity\brain\f7f79896-55ca-439e-b5d6-8d75238f40e6\.system_generated\logs"
t_path = os.path.join(log_dir, "transcript_full.jsonl")

if os.path.exists(t_path):
    with open(t_path, "r", encoding="utf-8", errors="ignore") as f:
        for idx, line in enumerate(f):
            try:
                d = json.loads(line)
                content = d.get("content", "")
                if "def safe_groq_only_completion" in content and "CascadeAgent" in content:
                    print(f"Found CascadeAgent version on line {idx+1} (step {d.get('step_index')})")
                    # Let's save a chunk of lines
                    lines = content.splitlines()
                    # Find start of safe_groq_only_completion
                    start_line = -1
                    for i, l in enumerate(lines):
                        if "async def safe_groq_only_completion" in l:
                            start_line = i
                            break
                    if start_line != -1:
                        chunk = "\n".join(lines[start_line:start_line+100])
                        print(chunk)
                        print("=" * 50)
            except Exception as e:
                pass
else:
    print("Transcript not found.")
