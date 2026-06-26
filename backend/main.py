import os
import glob
import csv
import json
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, List
import onboarding_agent
import agent_orchestrator

app = FastAPI(title="CareerOS API", description="Autonomous Multi-Agent Career Assistant API")

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

@app.get("/api/jobs/discover")
def discover_jobs(
    q: Optional[str] = None,
    category: Optional[str] = None,
    page: int = 1,
    limit: int = 10
):
    try:
        with open("jobs_db.json", "r") as f:
            jobs = json.load(f)
            
        filtered = jobs
        if q:
            q_lower = q.lower()
            filtered = [
                j for j in filtered
                if q_lower in j["title"].lower() or q_lower in j["company"].lower() or q_lower in j["description"].lower() or any(q_lower in s.lower() for s in j["skills"])
            ]
        if category:
            filtered = [j for j in filtered if j["category"].lower() == category.lower()]
            
        start = (page - 1) * limit
        end = start + limit
        paginated = filtered[start:end]
        
        return {
            "total": len(filtered),
            "page": page,
            "limit": limit,
            "jobs": paginated
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/jobs/apply")
async def apply_to_job(payload: ApplyRequest):
    try:
        jd_text = payload.jd_text
        if payload.job_id:
            # Load from jobs database
            with open("jobs_db.json", "r") as f:
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
            
            # Default values
            app_info = {
                "id": d,
                "company": d.split("_")[0],
                "role": "_".join(d.split("_")[1:]) if len(d.split("_")) > 1 else "Unknown Role",
                "ats_score": 0,
                "strengths": [],
                "improvements": [],
                "has_pdf": os.path.exists(os.path.join(path, "resume.pdf")),
                "has_tex": os.path.exists(os.path.join(path, "resume.tex")),
                "has_prep": os.path.exists(os.path.join(path, "interview_readiness.pdf")),
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
def download_file(app_id: str, filename: str):
    file_path = os.path.join("output", app_id, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
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
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
