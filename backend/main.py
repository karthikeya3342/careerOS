import os
import glob
import csv
import json
import asyncio
import base64
import urllib.request
from contextlib import asynccontextmanager
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, List
import onboarding_agent
import agent_orchestrator
from job_scraping_agent import JobScrapingAgent

# ─────────────────────────────────────────────
# Inline Scheduler (runs as background asyncio task)
# ─────────────────────────────────────────────
AGENTMAIL_API_KEY = os.getenv("AGENTMAIL_API_KEY", "")
INBOX_ID = os.getenv("AGENTMAIL_INBOX_ID", "")

def _compile_csv(jobs):
    import io, csv as _csv
    out = io.StringIO()
    w = _csv.writer(out)
    w.writerow(["ID", "Title", "Company", "Location", "Category", "Skills", "Apply URL"])
    for j in jobs:
        w.writerow([j.get("id",""), j.get("title",""), j.get("company",""),
                    j.get("location",""), j.get("category",""),
                    ", ".join(j.get("skills",[])), j.get("apply_url","")])
    return out.getvalue()

def _send_mail(to_email, subject, html, text, csv_str=None):
    url = f"https://api.agentmail.to/v0/inboxes/{INBOX_ID}/messages/send"
    payload = {"to": to_email, "subject": subject, "text": text, "html": html}
    if csv_str:
        payload["attachments"] = [{
            "filename": "scraped_jobs.csv",
            "content_type": "text/csv",
            "content_disposition": "attachment",
            "content": base64.b64encode(csv_str.encode()).decode()
        }]
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {AGENTMAIL_API_KEY}",
                 "Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req) as r:
            print(f"[Scheduler] Email sent -> {to_email} | status {r.status}")
    except Exception as e:
        print(f"[Scheduler] Email failed: {e}")

async def daily_scraping_job(user_id: str, to_email: str, run_scrape: bool = True):
    _backend_dir = os.path.dirname(os.path.abspath(__file__))
    _db_path = os.path.join(_backend_dir, "jobs_db.json")
    print(f"[Scheduler] Running daily job for {user_id} -> {to_email} (run_scrape={run_scrape})")

    if run_scrape:
        # Clear non-starred jobs
        if os.path.exists(_db_path):
            with open(_db_path, "r", encoding="utf-8") as f:
                jobs = json.load(f)
            with open(_db_path, "w", encoding="utf-8") as f:
                json.dump([j for j in jobs if j.get("starred")], f, indent=4)

        # Scrape
        try:
            agent = JobScrapingAgent(user_id)
            new_count = await agent.run()
        except Exception as e:
            print(f"[Scheduler] Scraper error: {e}")
            new_count = 0

    # Load results
    try:
        with open(_db_path, "r", encoding="utf-8") as f:
            all_jobs = json.load(f)
    except Exception:
        all_jobs = []
    new_jobs = [j for j in all_jobs if not j.get("starred")]
    print(f"[Scheduler] {len(new_jobs)} new jobs scraped.")

    if not new_jobs:
        _send_mail(to_email,
            f"[careerOS] Daily Digest – {datetime.now().strftime('%Y-%m-%d')}",
            "<p>No new matching internships today. Check your starred jobs in the console.</p>",
            "No new matching internships today.")
        return

    top10 = new_jobs[:10]
    items_html = "".join([
        f"""<div style='border:3px solid #2B2D42;padding:15px;margin-bottom:14px;box-shadow:3px 3px 0 #2B2D42'>
            <p style='margin:0 0 4px 0;font-size:11px;font-weight:bold;color:#8D99AE;text-transform:uppercase'>{j.get('location','')}</p>
            <h3 style='margin:0 0 4px 0;color:#2B2D42'>{j.get('title','')}</h3>
            <p style='margin:0 0 10px 0;color:#EF233C;font-weight:bold;font-size:12px'>{j.get('company','')}</p>
            <a href='{j.get('apply_url','#')}' style='background:#EF233C;color:#fff;padding:6px 12px;
               border:2px solid #2B2D42;font-weight:bold;font-size:11px;text-decoration:none'>Job Link →</a>
            </div>""" for j in top10])
    html = f"""
    <html><body style='font-family:sans-serif;max-width:600px;margin:0 auto;padding:20px;background:#F4F4F9'>
    <div style='border:4px solid #2B2D42;padding:25px;background:#fff;box-shadow:5px 5px 0 #2B2D42'>
        <h1 style='color:#2B2D42;border-bottom:4px solid #2B2D42;padding-bottom:10px;text-transform:uppercase'>careerOS Daily Digest</h1>
        <p>AI scraper ran at <strong>8:00 AM</strong> and found <strong>{len(new_jobs)} new internships</strong>.<br>
           Full list attached as CSV. Top 10 below:</p>
        {items_html}
        <div style='border-top:2px solid #2B2D42;padding-top:20px;text-align:center'>
            <a href='http://localhost:3000' style='background:#EF233C;color:#fff;border:4px solid #2B2D42;
               padding:12px 24px;font-weight:bold;text-decoration:none;text-transform:uppercase'>Open Dashboard</a>
        </div>
    </div></body></html>"""
    _send_mail(to_email,
        f"[careerOS] 🚀 {len(new_jobs)} Tailored Internships – {datetime.now().strftime('%Y-%m-%d')}",
        html, f"{len(new_jobs)} new internships found. See attachment.",
        _compile_csv(new_jobs))

