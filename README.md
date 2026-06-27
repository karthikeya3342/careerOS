# CareerOS — Autonomous Multi-Agent Career Optimization Engine

CareerOS is an advanced, autonomous multi-agent developer command center designed to automate profile ingestion, resume tailoring, ATS evaluation loops, and outreach preparation. 

By leveraging a structured multi-agent architecture (Drafter and Verifier models), CareerOS crawls public data (GitHub commits, LeetCode, Codeforces, CodeChef), synthesizes candidate records into a Hindsight vector memory store, tailors LaTeX resumes to match job descriptions, runs ATS scoring feedback loops, and compiles print-ready PDFs.

---

## 🏗️ System Architecture & Multi-Agent Design

CareerOS runs a two-pronged autonomous pipeline: an **Automated Daily Job Discovery & Email Digest** pipeline, and a **Resume Optimization & Tailoring** pipeline.

### 1. Automated Job Discovery & Daily Email Digest (8:00 AM Cron)
Every morning at 8:00 AM, the inline background scheduler automatically initiates the following workflow:
```mermaid
graph TD
    Cron[8:00 AM Daily Trigger] -->|Clear Database| CleanDb[Clear non-starred jobs from Database]
    CleanDb -->|Initialize| ScrapAgent[JobScrapingAgent]
    
    ScrapAgent -->|Query Engines| JobSpy[JobSpy: Indeed, LinkedIn, Glassdoor]
    ScrapAgent -->|Query Scrapers| JobScout[Job-Scout: Naukri, Apna, Shine, Foundit]
    
    JobSpy -->|Aggregate| Store[Update jobs_db.json]
    JobScout -->|Aggregate| Store
    
    Store -->|Compile top 10 & CSV| MailGen[Build Email Digest & CSV attachment]
    MailGen -->|Send Message| AgentMail[AgentMail API]
    AgentMail -->|Deliver Digest| User[Candidate Inbox]
```

### 2. Multi-Agent Resume Optimization & ATS Feedback Loop
When a candidate selects a job from the dashboard and clicks **Apply & Optimize**, the tailoring loop starts:
```mermaid
graph TD
    E[Opportunities Board] -->|Selected JD| F[Pre-Router & Complexity Agent]
    F -->|Load Static Profile| D[(Hindsight Memory Bank)]
    
    F -->|Drafter Agent| G[Gemini 3.1 Flash Lite]
    G -->|Tailored TeX Resume| H[Verifier Agent: Llama 3.3 70B]
    
    H -->|ATS Evaluation Loop| I{Score >= 80%?}
    I -->|No: Feedback Adjustments| G
    I -->|Yes| J[PDF LaTeX Compiler]
    
    J -->|Output Directory| K[PDF / TeX / Outreach MD / Prep Guide]
```

### 🤖 Core Agents
1. **JobScrapingAgent**: Programmatically retrieves candidate parameters from profile configuration, generates search queries, executes scraping across multiple job boards concurrently (LinkedIn, Indeed, Glassdoor via JobSpy, and Naukri, Apna, Shine, Foundit via Job-Scout), filters, and saves them to local storage.
2. **Profile Synthesizer Agent**: Takes manual onboarding fields, crawled social metrics, and raw previous resume details, executing an LLM synthesis step to construct a structured Markdown candidate profile stored in the Hindsight Vector Memory.
3. **Commit Verification Agent**: Queries GitHub commits for each repo to verify actual authorship, filtering out template forks and imports.
4. **Complexity & Pre-Router**: Routes tasks dynamically to the most efficient model based on task complexity.
5. **Drafter Agent**: Tailors resume content using Google's **XYZ Bullet Formula** (*Accomplished [X], as measured by [Y], by doing [Z]*), selecting the most relevant projects and experiences matching the job description.
6. **Verifier Agent**: Computes the ATS match score, extracts key strengths, identifies missing requirements, and feeds improvements back to the Drafter for correction.
7. **TeX Compiler & Self-Correction Agent**: Compiles LaTeX files to PDF via API and scans compilation error logs to automatically self-correct layout issues.

---

## 🛠️ Technology Stack
- **Backend**: FastAPI, Python 3.10+, Uvicorn, Cascadeflow orchestration, Hindsight Memory Layer, Groq API, Google AI Studio.
- **Frontend**: Next.js 15+ (App Router), React 19, Tailwind CSS v4, Google Fonts (Outfit & JetBrains Mono).

