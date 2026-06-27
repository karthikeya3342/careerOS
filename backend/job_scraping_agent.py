import os
import sys
import re
import json
import hashlib
import asyncio
from typing import List, Dict, Any
from groq import Groq
from dotenv import load_dotenv
from hindsight_helper import HindsightMemoryManager

# Add job-scout and JobSpy directories to python path
scout_path = os.path.join(os.path.dirname(__file__), "job-scout")
if scout_path not in sys.path:
    sys.path.insert(0, scout_path)

jobspy_path = os.path.join(os.path.dirname(__file__), "JobSpy")
if jobspy_path not in sys.path:
    sys.path.insert(0, jobspy_path)

# Import job-scout scrapers
from scrapers.apna import scrape_apna
from scrapers.shine import scrape_shine
from scrapers.naukri import scrape_naukri
from scrapers.foundit import scrape_foundit
from scrapers.glassdoor import scrape_glassdoor

# Import JobSpy
from jobspy import scrape_jobs

load_dotenv()

groq_key = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=groq_key)
WORKHORSE_MODEL = "llama-3.3-70b-versatile"

# Normalized Category Helper
def classify_category(title: str, query_role: str) -> str:
    combined = (title + " " + query_role).lower()
    if "machine learning" in combined or "ml" in combined or "computer vision" in combined or "nlp" in combined:
        return "Machine Learning"
    if "robot" in combined or "kinematics" in combined or "ros" in combined:
        return "Robotics"
    if "react" in combined or "frontend" in combined or "ui developer" in combined or "next.js" in combined:
        return "Frontend Development"
    if "devops" in combined or "cloud" in combined or "kubernetes" in combined or "aws" in combined:
        return "Cloud & DevOps"
    if "data science" in combined or "data analyst" in combined:
        return "Data Science"
    if "full stack" in combined or "fullstack" in combined:
        return "Full Stack Development"
    if "support" in combined or "helpdesk" in combined or "sysadmin" in combined or "it tech" in combined:
        return "IT & Support"
    return "Software Engineering"