async def _scheduler_loop():
    print("[Scheduler] Background loop started — will trigger daily at 08:00 AM.")
    _backend_dir = os.path.dirname(os.path.abspath(__file__))
    last_run_day = None
    while True:
        try:
            now = datetime.now()
            if now.hour == 8 and now.minute == 0 and last_run_day != now.day:
                cfg_path = os.path.join(_backend_dir, "users_config.json")
                fallback  = os.path.join(_backend_dir, "user_config.json")
                users = {}
                if os.path.exists(cfg_path):
                    with open(cfg_path, "r", encoding="utf-8") as f:
                        users = json.load(f)
                elif os.path.exists(fallback):
                    with open(fallback, "r", encoding="utf-8") as f:
                        c = json.load(f)
                    if c.get("user_id"):
                        users[c["user_id"]] = c
                if users:
                    print(f"[Scheduler] Triggering for {len(users)} user(s)...")
                    await asyncio.gather(*[
                        daily_scraping_job(u["user_id"], u["email"])
                        for u in users.values() if u.get("user_id") and u.get("email")
                    ])
                    last_run_day = now.day
                else:
                    print("[Scheduler] No registered users yet.")
                await asyncio.sleep(60)   # skip rest of this minute
            else:
                await asyncio.sleep(15)
        except Exception as e:
            print(f"[Scheduler] Loop error: {e}")
            await asyncio.sleep(15)

def _suppress_connection_reset(loop, context):
    # WinError 10054 = connection forcibly closed by remote host.
    # This is a harmless Windows asyncio/ProactorEventLoop artefact
    # that fires when a browser closes a connection mid-flight.
    exc = context.get("exception")
    if isinstance(exc, ConnectionResetError):
        return  # silently ignore
    loop.default_exception_handler(context)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Suppress harmless Windows socket noise
    loop = asyncio.get_event_loop()
    loop.set_exception_handler(_suppress_connection_reset)
    # Start background scheduler when server boots
    task = asyncio.create_task(_scheduler_loop())
    yield
    # Graceful shutdown
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

app = FastAPI(title="CareerOS API",
              description="Autonomous Multi-Agent Career Assistant API",
              lifespan=lifespan)

backend_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(backend_dir, "jobs_db.json")

# Enable CORS for Next.js app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class OnboardRequest(BaseModel):
    user_id: str
    name: str
    email: str
    phone: Optional[str] = ""
    github: str
    leetcode: Optional[str] = ""
    codeforces: Optional[str] = ""
    codechef: Optional[str] = ""
    linkedin: Optional[str] = ""
    portfolio: Optional[str] = ""
    education: Optional[str] = ""
    cgpa: Optional[str] = ""
    experience: Optional[str] = ""
    previous_resume_text: Optional[str] = ""

