import os
import json

log_dir = r"C:\Users\satis\.gemini\antigravity\brain\f7f79896-55ca-439e-b5d6-8d75238f40e6\.system_generated\logs"
t_path = os.path.join(log_dir, "transcript.jsonl")

if os.path.exists(t_path):
    steps = []
    with open(t_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            try:
                steps.append(json.loads(line))
            except Exception:
                pass
                
    for idx in range(1700, len(steps)):
        s = steps[idx]
        print(f"\n=== STEP {s.get('step_index')} ===")
        print(f"Type: {s.get('type')}")
        print(f"Source: {s.get('source')}")
        content = s.get('content', '')
        if content:
            print("Content:", content[:400].encode("ascii", errors="replace").decode("ascii"))
        else:
            print("Content: None")
        for tc in s.get("tool_calls", []):
            print("Tool call:", tc.get("name"), str(tc.get("args"))[:200].encode("ascii", errors="replace").decode("ascii"))
else:
    print("Transcript not found.")