class JobScrapingAgent:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.mem_mgr = HindsightMemoryManager()

    async def get_user_context(self) -> Dict[str, str]:
        """Fetch candidate profile and preferences from Hindsight memory bank."""
        await self.mem_mgr.initialize_bank()
        profile_text = ""
        preferences = ""
        
        try:
            doc = await self.mem_mgr.client.documents.get_document(self.mem_mgr.bank_id, f"{self.user_id}_onboarding_static")
            if doc and hasattr(doc, "original_text") and doc.original_text:
                profile_text = doc.original_text
        except Exception as e:
            print(f"[ScraperAgent] Failed to fetch onboarding static document: {e}")
            
        # Fallback to search query if direct fetch fails
        if not profile_text:
            memories = await self.mem_mgr.recall_memories("What is my core career profile?", [f"userId:{self.user_id}"])
            if memories:
                profile_text = "\n".join(memories)
                
        try:
            preferences = await self.mem_mgr.fetch_user_mental_model(self.user_id)
        except Exception as e:
            print(f"[ScraperAgent] Failed to fetch user mental model preferences: {e}")
            
        await self.mem_mgr.close()
        
        return {
            "profile": profile_text or "No detailed profile found. Use default tech keywords.",
            "preferences": preferences or "No preferences recorded yet."
        }

    async def synthesize_queries(self, context: Dict[str, str]) -> Dict[str, Any]:
        """Ask LLM to recommend optimal search roles and target locations based on profile."""
        system_prompt = (
            "You are the AI Job Search Architect for careerOS. Your task is to analyze a candidate's profile "
            "and active preferences to formulate the most optimal search criteria for scraping job boards.\n\n"
            "CRITICAL PERSONALIZATION RULES:\n"
            "1. **Student Status & Graduation Year**: Check if the candidate is currently a student (e.g., they have not graduated yet, class year is in the future like 2026/2027/2028). "
            "   - If they are a student, you MUST strictly target **Internships, Co-ops, and Student Programs**. All synthesized roles MUST include keywords like 'Intern', 'Internship', 'Co-op', or 'Summer Intern'. Do NOT target full-time or senior roles (e.g., do NOT synthesize 'Software Engineer' or 'Robotics Engineer' without the word 'Intern' or 'Internship').\n"
            "   - If they have already graduated and have full-time experience, synthesize entry-level or standard roles appropriate for their experience level.\n"
            "2. **Domain/Skills Alignment**: Focus on the candidate's specific background, core skills, and minor/specializations (e.g. Robotics, AI/ML, Full Stack, Frontend).\n"
            "3. **Location Strategy**: Check if they prefer remote, hybrid, or specific cities. If no location preferences are specified, default to tech hubs in their region (e.g., 'Bengaluru', 'Hyderabad', 'Remote' for India-based candidates). All locations synthesized MUST be strictly inside the candidate's local country (e.g. Indian cities like Bengaluru, Hyderabad, Chennai, Mumbai, Pune, Delhi, Noida, Gurgaon if they are based in India) or Remote. Do NOT synthesize international locations.\n\n"
            "Synthesize:\n"
            "Generate a JSON object containing a list of target `roles` (query keywords, up to 3), a list of target `locations` (up to 3), and the primary `job_type` (either 'internship' or 'full_time'). "
            "Keep roles/keywords concise and direct for search engines (e.g., 'Software Engineer Intern', 'ML Intern'). Locations should be simple, e.g. 'Bengaluru', 'Remote'.\n\n"
            "Your output must be ONLY a valid JSON block of this schema, with no additional text or markdown formatting:\n"
            "{\n"
            "  \"roles\": [\"keyword1\", \"keyword2\", \"keyword3\"],\n"
            "  \"locations\": [\"location1\", \"location2\", \"location3\"],\n"
            "  \"job_type\": \"internship\"\n"
            "}"
        )
        
        user_prompt = (
            f"Candidate Profile Summary:\n{context['profile']}\n\n"
            f"Candidate Preferences & Mental Model:\n{context['preferences']}\n"
        )
        
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: groq_client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    model=WORKHORSE_MODEL,
                    temperature=0.2,
                    response_format={"type": "json_object"}
                )
            )
            data = json.loads(response.choices[0].message.content)
            print("[ScraperAgent] Synthesized query parameters from LLM:", data)
            return data
        except Exception as e:
            print(f"[ScraperAgent] Error in LLM synthesis: {e}")
            # Fallback default values
            return {
                "roles": ["Software Engineer Intern", "SDE Intern"],
                "locations": ["Bengaluru", "Remote"],
                "job_type": "internship"
            }

    def run_scrapers(self, roles: List[str], locations: List[str], job_type: str = None) -> List[Dict[str, Any]]:
        """Routes and runs the appropriate scrapers based on location."""
        scraped_jobs = []
        
        for role in roles:
            for loc in locations:
                print(f"\n[ScraperAgent] Searching for '{role}' in '{loc}'...")
                
                # Determine if it's an Indian location
                is_india = False
                normalized_loc = loc.lower()
                india_city_map = {
                    "bangalore": "Bengaluru",
                    "bengaluru": "Bengaluru",
                    "hyderabad": "Hyderabad",
                    "mumbai": "Mumbai",
                    "pune": "Pune",
                    "chennai": "Chennai",
                    "delhi": "Delhi",
                    "noida": "Noida",
                    "gurugram": "Gurugram",
                    "gurgaon": "Gurugram"
                }
                
                matched_india_city = None
                for k, v in india_city_map.items():
                    if k in normalized_loc:
                        is_india = True
                        matched_india_city = v
                        break
                
                # Source 1: JobSpy (Indeed, LinkedIn, Glassdoor)
                print(f"[ScraperAgent] Querying JobSpy (Indeed, LinkedIn, Glassdoor) for '{role}' in '{loc}'...")
                try:
                    # Run JobSpy (Indeed, LinkedIn, Glassdoor)
                    df = scrape_jobs(
                        site_name=["indeed", "linkedin", "glassdoor"],
                        search_term=role,
                        location=loc,
                        results_wanted=5,
                        hours_old=72,  # 3 days freshness
                        job_type=job_type,
                        verbose=1
                    )
                    if df is not None and not df.empty:
                        # Replace all NaN values with None to be JSON-serializable
                        df = df.astype(object).where(df.notnull(), None)
                        records = df.to_dict(orient="records")
                        for r in records:
                            # Normalize JobSpy attributes
                            apply_url = r.get("job_url") or ""
                            if not apply_url:
                                continue
                                
                            skills_str = r.get("skills") or ""
                            skills_list = [s.strip() for s in skills_str.split(",") if s.strip()] if isinstance(skills_str, str) else []
                            if not skills_list and isinstance(r.get("skills"), list):
                                skills_list = r.get("skills")
                                
                            category = classify_category(r.get("title", ""), role)
                            
                            job_item = {
                                "id": f"scraped-jobspy-{hashlib.md5(apply_url.encode('utf-8')).hexdigest()[:12]}",
                                "title": r.get("title") or "Unknown Role",
                                "company": r.get("company") or "Unknown Company",
                                "category": category,
                                "experience_years": r.get("experience_years") or 0,
                                "skills": skills_list,
                                "description": r.get("description") or "",
                                "location": r.get("location") or loc,
                                "type": r.get("job_type") or "Full-time",
                                "apply_url": apply_url,
                                "source": r.get("site") or "jobspy"
                            }
                            scraped_jobs.append(job_item)
                        print(f"[ScraperAgent] JobSpy yielded {len(records)} jobs.")
                except Exception as e:
                    print(f"[ScraperAgent] JobSpy query failed: {e}")
                
                # Fallback for Glassdoor on Indian locations
                glassdoor_jobs_count = sum(1 for j in scraped_jobs if j.get("source") == "glassdoor")
                if is_india and matched_india_city and glassdoor_jobs_count == 0:
                    print(f"[ScraperAgent] JobSpy yielded 0 Glassdoor jobs. Falling back to Playwright Glassdoor scraper for '{matched_india_city}'...")
                    try:
                        gd_res = scrape_glassdoor(role=role, from_age_days=3, limit=5, locations=[matched_india_city])
                        for r in gd_res:
                            apply_url = r.get("Link") or r.get("apply_url") or ""
                            if not apply_url:
                                continue
                            category = classify_category(r.get("Job Title", ""), role)
                            job_item = {
                                "id": f"scraped-glassdoor-{hashlib.md5(apply_url.encode('utf-8')).hexdigest()[:12]}",
                                "title": r.get("Job Title") or "Unknown Role",
                                "company": r.get("Company") or "Unknown Company",
                                "category": category,
                                "experience_years": 0,
                                "skills": [],
                                "description": r.get("Description") or "",
                                "location": r.get("Location") or matched_india_city,
                                "type": "Full-time",
                                "apply_url": apply_url,
                                "source": "glassdoor"
                            }
                            scraped_jobs.append(job_item)
                        print(f"[ScraperAgent] Playwright Glassdoor scraper yielded {len(gd_res)} jobs.")
                    except Exception as e:
                        print(f"[ScraperAgent] Playwright Glassdoor scraper failed: {e}")
                
                # Source 2: job-scout (Naukri, Apna, Shine, Foundit)
                if is_india and matched_india_city:
                    print(f"[ScraperAgent] India city detected: '{matched_india_city}'. Querying job-scout scrapers...")
                    
                    # A. Naukri
                    try:
                        print(f"[ScraperAgent] Querying Naukri for '{role}' in '{matched_india_city}'...")
                        naukri_res = scrape_naukri(role=role, city=matched_india_city, job_age_days=3, limit=5)
                        for r in naukri_res:
                            apply_url = r.get("Link") or r.get("apply_url") or ""
                            if not apply_url:
                                continue
                            skills_str = r.get("Skills") or ""
                            skills_list = [s.strip() for s in skills_str.split(",") if s.strip()]
                            category = classify_category(r.get("Job Title", ""), role)
                            job_item = {
                                "id": f"scraped-naukri-{hashlib.md5(apply_url.encode('utf-8')).hexdigest()[:12]}",
                                "title": r.get("Job Title") or "Unknown Role",
                                "company": r.get("Company") or "Unknown Company",
                                "category": category,
                                "experience_years": 0, # Default
                                "skills": skills_list,
                                "description": r.get("Description") or "",
                                "location": r.get("Location") or matched_india_city,
                                "type": "Full-time",
                                "apply_url": apply_url,
                                "source": "naukri"
                            }
                            scraped_jobs.append(job_item)
                        print(f"[ScraperAgent] Naukri yielded {len(naukri_res)} jobs.")
                    except Exception as e:
                        print(f"[ScraperAgent] Naukri scraper failed: {e}")
                        
                    # B. Apna
                    try:
                        # Apna only supports Bengaluru, Mumbai, Delhi NCR, Hyderabad, Chennai, Pune, Kolkata, Ahmedabad
                        apna_city = matched_india_city
                        if apna_city == "Delhi":
                            apna_city = "Delhi NCR"
                        elif apna_city in ("Noida", "Gurugram"):
                            apna_city = "Delhi NCR"
                            
                        print(f"[ScraperAgent] Querying Apna for '{role}' in '{apna_city}'...")
                        apna_res = scrape_apna(role=role, city=apna_city, posted_in_days=3, limit=5)
                        for r in apna_res:
                            apply_url = r.get("Link") or r.get("apply_url") or ""
                            if not apply_url:
                                continue
                            skills_str = r.get("Skills") or ""
                            skills_list = [s.strip() for s in skills_str.split(",") if s.strip()]
                            category = classify_category(r.get("Job Title", ""), role)
                            job_item = {
                                "id": f"scraped-apna-{hashlib.md5(apply_url.encode('utf-8')).hexdigest()[:12]}",
                                "title": r.get("Job Title") or "Unknown Role",
                                "company": r.get("Company") or "Unknown Company",
                                "category": category,
                                "experience_years": 0,
                                "skills": skills_list,
                                "description": r.get("Description") or "",
                                "location": r.get("Location") or apna_city,
                                "type": r.get("Workplace") or "Full-time",
                                "apply_url": apply_url,
                                "source": "apna"
                            }
                            scraped_jobs.append(job_item)
                        print(f"[ScraperAgent] Apna yielded {len(apna_res)} jobs.")
                    except Exception as e:
                        print(f"[ScraperAgent] Apna scraper failed: {e}")
                        
                    # C. Shine
                    try:
                        shine_city = matched_india_city
                        # Shine uses "Bangalore" instead of "Bengaluru", and "Gurgaon" instead of "Gurugram"
                        if shine_city == "Bengaluru":
                            shine_city = "Bangalore"
                        elif shine_city == "Gurugram":
                            shine_city = "Gurgaon"
                            
                        print(f"[ScraperAgent] Querying Shine for '{role}' in '{shine_city}'...")
                        shine_res = scrape_shine(role=role, city=shine_city, posting_days=3, limit=5)
                        for r in shine_res:
                            apply_url = r.get("Link") or r.get("apply_url") or ""
                            if not apply_url:
                                continue
                            skills_str = r.get("Skills") or ""
                            skills_list = [s.strip() for s in skills_str.split(",") if s.strip()]
                            category = classify_category(r.get("Job Title", ""), role)
                            job_item = {
                                "id": f"scraped-shine-{hashlib.md5(apply_url.encode('utf-8')).hexdigest()[:12]}",
                                "title": r.get("Job Title") or "Unknown Role",
                                "company": r.get("Company") or "Unknown Company",
                                "category": category,
                                "experience_years": 0,
                                "skills": skills_list,
                                "description": r.get("Description") or "",
                                "location": r.get("Location") or shine_city,
                                "type": "Full-time",
                                "apply_url": apply_url,
                                "source": "shine"
                            }
                            scraped_jobs.append(job_item)
                        print(f"[ScraperAgent] Shine yielded {len(shine_res)} jobs.")
                    except Exception as e:
                        print(f"[ScraperAgent] Shine scraper failed: {e}")
                        
                    # D. Foundit
                    try:
                        print(f"[ScraperAgent] Querying Foundit for '{role}' in '{matched_india_city}'...")
                        foundit_res = scrape_foundit(role=role, city=matched_india_city, job_freshness_days=3, limit=5)
                        for r in foundit_res:
                            apply_url = r.get("Link") or r.get("apply_url") or ""
                            if not apply_url:
                                continue
                            skills_str = r.get("Skills") or ""
                            skills_list = [s.strip() for s in skills_str.split(",") if s.strip()]
                            category = classify_category(r.get("Job Title", ""), role)
                            job_item = {
                                "id": f"scraped-foundit-{hashlib.md5(apply_url.encode('utf-8')).hexdigest()[:12]}",
                                "title": r.get("Job Title") or "Unknown Role",
                                "company": r.get("Company") or "Unknown Company",
                                "category": category,
                                "experience_years": 0,
                                "skills": skills_list,
                                "description": r.get("Description") or "",
                                "location": r.get("Location") or matched_india_city,
                                "type": "Full-time",
                                "apply_url": apply_url,
                                "source": "foundit"
                            }
                            scraped_jobs.append(job_item)
                        print(f"[ScraperAgent] Foundit yielded {len(foundit_res)} jobs.")
                    except Exception as e:
                        print(f"[ScraperAgent] Foundit scraper failed: {e}")
                        
        return scraped_jobs

    def _clean_nan(self, val):
        import math
        if isinstance(val, float) and math.isnan(val):
            return None
        if isinstance(val, list):
            return [self._clean_nan(x) for x in val]
        if isinstance(val, dict):
            return {k: self._clean_nan(v) for k, v in val.items()}
        return val

    def consolidate_jobs(self, scraped_jobs: List[Dict[str, Any]]) -> int:
        """Merge newly scraped jobs into jobs_db.json, eliminating duplicates."""
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(backend_dir, "jobs_db.json")
        
        # Load existing jobs
        existing_jobs = []
        if os.path.exists(db_path):
            try:
                with open(db_path, "r", encoding="utf-8") as f:
                    existing_jobs = json.load(f)
            except Exception as e:
                print(f"[ScraperAgent] Error reading jobs database: {e}")
                
        # Index of existing URLs to avoid duplicates
        existing_urls = {j.get("apply_url") or j.get("Link") or j.get("job_url") for j in existing_jobs if j.get("apply_url") or j.get("Link") or j.get("job_url")}
        
        newly_added = 0
        merged_jobs = list(existing_jobs)
        
        for job in scraped_jobs:
            url = job.get("apply_url")
            if url and url not in existing_urls:
                merged_jobs.insert(0, job)  # Add new jobs to the beginning of the list
                existing_urls.add(url)
                newly_added += 1
                
        # Write merged list back
        if newly_added > 0:
            # Clean all records to ensure strict JSON compliance (no NaN floats)
            cleaned_jobs = [self._clean_nan(job) for job in merged_jobs]
            try:
                with open(db_path, "w", encoding="utf-8") as f:
                    json.dump(cleaned_jobs, f, indent=4, allow_nan=False)
                print(f"[ScraperAgent] Consolidated {newly_added} new jobs into {db_path}.")
            except Exception as e:
                print(f"[ScraperAgent] Failed to save updated jobs list: {e}")
                
        return newly_added

    async def run(self) -> int:
        """Runs the entire personalized job scraping agent workflow."""
        print(f"\n[ScraperAgent] Starting personalized job search agent for User ID: {self.user_id}...")
        
        # Step 1: Recall profile and preferences
        context = await self.get_user_context()
        
        # Step 2: Synthesize search queries (roles and locations)
        queries = await self.synthesize_queries(context)
        
        # Step 3: Run the scrapers (JobSpy + job-scout)
        # Using loop.run_in_executor to avoid blocking event loop
        loop = asyncio.get_event_loop()
        scraped_jobs = await loop.run_in_executor(
            None,
            lambda: self.run_scrapers(
                queries.get("roles", []),
                queries.get("locations", []),
                queries.get("job_type")
            )
        )
        
        # Post-Scrape Strict Filter for Student Internships
        job_type = queries.get("job_type")
        if job_type == "internship":
            print("[ScraperAgent] Applying strict post-scrape filter for student internships...")
            filtered_jobs = []
            indian_cities = {
                "bengaluru", "bangalore", "hyderabad", "chennai", "mumbai", "pune", "delhi", 
                "noida", "gurugram", "gurgaon", "kolkata", "ahmedabad", "jaipur"
            }
            for job in scraped_jobs:
                title = job.get("title", "").lower()
                location = job.get("location", "").lower()
                
                # Rule 1: Title must contain internship keywords
                is_intern = any(w in title for w in ["intern", "co-op", "coop", "trainee", "student", "fellow"])
                
                # Rule 2: Country / Location check (Only Remote or Indian tech cities)
                is_local = False
                if "remote" in location:
                    is_local = True
                elif any(city in location for city in indian_cities):
                    is_local = True
                elif "india" in location:
                    is_local = True
                
                if is_intern and is_local:
                    filtered_jobs.append(job)
                else:
                    safe_title = str(job.get('title', '')).encode('ascii', 'replace').decode('ascii')
                    safe_loc = str(job.get('location', '')).encode('ascii', 'replace').decode('ascii')
                    print(f"[ScraperAgent] Filtered out non-matching job: {safe_title} at {safe_loc}")
            scraped_jobs = filtered_jobs
        
        # Step 4: Save and merge results
        new_count = self.consolidate_jobs(scraped_jobs)
        
        print(f"[ScraperAgent] Finished agent run. Yielded {len(scraped_jobs)} total scraped jobs, {new_count} new.")
        return new_count