class ApplyRequest(BaseModel):
    user_id: str
    job_id: Optional[str] = None
    jd_text: Optional[str] = None

class ScrapeRequest(BaseModel):
    user_id: str

class SaveEmailRequest(BaseModel):
    email: str
    user_id: str

@app.post("/api/onboard")
async def onboard_user(payload: OnboardRequest):
    try:
        urls = {
            "name": payload.name,
            "email": payload.email,
            "phone": payload.phone,
            "github": payload.github,
            "leetcode": payload.leetcode,
            "codeforces": payload.codeforces,
            "codechef": payload.codechef,
            "linkedin": payload.linkedin,
            "portfolio": payload.portfolio,
            "education": payload.education,
            "cgpa": payload.cgpa,
            "experience": payload.experience,
            "previous_resume_text": payload.previous_resume_text
        }
        res = await onboarding_agent.run_onboarding_pipeline(payload.user_id, urls)
        return {"status": "success", "profile": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/jobs/scrape")
async def scrape_jobs_for_user(payload: ScrapeRequest):
    try:
        agent = JobScrapingAgent(payload.user_id)
        new_count = await agent.run()
        return {"status": "success", "new_jobs_count": new_count}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/user/save-email")
def save_user_email(payload: SaveEmailRequest):
    try:
        config_path = os.path.join(os.path.dirname(__file__), "users_config.json")
        users = {}
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    users = json.load(f)
            except Exception:
                users = {}
        users[payload.user_id] = {
            "email": payload.email,
            "user_id": payload.user_id
        }
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=4)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/user/test-email")
async def trigger_test_email(user_id: Optional[str] = None):
    try:
        _backend_dir = os.path.dirname(os.path.abspath(__file__))
        cfg_path = os.path.join(_backend_dir, "users_config.json")
        fallback  = os.path.join(_backend_dir, "user_config.json")

        users: dict = {}
        if os.path.exists(cfg_path):
            with open(cfg_path, "r", encoding="utf-8") as f:
                users = json.load(f)
        elif os.path.exists(fallback):
            with open(fallback, "r", encoding="utf-8") as f:
                c = json.load(f)
            if c.get("user_id"):
                users[c["user_id"]] = c

        if not users:
            raise HTTPException(status_code=400,
                detail="No registered users found. Please log in or reload the page first.")

        if user_id:
            if user_id not in users:
                raise HTTPException(status_code=404,
                    detail=f"User config for '{user_id}' not found.")
            u = users[user_id]
            await daily_scraping_job(u["user_id"], u["email"], run_scrape=False)
            return {"status": "success",
                    "message": f"Test digest email triggered and sent to {u['email']}."}
        else:
            await asyncio.gather(*[
                daily_scraping_job(u["user_id"], u["email"], run_scrape=False)
                for u in users.values() if u.get("user_id") and u.get("email")
            ])
            return {"status": "success",
                    "message": f"Daily digest triggered for all {len(users)} users."}
    except HTTPException:
        raise
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/jobs/clear")
async def clear_all_jobs():
    try:
        with open(db_path, "r", encoding="utf-8") as f:
            jobs = json.load(f)
        # Only keep starred jobs
        kept_jobs = [j for j in jobs if j.get("starred", False)]
        with open(db_path, "w", encoding="utf-8") as f:
            json.dump(kept_jobs, f, indent=4)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/jobs/{job_id}/toggle-star")
def toggle_star_job(job_id: str):
    try:
        with open(db_path, "r", encoding="utf-8") as f:
            jobs = json.load(f)
        for j in jobs:
            if j["id"] == job_id:
                j["starred"] = not j.get("starred", False)
                break
        with open(db_path, "w", encoding="utf-8") as f:
            json.dump(jobs, f, indent=4)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/jobs/{job_id}")
