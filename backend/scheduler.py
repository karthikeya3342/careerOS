import os
import sys
import json
import base64
import urllib.request
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Ensure backend directory is in python search path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from job_scraping_agent import JobScrapingAgent

load_dotenv(os.path.join(backend_dir, ".env"))

AGENTMAIL_API_KEY = "am_us_inbox_07b7f530b5c0fb42f4b64b116f7472d2d21498851dd95709559fc958bdad9950"
INBOX_ID = "careeros@agentmail.to"

def clear_non_starred_jobs(db_path):
    try:
        if os.path.exists(db_path):
            with open(db_path, "r", encoding="utf-8") as f:
                jobs = json.load(f)
            kept_jobs = [j for j in jobs if j.get("starred", False)]
            with open(db_path, "w", encoding="utf-8") as f:
                json.dump(kept_jobs, f, indent=4)
            print(f"[Scheduler] Pre-scrape clear complete. Kept {len(kept_jobs)} starred jobs.")
            return kept_jobs
        else:
            print("[Scheduler] Database file not found. Initializing empty list.")
            with open(db_path, "w", encoding="utf-8") as f:
                json.dump([], f, indent=4)
            return []
    except Exception as e:
        print(f"[Scheduler] Error during pre-scrape clear: {e}")
        return []

def compile_csv_string(jobs):
    import io
    import csv
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Title", "Company", "Location", "Category", "Skills", "Apply URL"])
    for j in jobs:
        writer.writerow([
            j.get("id", ""),
            j.get("title", ""),
            j.get("company", ""),
            j.get("location", ""),
            j.get("category", ""),
            ", ".join(j.get("skills", [])),
            j.get("apply_url", "")
        ])
    return output.getvalue()

def send_agent_mail(to_email, subject, html_content, text_content, csv_content=None):
    url = f"https://api.agentmail.to/v0/inboxes/{INBOX_ID}/messages/send"
    
    payload = {
        "to": to_email,
        "subject": subject,
        "text": text_content,
        "html": html_content
    }
    
    if csv_content:
        b64_content = base64.b64encode(csv_content.encode("utf-8")).decode("utf-8")
        payload["attachments"] = [{
            "filename": "scraped_jobs.csv",
            "content_type": "text/csv",
            "content_disposition": "attachment",
            "content": b64_content
        }]
        
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {AGENTMAIL_API_KEY}",
            "Content-Type": "application/json"
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as res:
            print(f"[Scheduler] Email sent successfully. Status: {res.status}")
            print(res.read().decode("utf-8"))
    except Exception as e:
        print(f"[Scheduler] Failed to send email via AgentMail: {e}")

