import asyncio
import json
from onboarding_agent import run_onboarding_pipeline

async def test():
    urls = {
        "name": "Karthikeya",
        "email": "karthikeya@gmail.com",
        "github": "https://github.com/karthikeya3342",
        "leetcode": "https://leetcode.com/karthikeya3342",
        "codeforces": "https://codeforces.com/profile/karthikeya3342",
        "codechef": "https://www.codechef.com/users/karthikeya3342",
        "linkedin": "https://www.linkedin.com/in/karthikeya3342",
        "portfolio": "https://karthikeya.dev"
    }
    print("Starting enhanced onboarding pipeline for karthikeya3342...")
    res = await run_onboarding_pipeline("karthikeya3342", urls)
    print("Onboarding completed successfully. Core profile metadata:")
    # Print a safe non-unicode summary to avoid Windows terminal encoding errors
    safe_profile = {
        "user_id": res.get("user_id"),
        "name": res.get("name"),
        "github_user": res.get("github", {}).get("username"),
        "leetcode_solved": res.get("leetcode", {}).get("total_solved"),
        "codeforces_rating": res.get("codeforces", {}).get("rating"),
        "codechef_rating": res.get("codechef", {}).get("rating")
    }
    print(json.dumps(safe_profile, indent=2))

asyncio.run(test())