def delete_job(job_id: str):
    try:
        with open(db_path, "r", encoding="utf-8") as f:
            jobs = json.load(f)
        jobs = [j for j in jobs if j["id"] != job_id]
        with open(db_path, "w", encoding="utf-8") as f:
            json.dump(jobs, f, indent=4)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_unique_locations(jobs) -> List[str]:
    import re
    unique = set()
    ignore_words = {
        "india", "karnataka", "tamil nadu", "us", "ca", "mi", "ga", "fl", "nc", "il", "texas",
        "united states", "remote", "hybrid", "onsite", "in", "and", "plus"
    }
    for j in jobs:
        loc = j.get("location")
        if not loc:
            continue
        parts = re.split(r'[,/;]|\band\b', loc)
        for p in parts:
            p_clean = re.sub(r'\+\d+|\bplus\b', '', p)
            val = p_clean.strip().strip('+0123456789 ')
            if not val:
                continue
            val_lower = val.lower()
            if val_lower in ignore_words:
                continue
            
            # Normalize common cities
            if "bangalore" in val_lower or "bengaluru" in val_lower:
                unique.add("Bengaluru")
            elif "remote" in val_lower:
                unique.add("Remote")
            elif "hyderabad" in val_lower:
                unique.add("Hyderabad")
            elif "chennai" in val_lower:
                unique.add("Chennai")
            elif "noida" in val_lower:
                unique.add("Noida")
            elif "mumbai" in val_lower:
                unique.add("Mumbai")
            elif "pune" in val_lower:
                unique.add("Pune")
            else:
                unique.add(val.title())
    return sorted(list(unique))