---

## 🚀 Setup & Installation

### Prerequisites
Make sure you have the following installed:
- Python 3.10+
- Node.js 18+ & npm
- Git

---

### 1. Backend Setup (FastAPI)

1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. Install required Python packages:
   ```bash
   pip install -r requirements.txt
   ```
   *(Ensure `cascadeflow`, `fastapi`, `uvicorn`, `groq`, `google-generativeai`, `python-dotenv`, and other dependencies are installed)*

4. Install Playwright browser dependencies (needed for Apna and Foundit scrapers):
   ```bash
   playwright install chromium
   ```

5. Configure the Environment Variables:
   Create a `.env` file in the `backend/` directory:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   GEMINI_API_KEY=your_gemini_api_key_here
   HINDSIGHT_API_KEY=your_hindsight_api_key_here
   AGENTMAIL_API_KEY=your_agentmail_api_key_here
   AGENTMAIL_INBOX_ID=your_agentmail_inbox_id_here
   ```

6. Initialize the Simulated Jobs Database:
   Generate mock jobs (Machine Learning, Robotics, Software Engineering, etc.):
   ```bash
   python generate_jobs.py
   ```

7. Launch the backend API server:
   ```bash
   python main.py
   ```
   The backend API will start running on `http://localhost:8000`.

---

### 2. Frontend Setup (Next.js)

1. Navigate to the `frontend` directory:
   ```bash
   cd ../frontend
   ```

2. Install Node modules:
   ```bash
   npm install
   ```

3. Configure Environment Variables (Optional):
   By default, the frontend connects to `http://localhost:8000`. If your backend runs on a custom port, create a `.env.local` file:
   ```env
   NEXT_PUBLIC_API_BASE=http://localhost:8000
   ```

4. Launch the Next.js development server:
   ```bash
   npm run dev
   ```
   The frontend command console will start running on `http://localhost:3000`. Open it in your browser.

---

## 🖥️ Usage Guide

1. **Profile Ingestion**:
   - Go to the **Profile Ingestion** tab.
   - Fill in your basic details, add your crawler URLs (GitHub, LeetCode, Codeforces, etc.), paste your previous resume, and click **Sync & Synthesize Profile**.
   - Your synthesized factual profile will sync with Hindsight Cloud and render in the **Factual Memory** panel.

2. **Calibrate Jobs**:
   - Go to the **Opportunities Board** tab.
   - Filter jobs by category, search by skills, or filter for **Starred Only** to show saved opportunities.
   - Click **View Details** to inspect required competencies or click **Apply & Optimize** to launch the multi-agent pipeline.

3. **Automated 8 AM Discovery & Email Digest**:
   - **Fresh Opportunities Daily**: Every morning at 8:00 AM, the inline background scheduler activates.
   - **Starred Jobs Preservation**: Before scraping, the system wipes previous jobs to prevent clutter. However, all **starred jobs** are preserved in the local database and dashboard.
   - **Aggregated Scraping**: The `JobScrapingAgent` crawls multiple directories (Indeed, LinkedIn, Glassdoor, Naukri, Apna, Shine, Foundit) concurrently to collect the latest matching internships.
   - **AgentMail Email Digest**: On completion, it compiles the top 10 new job matches into a premium HTML email and attaches a compiled CSV of all scraped jobs, sending it to your email via **AgentMail**.
   - **Manual Run**: You can also force a scrape and email run at any time using the manual trigger button on the frontend console.

4. **Monitor Live Pipeline**:
   - When optimization is triggered, the progress line will fill, indicating active agents.
   - The **Pipeline Terminal Output** logs real-time agent completions, reasoning, and compile diagnostics.

5. **Applications & Downloads**:
   - Go to the **Applications** tab.
   - Click **View Analysis & Output** to open the details panel.
   - Toggle **ATS Analysis** to check matching strengths and improvements.
   - Toggle **Resume Preview** to inspect a formatted document representation of the generated LaTeX.
   - Download compiled PDFs, TeX source codes, outreach email templates, and interview prep guides, or click **Overleaf** to edit the TeX code directly in your browser.

---

## 🔒 Security
- All sensitive variables, API keys, and credential tags are isolated in `.env` files.
- `.gitignore` is configured at the root level to prevent staging environment secrets, Python caches, and temporary build PDF/TeX outputs.