async def daily_scraping_job(user_id, to_email):
    print(f"\n[Scheduler] [{datetime.now().isoformat()}] Starting daily scraping task for User ID: {user_id}...")
    
    db_path = os.path.join(backend_dir, "jobs_db.json")
    
    # 1. Clear non-starred jobs
    clear_non_starred_jobs(db_path)
    
    # 2. Run Scraping Agent
    agent = JobScrapingAgent(user_id)
    try:
        new_count = await agent.run()
        print(f"[Scheduler] Scraper complete. Added {new_count} new jobs.")
    except Exception as e:
        print(f"[Scheduler] Scraping failed: {e}")
        new_count = 0
        
    # 3. Load updated jobs
    try:
        with open(db_path, "r", encoding="utf-8") as f:
            jobs = json.load(f)
    except Exception as e:
        print(f"[Scheduler] Failed to read jobs_db: {e}")
        jobs = []
        
    # Get newly scraped jobs (all non-starred ones)
    new_jobs = [j for j in jobs if not j.get("starred", False)]
    print(f"[Scheduler] Found {len(new_jobs)} newly scraped jobs.")
    
    if not new_jobs:
        subject = f"[careerOS] Daily Internship Digest - {datetime.now().strftime('%Y-%m-%d')}"
        text_content = "No new internships matching your preferences were found today. Open your console to check your starred opportunities."
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; max-width: 600px; margin: 0 auto; padding: 20px; color: #2B2D42;">
            <div style="border: 4px solid #2B2D42; padding: 20px; background: #FFFFFF; box-shadow: 4px 4px 0px #2B2D42;">
                <h1 style="text-transform: uppercase; font-size: 24px; color: #EF233C; margin-top: 0;">careerOS Daily Digest</h1>
                <p>Hi Karthikeya,</p>
                <p>Our AI Scraping Agent ran today at 8:00 AM but did not find any brand new internships matching your exact preferences.</p>
                <p>Open your local dashboard to manage your starred applications or start a manual search.</p>
                <br/>
                <p style="font-size: 12px; color: #8D99AE;">careerOS Engine Daemon</p>
            </div>
        </body>
        </html>
        """
        send_agent_mail(to_email, subject, html_content, text_content)
        return

    # Sort new jobs (taking the first 10 for display)
    top_10 = new_jobs[:10]
    
    # Compile HTML body with dynamic CSS inline
    html_items = ""
    for j in top_10:
        skills_tags = "".join([f'<span style="background: #8D99AE; color: #FFFFFF; font-size: 9px; font-weight: bold; padding: 2px 6px; margin-right: 4px; border: 1px solid #2B2D42; display: inline-block;">{s}</span>' for s in j.get("skills", [])[:3]])
        html_items += f"""
        <div style="border: 3px solid #2B2D42; background: #FFFFFF; padding: 15px; margin-bottom: 15px; box-shadow: 3px 3px 0px #2B2D42;">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <span style="background: #2B2D42; color: #F4F4F9; font-size: 9px; font-weight: bold; padding: 2px 6px; text-transform: uppercase;">{j.get("category", "")}</span>
                <span style="font-size: 10px; color: #8D99AE; font-weight: bold;">{j.get("location", "")}</span>
            </div>
            <h3 style="margin: 10px 0 5px 0; color: #2B2D42; font-size: 16px;">{j.get("title", "")}</h3>
            <p style="margin: 0 0 10px 0; color: #EF233C; font-weight: bold; font-size: 12px; text-transform: uppercase;">{j.get("company", "")}</p>
            <div style="margin-bottom: 12px;">{skills_tags}</div>
            <a href="{j.get('apply_url', '#')}" target="_blank" style="display: inline-block; background: #EF233C; color: #FFFFFF; text-decoration: none; border: 2px solid #2B2D42; padding: 6px 12px; font-size: 11px; font-weight: bold; box-shadow: 2px 2px 0px #2B2D42;">Job Link &rarr;</a>
        </div>
        """
        
    subject = f"[careerOS] 🚀 Daily Tailored Internships Compiled - {datetime.now().strftime('%Y-%m-%d')}"
    text_content = f"Compiled {len(new_jobs)} new internships for you. Open your console to apply and optimize."
    
    html_content = f"""
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #F4F4F9; color: #2B2D42;">
        <div style="border: 4px solid #2B2D42; padding: 25px; background: #FFFFFF; box-shadow: 5px 5px 0px #2B2D42;">
            <h1 style="text-transform: uppercase; font-size: 26px; color: #2B2D42; margin-top: 0; border-bottom: 4px solid #2B2D42; padding-bottom: 10px;">careerOS Daily Digest</h1>
            <p style="font-size: 15px; font-weight: bold;">Hi Karthikeya,</p>
            <p>Our AI Scraping Agent ran today at 8:00 AM and compiled <strong>{len(new_jobs)} brand new internships</strong> tailored to your profile (Robotics spec, B.Tech CSE Class of 2028).</p>
            <p>We've attached the full list as a CSV sheet. Here are the <strong>Top 10 Recommendations</strong>:</p>
            
            <div style="margin: 25px 0;">
                {html_items}
            </div>
            
            <div style="border-top: 2px solid #2B2D42; padding-top: 20px; text-align: center;">
                <p style="font-weight: bold; margin-bottom: 15px;">Ready to apply and optimize?</p>
                <a href="http://localhost:3000" style="display: inline-block; background: #EF233C; color: #FFFFFF; text-decoration: none; border: 4px solid #2B2D42; padding: 12px 24px; font-size: 14px; font-weight: bold; box-shadow: 4px 4px 0px #2B2D42; text-transform: uppercase;">Open Console Dashboard</a>
            </div>
            <p style="font-size: 11px; color: #8D99AE; margin-top: 30px; text-align: center;">careerOS Local Agent Daemon &bull; Laptop Host</p>
        </div>
    </body>
    </html>
    """
    
    csv_content = compile_csv_string(new_jobs)
    send_agent_mail(to_email, subject, html_content, text_content, csv_content)

async def main():
    print("[Scheduler] careerOS Automation Daemon started.")
    print("[Scheduler] Monitoring time loop to trigger daily at 8:00 AM local time...")
    config_path = os.path.join(backend_dir, "users_config.json")
    fallback_path = os.path.join(backend_dir, "user_config.json")
    
    last_run_day = None
    
    while True:
        try:
            now = datetime.now()
            # Trigger daily scraping at exactly 8:00 AM
            if now.hour == 8 and now.minute == 0 and last_run_day != now.day:
                users = {}
                if os.path.exists(config_path):
                    with open(config_path, "r", encoding="utf-8") as f:
                        users = json.load(f)
                elif os.path.exists(fallback_path):
                    with open(fallback_path, "r", encoding="utf-8") as f:
                        config = json.load(f)
                    uid = config.get("user_id")
                    if uid:
                        users[uid] = config
                
                if users:
                    print(f"[Scheduler] Daily 8:00 AM trigger: Processing {len(users)} registered users...")
                    tasks = [daily_scraping_job(u["user_id"], u["email"]) for u in users.values() if u.get("user_id") and u.get("email")]
                    if tasks:
                        await asyncio.gather(*tasks)
                        last_run_day = now.day
                    else:
                        print("[Scheduler] No valid user configurations found.")
                else:
                    print("[Scheduler] No registered user configurations found. Waiting for frontend login to populate...")
                
                # Sleep for 60 seconds to avoid trigger repeats
                await asyncio.sleep(60)
            else:
                # Poll every 15 seconds
                await asyncio.sleep(15)
        except Exception as e:
            print(f"[Scheduler] Error in time loop: {e}")
            await asyncio.sleep(15)

if __name__ == "__main__":
    asyncio.run(main())