@app.get("/api/jobs/discover")
def discover_jobs(
    q: Optional[str] = None,
    category: Optional[str] = None,
    location: Optional[str] = None,
    starred_only: bool = False,
    page: int = 1,
    limit: int = 10
):
    try:
        with open(db_path, "r", encoding="utf-8") as f:
            jobs = json.load(f)

        filtered = jobs

        # Starred-only filter
        if starred_only:
            filtered = [j for j in filtered if j.get("starred", False)]

        if q:
            q_lower = q.lower()
            filtered = [
                j for j in filtered
                if q_lower in j["title"].lower() or q_lower in j["company"].lower() or q_lower in j["description"].lower() or any(q_lower in s.lower() for s in j["skills"])
            ]
        if category:
            filtered = [j for j in filtered if j.get("category") and j["category"].lower() == category.lower()]
        if location:
            loc_lower = location.lower()
            if loc_lower in ["bengaluru", "bangalore"]:
                filtered = [
                    j for j in filtered
                    if j.get("location") and ("bengaluru" in j["location"].lower() or "bangalore" in j["location"].lower())
                ]
            else:
                filtered = [
                    j for j in filtered
                    if j.get("location") and loc_lower in j["location"].lower()
                ]

        start = (page - 1) * limit
        end = start + limit
        paginated = filtered[start:end]

        all_locations = get_unique_locations(jobs)

        return {
            "total": len(filtered),
            "page": page,
            "limit": limit,
            "jobs": paginated,
            "locations": all_locations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/jobs/apply")
async def apply_to_job(payload: ApplyRequest):
    try:
        jd_text = payload.jd_text
        if payload.job_id:
            # Load from jobs database
            with open(db_path, "r", encoding="utf-8") as f:
                jobs = json.load(f)
            job = next((j for j in jobs if j["id"] == payload.job_id), None)
            if not job:
                raise HTTPException(status_code=404, detail="Job not found")
            jd_text = f"Title: {job['title']}\nCompany: {job['company']}\nLocation: {job['location']}\nDescription: {job['description']}\nSkills: {', '.join(job['skills'])}"
            
        if not jd_text:
            raise HTTPException(status_code=400, detail="Must provide job_id or jd_text")
            
        res = await agent_orchestrator.process_job_application(payload.user_id, jd_text)
        return res
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/pipeline-status/{user_id}")
def get_pipeline_status(user_id: str):
    status_path = f"output/{user_id}_status.json"
    if os.path.exists(status_path):
        try:
            with open(status_path, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"stage": "Idle", "details": "No active optimization running."}

@app.get("/api/profile/{user_id}")
async def get_user_profile(user_id: str):
    from hindsight_helper import HindsightMemoryManager
    mem_mgr = HindsightMemoryManager()
    await mem_mgr.initialize_bank()
    try:
        profile_text = ""
        # Attempt to get the full onboarding static document directly
        try:
            doc = await mem_mgr.client.documents.get_document(mem_mgr.bank_id, f"{user_id}_onboarding_static")
            if doc and hasattr(doc, "original_text") and doc.original_text:
                profile_text = doc.original_text
        except Exception as e:
            print(f"Direct get_document failed for {user_id}_onboarding_static: {e}")

        # Fallback to semantic query if direct fetch didn't yield result
        if not profile_text:
            memories = await mem_mgr.recall_memories("What is my core career profile?", [f"userId:{user_id}"])
            for m in memories:
                if "Candidate Static Profile:" in m:
                    profile_text = m
                    break
            if not profile_text and memories:
                profile_text = memories[0]
        
        preferences = await mem_mgr.fetch_user_mental_model(user_id)
        await mem_mgr.close()
        
        return {
            "status": "success",
            "profile_summary": profile_text,
            "preferences": preferences
        }
    except Exception as e:
        await mem_mgr.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/applications")
def get_applications():
    try:
        apps = []
        if not os.path.exists("output"):
            return []
            
        # Scan directories in output
        dirs = [d for d in os.listdir("output") if os.path.isdir(os.path.join("output", d))]
        for d in dirs:
            path = os.path.join("output", d)
            csv_path = os.path.join(path, "ats_evaluation_summary.csv")
            
            has_pdf_file = False
            pdf_path = os.path.join(path, "resume.pdf")
            if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 100:
                has_pdf_file = True

            has_prep_file = False
            prep_path = os.path.join(path, "interview_readiness.pdf")
            if os.path.exists(prep_path) and os.path.getsize(prep_path) > 100:
                has_prep_file = True

            # Default values
            app_info = {
                "id": d,
                "company": d.split("_")[0],
                "role": "_".join(d.split("_")[1:]) if len(d.split("_")) > 1 else "Unknown Role",
                "ats_score": 0,
                "strengths": [],
                "improvements": [],
                "has_pdf": has_pdf_file,
                "has_tex": os.path.exists(os.path.join(path, "resume.tex")),
                "has_prep": has_prep_file,
                "has_outreach": os.path.exists(os.path.join(path, "outreach_messages.md"))
            }
            
            # Read CSV if exists
            if os.path.exists(csv_path):
                try:
                    with open(csv_path, "r", encoding="utf-8") as f:
                        reader = csv.reader(f)
                        next(reader)  # Header
                        for row in reader:
                            if len(row) >= 2:
                                k, v = row[0], row[1]
                                if k == "ATS Score":
                                    app_info["ats_score"] = float(v) if v else 0
                                elif k == "Strengths":
                                    app_info["strengths"] = [s.strip() for s in v.split(";") if s.strip()]
                                elif k == "Improvements Needed":
                                    app_info["improvements"] = [s.strip() for s in v.split(";") if s.strip()]
                except Exception as e:
                    print("Error reading CSV:", e)
                    
            apps.append(app_info)
            
        return apps
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/download/{app_id}/{filename}")
def download_file(app_id: str, filename: str, inline: Optional[bool] = False):
    file_path = os.path.join("output", app_id, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    if inline or filename.endswith(".pdf"):
        return FileResponse(file_path)
    return FileResponse(file_path, filename=filename)

@app.get("/api/view-tex/{app_id}")
def view_tex_content(app_id: str):
    file_path = os.path.join("output", app_id, "resume.tex")
    if not os.path.exists(file_path):
         raise HTTPException(status_code=404, detail="LaTeX file not found")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
