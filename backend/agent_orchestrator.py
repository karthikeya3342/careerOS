import os
import re
import json
import csv
import urllib.parse
import httpx
from dotenv import load_dotenv
from hindsight_helper import HindsightMemoryManager
from hiring_agent_wrapper import evaluate_candidate_resume, evaluate_candidate_profile
from groq import Groq
import logging

# Silence verbose cascadeflow logs
logging.getLogger("cascadeflow").setLevel(logging.ERROR)

# Import cascadeflow components
from cascadeflow import CascadeAgent, ModelConfig
from cascadeflow.providers.base import BaseProvider, ModelResponse
import cascadeflow.providers as cf_providers

# Load environment variables
load_dotenv()

# Define custom GeminiProvider to add native Google AI Studio support to Cascadeflow
class GeminiProvider(BaseProvider):
    def __init__(self, api_key=None, retry_config=None, http_config=None):
        super().__init__(api_key=api_key, retry_config=retry_config, http_config=http_config)
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        
    def _load_api_key(self):
        return os.getenv("GEMINI_API_KEY")
        
    def _check_logprobs_support(self):
        return False
        
    def estimate_cost(self, tokens: int, model: str) -> float:
        return (tokens / 1000) * 0.000075
        
    async def _stream_impl(self, prompt: str, model: str, max_tokens: int = 4096, temperature: float = 0.7, system_prompt=None, **kwargs):
        res = await self._complete_impl(prompt=prompt, model=model, max_tokens=max_tokens, temperature=temperature, system_prompt=system_prompt, **kwargs)
        yield res.content
        
    async def _complete_impl(self, prompt=None, model="", max_tokens=4096, temperature=0.7, system_prompt=None, messages=None, **kwargs):
        import httpx
        import time
        
        msgs = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})
        if messages:
            msgs.extend(messages)
        elif prompt:
            msgs.append({"role": "user", "content": prompt})
            
        gemini_contents = []
        system_instruction = None
        
        for m in msgs:
            role = m["role"]
            if role == "system":
                system_instruction = {"parts": [{"text": m["content"]}]}
                continue
            if role == "assistant":
                role = "model"
            gemini_contents.append({
                "role": role,
                "parts": [{"text": m["content"]}]
            })
            
        payload = {
            "contents": gemini_contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens
            }
        }
        if system_instruction:
            payload["systemInstruction"] = system_instruction
            
        gemini_model = model or "gemini-3.1-flash-lite"
        if "/" in gemini_model:
            gemini_model = gemini_model.split("/")[-1]
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent?key={self.api_key}"
        
        start_time = time.time()
        async with httpx.AsyncClient(timeout=180.0) as client:
            resp = await client.post(url, json=payload, headers={"Content-Type": "application/json"})
            resp.raise_for_status()
            resp_data = resp.json()
            
            parts = resp_data["candidates"][0]["content"]["parts"]
            actual_text = ""
            for part in parts:
                if not part.get("thought", False):
                    actual_text += part.get("text", "")
            
            latency_ms = (time.time() - start_time) * 1000
            prompt_text = "".join(m["content"] for m in msgs)
            prompt_tokens = len(prompt_text) // 4
            completion_tokens = len(actual_text) // 4
            tokens_used = prompt_tokens + completion_tokens
            
            cost = self.estimate_cost(tokens_used, gemini_model)
            
            response = ModelResponse(
                content=actual_text.strip(),
                model=gemini_model,
                provider="gemini",
                cost=cost,
                tokens_used=tokens_used,
                confidence=0.85,
                latency_ms=latency_ms,
                metadata={"finish_reason": "stop"}
            )
            return response

# Register custom GeminiProvider under "custom" key in PROVIDER_REGISTRY
cf_providers.PROVIDER_REGISTRY["custom"] = GeminiProvider

FLAGSHIP_MODEL = "llama-3.3-70b-versatile"

# Initialize Groq client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Define CascadeAgent configurations
quick_models = [
    ModelConfig(name="llama-3.3-70b-versatile", provider="groq", cost=0.00015),
    ModelConfig(name="gemini-3.1-flash-lite", provider="custom", cost=0.000075, api_key=os.getenv("GEMINI_API_KEY"))
]

flagship_models = [
    ModelConfig(name="llama-3.3-70b-versatile", provider="groq", cost=0.00015),
    ModelConfig(name="gemini-3.1-flash-lite", provider="custom", cost=0.000075, api_key=os.getenv("GEMINI_API_KEY"))
]

def update_status(user_id: str, stage: str, details: str = ""):
    """Updates the execution status file for real-time dashboard progress tracking."""
    try:
        os.makedirs("output", exist_ok=True)
        status_path = f"output/{user_id}_status.json"
        with open(status_path, "w") as f:
            json.dump({"stage": stage, "details": details}, f)
    except Exception:
        pass

async def safe_groq_only_completion(messages: list, temperature: float = 0.1, max_retries: int = 4) -> str:
    """Queries Groq/Gemini models using Cascadeflow for quick task parsing and routing."""
    try:
        agent = CascadeAgent(models=quick_models, verbose=False)
        res = await agent.run(query=messages, max_tokens=2000, temperature=temperature)
        return res.content.strip()
    except Exception as e:
        print(f"Cascadeflow quick query failed: {e}")
        # Fallback to direct Gemini REST
        api_key = os.getenv("GEMINI_API_KEY")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent?key={api_key}"
        try:
            gemini_contents = []
            for m in messages:
                role = m["role"]
                if role == "assistant":
                    role = "model"
                gemini_contents.append({"role": role, "parts": [{"text": m["content"]}]})
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(url, json={"contents": gemini_contents, "generationConfig": {"temperature": temperature}})
                if resp.status_code == 200:
                    return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception:
            pass
        raise e

async def safe_groq_completion(model: str, messages: list, temperature: float = 0.2, max_retries: int = 6) -> str:
    """Queries Groq/Gemini models using Cascadeflow for deep reasoning and resume generation tasks."""
    try:
        agent = CascadeAgent(models=flagship_models, verbose=False)
        res = await agent.run(query=messages, max_tokens=4000, temperature=temperature)
        return res.content.strip()
    except Exception as e:
        print(f"Cascadeflow deep query failed: {e}")
        # Fallback to direct Gemini REST
        api_key = os.getenv("GEMINI_API_KEY")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent?key={api_key}"
        try:
            gemini_contents = []
            for m in messages:
                role = m["role"]
                if role == "assistant":
                    role = "model"
                gemini_contents.append({"role": role, "parts": [{"text": m["content"]}]})
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(url, json={"contents": gemini_contents, "generationConfig": {"temperature": temperature}})
                if resp.status_code == 200:
                    return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception:
            pass
        raise e

def clean_latex_special_chars(latex_code: str) -> str:
    """Regex-based helper to escape unescaped special characters (&, %, _) in plain LaTeX text."""
    # Escape unescaped '&' (not preceded by backslash and not inside an HTML-like entity or link)
    latex_code = re.sub(r'(?<!\\)&', r'\&', latex_code)
    # Escape unescaped '_'
    latex_code = re.sub(r'(?<!\\)_', r'\_', latex_code)
    # Escape unescaped '%' (only when not preceded by backslash)
    latex_code = re.sub(r'(?<!\\)%', r'\%', latex_code)
    return latex_code

def clean_latex_code(latex: str) -> str:
    """Removes problematic Unicode characters (e.g. U+202F) and converts quotes/dashes to LaTeX standards."""
    replacements = {
        "\u202f": " ",   # narrow no-break space
        "\u200b": "",    # zero-width space
        "\u00a0": " ",   # non-breaking space
        "\u2013": "--",  # en dash
        "\u2014": "---", # em dash
        "\u2018": "'",   # left single quote
        "\u2019": "'",   # right single quote
        "\u201c": "``",  # left double quote
        "\u201d": "''",  # right double quote
        " ": " ",        # visual narrow space U+202F
    }
    for orig, rep in replacements.items():
        latex = latex.replace(orig, rep)
    # Apply defensive escaping for unescaped & / _ / % characters
    latex = clean_latex_special_chars(latex)
    return latex

async def compile_latex_to_pdf_with_log(latex_code: str, output_path: str) -> tuple[bool, str]:
    """Compiles LaTeX code to a PDF using TeXLive.net API.
    Returns (True, success_msg) or (False, compilation_error_log)."""
    latex_code = clean_latex_code(latex_code)
    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            resp = await client.post(
                "https://texlive.net/cgi-bin/latexcgi",
                files={
                    "filename[]": (None, "document.tex"),
                    "filecontents[]": (None, latex_code),
                    "engine": (None, "pdflatex"),
                    "return": (None, "pdf")
                },
                follow_redirects=True
            )
            if resp.status_code == 200 and resp.content.startswith(b"%PDF"):
                with open(output_path, "wb") as f:
                    f.write(resp.content)
                return True, "PDF saved successfully"
            else:
                error_log = ""
                try:
                    error_log = resp.content.decode("utf-8", errors="ignore")
                except Exception:
                    error_log = "Unknown LaTeX compilation error"
                return False, error_log
    except Exception as e:
        return False, str(e)

async def compile_latex_to_pdf(latex_code: str, output_path: str) -> bool:
    """Compiles LaTeX code to a PDF using TeXLive.net API. Returns True on success, False on error."""
    success, _ = await compile_latex_to_pdf_with_log(latex_code, output_path)
    return success

async def parse_job_description(jd_text: str) -> dict:
    """Parses JD and extracts JSON schema using Qwen 3.6 27b."""
    prompt = f"""
Analyze the following Job Description (JD) and extract details into a JSON object:
{{
  "company": "Company Name",
  "role": "Job Title",
  "skills": ["List", "of", "required", "skills", "and", "technologies"],
  "location": "Location info",
  "type": "Full-time/Internship/Contract",
  "experience_years": 0
}}

Job Description:
{jd_text}

Return ONLY raw JSON block. No explanation, no markdown ticks.
"""
    res_text = await safe_groq_only_completion(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    
    # Strip thoughts or markdown blocks
    if "</think>" in res_text:
        res_text = res_text.split("</think>")[-1].strip()
    if res_text.startswith("```json"):
        res_text = res_text[7:]
    if res_text.endswith("```"):
        res_text = res_text[:-3]
    try:
        return json.loads(res_text.strip())
    except Exception as e:
        print("Failed to parse JD JSON. Content was:", res_text)
        return {
            "company": "Unknown Company",
            "role": "Software Engineer",
            "skills": [],
            "location": "Remote",
            "type": "Full-time",
            "experience_years": 0
        }

async def evaluate_eligibility(user_id: str, parsed_jd: dict, profile_summary: str) -> dict:
    """Compares JD skills/details with profile summary using Qwen 3.6 27b."""
    prompt = f"""
Compare the candidate's profile against the Job Description requirements.

Candidate Profile Summary:
{profile_summary}

Job Description Details:
{json.dumps(parsed_jd, indent=2)}

Decide if the candidate is eligible for this role. For example, if a role requires a Senior Developer (5+ years exp) and the candidate is a student with 0-1 years exp, this is a Total Mismatch. If the role matches their tech stack and level, it's a High Alignment.

Output your evaluation in this JSON format:
{{
  "match_percentage": 85,
  "status": "Eligible / Reject",
  "reason": "1 sentence explanation"
}}
Return ONLY the raw JSON block. No markdown, no comments.
"""
    res_text = await safe_groq_only_completion(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    if "</think>" in res_text:
        res_text = res_text.split("</think>")[-1].strip()
    if res_text.startswith("```json"):
        res_text = res_text[7:]
    if res_text.endswith("```"):
        res_text = res_text[:-3]
    try:
        return json.loads(res_text.strip())
    except Exception:
        return {"match_percentage": 50, "status": "Eligible", "reason": "Evaluated manually."}

async def generate_resume_latex(
    parsed_jd: dict, 
    profile_summary: str, 
    feedback: str, 
    candidate_name: str, 
    candidate_phone: str,
    candidate_email: str, 
    candidate_linkedin: str, 
    candidate_github: str
) -> str:
    """Generates Jake's Resume LaTeX using a one-shot system prompt + lean user message."""
    linkedin_user = candidate_linkedin.split("/in/")[-1].strip("/").split("?")[0] if "/in/" in candidate_linkedin else "linkedin"
    github_user = candidate_github.replace("https://", "").replace("github.com/", "").strip("/")
    feedback_block = f"\n\nATS FEEDBACK FROM PREVIOUS ITERATION (address these in this version):\n{feedback}" if feedback else ""

    # ── ONE-SHOT SYSTEM PROMPT ──────────────────────────────────────────────
    SYSTEM_PROMPT = r"""
You are ResumeGPT — an elite LaTeX resume engineer that produces Jake's Resume format output.
You receive candidate data and a job description, and you output ONE complete, compilation-ready
LaTeX document. Nothing else. No explanation, no markdown fences, no commentary.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 1 — OUTPUT CONTRACT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Output starts with \documentclass and ends with \end{document}. Nothing before or after.
• No markdown code fences (no ```latex). Raw LaTeX only.
• The document must compile with pdflatex on the first attempt — zero undefined commands.
• The document must fit on EXACTLY one page (9pt, Jake margins).
• Every special character in TEXT CONTENT must be escaped:
    & → \&    % → \%    $ → \$    # → \#    _ → \_    ~ → \textasciitilde{}
• Do NOT use any non-ASCII Unicode characters inside LaTeX text fields.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 2 — PREAMBLE (copy verbatim, do not alter)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
\documentclass[letterpaper,9pt]{article}

\usepackage{latexsym}
\usepackage[empty]{fullpage}
\usepackage{titlesec}
\usepackage{marvosym}
\usepackage[usenames,dvipsnames]{color}
\usepackage{verbatim}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{fancyhdr}
\usepackage[english]{babel}
\usepackage{tabularx}
\input{glyphtounicode}

\pagestyle{fancy}
\fancyhf{}
\fancyfoot{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

\addtolength{\oddsidemargin}{-0.5in}
\addtolength{\evensidemargin}{-0.5in}
\addtolength{\textwidth}{1in}
\addtolength{\topmargin}{-.7in}
\addtolength{\textheight}{1.4in}

\urlstyle{same}
\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}

\titleformat{\section}{
  \vspace{-4pt}\scshape\raggedright\large
}{}{0em}{}[\color{black}\titlerule \vspace{-5pt}]

\pdfgentounicode=1

\newcommand{\resumeItem}[1]{
  \item\small{#1 \vspace{-2pt}}
}
\newcommand{\resumeSubheading}[4]{
  \vspace{-2pt}\item
    \begin{tabular*}{0.97\textwidth}[t]{l@{\extracolsep{\fill}}r}
      \textbf{#1} & #2 \\
      \textit{\small#3} & \textit{\small #4} \\
    \end{tabular*}\vspace{-7pt}
}
\newcommand{\resumeSubSubheading}[2]{
    \item
    \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
      \textit{\small#1} & \textit{\small #2} \\
    \end{tabular*}\vspace{-7pt}
}
\newcommand{\resumeProjectHeading}[2]{
    \item
    \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
      \small#1 & #2 \\
    \end{tabular*}\vspace{-7pt}
}
\newcommand{\resumeSubItem}[1]{\resumeItem{#1}\vspace{-4pt}}
\renewcommand\labelitemii{$\vcenter{\hbox{\tiny$\bullet$}}$}
\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=0.15in, label={}]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeItemListStart}{\begin{itemize}}
\newcommand{\resumeItemListEnd}{\end{itemize}\vspace{-5pt}}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 3 — HEADING BLOCK RULE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Use the candidate's SHORT preferred name (first + last only, 2 words max).
The header must be:

\begin{center}
    \textbf{\Huge \scshape <ShortName>} \\ \vspace{1pt}
    \small <phone> $|$ \href{mailto:<email>}{\underline{<email>}} $|$
    \href{<linkedin_url>}{\underline{LinkedIn}} $|$
    \href{<github_url>}{\underline{GitHub}}
\end{center}

Rules:
• Display text for LinkedIn link: the word "LinkedIn" (underlined). NOT the URL.
• Display text for GitHub link: the word "GitHub" (underlined). NOT the URL.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 4 — EDUCATION BLOCK RULE (DYNAMIC COURSEWORK ALIGNMENT)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Use \resumeSubheading with 4 args:
  Arg1 = FULL official university name (no abbreviations)
  Arg2 = City, State/Country
  Arg3 = Full degree + branch. If Minor exists: append "(Minor: <minor>)"
  Arg4 = "Mon YYYY -- Mon YYYY" date range

Add \resumeItemListStart with TWO bullets:
  Bullet 1: "CPI: X.XX/10.0 (after N semesters)" — exact format from profile
  Bullet 2: "Relevant Coursework: <4-6 courses most relevant to the target JD>"
    - Dynamically select courses from the profile that match the JD's specific domain (e.g. prioritize DBMS and Distributed Systems for backend, or Neural Networks for ML roles).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 5 — EXPERIENCE BLOCK RULE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Include an Experience section ONLY if the candidate has real industry/professional experience:
  co-founder role, internship at an external company, full-time employee, freelance contract.
  Academic research assistantships and coursework projects do NOT count.

If experience exists:
  Use \resumeSubheading: Arg1=Company, Arg2=Location, Arg3=Role Title, Arg4=Date range.
  Write EXACTLY 2-3 STAR-method bullets per role.
  Every bullet point must adhere to the Google XYZ Formula: Accomplished [X], as measured by [Y], by doing [Z].
  Begin each bullet with a strong, past-tense engineering verb.

If no real experience exists: OMIT the entire \section{Experience} block.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 6 — PROJECTS BLOCK RULE (DYNAMIC PROJECT SELECTION & GOOGLE XYZ FORMULA)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Count: TOP 3 projects if Experience section is present. TOP 4 if no Experience.
Selection: Choose 3-4 projects from the profile that have the strongest skill overlap with the target JD.
Ordering: List projects in decreasing order of relevance to the target JD (most relevant project first).

Each project uses \resumeProjectHeading with EXACTLY 2 arguments:
  Arg1: \textbf{SHORTNAME -- Descriptive Title} $|$ \emph{Tech1, Tech2, Tech3} $|$ \href{<github_url>}{\underline{GitHub}} (and also $|$ \href{<live_demo_url>}{\underline{Live Demo}} if a deployment/demo link is present in the profile)
  Arg2: Year (e.g. "2025") or Month Year (e.g. "Jan 2025")

Title rules:
  • SHORTNAME = short memorable name, ALL CAPS or Title Case (e.g. ATLAS, NexTrade, PixelForge)
  • Tech stack: at most 4-5 technologies inside \emph{}. Abbreviate if needed.
  • You MUST include the clickable GitHub link (using \href) and if it is deployed, the Live Demo link too in Arg1, formatted exactly as shown above. Escape any special characters in the URLs (e.g. use \_ for underscores in the URL path) so LaTeX compiles flawlessly. Do NOT display raw URLs; always label them as underlined "GitHub" or "Live Demo".

Bullet rules:
  • EVERY project must have EXACTLY 3 bullet points. Count them. 1=fail. 2=fail. 4=fail.
  • Google XYZ Bullet Formula: Each bullet must follow the format: Accomplished [X], as measured by [Y], by doing [Z].
    - Example: Optimized model latency [X] by 40% [Y] through the implementation of TensorRT engine quantization [Z].
    - If no numeric metric is available in the profile, use a technical scale/performance indicator:
      Example: Architected a real-time message consumer [X] to handle asynchronous execution [Y] by deploying a Celery task queue with Redis [Z].
  • Banned Weak Verbs: Never begin a bullet with: helped, assisted, worked on, managed, led, built, created, developed, made, handled.
  • Replacement Strong Verbs: Always begin each bullet with: Architected, Engineered, Optimized, Spearheaded, Refactored, Designed, Deployed, Automated, Streamlined, Integrated.
  • Bullets must be short enough to not overflow the page width. If too long, split or compress.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 7 — TECHNICAL SKILLS BLOCK RULE (JD ALIGNMENT)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Use this exact structure (skip any group with no content from the profile):

\section{Technical Skills}
 \begin{itemize}[leftmargin=0.15in, label={}]
    \small{\item{
     \textbf{Languages}{: ...} \\
     \textbf{AI/ML \& Vision}{: ...} \\
     \textbf{Frameworks \& Libraries}{: ...} \\
     \textbf{Developer Tools}{: ...} \\
     \textbf{Concepts}{: ...}
    }}
 \end{itemize}

Include ONLY technologies explicitly mentioned in the candidate profile. Do not invent skills.
Prioritize listing skills in each category that are explicitly required or preferred by the target JD.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 8 — HONORS & AWARDS BLOCK RULE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ALLOWED — include these if present in the profile:
  ✓ Hackathon placement (e.g. "1st Place -- HackMIT 2025: Built an AI triage assistant...")
  ✓ Competitive programming stats (e.g. "LeetCode: Solved 235+ problems across DS&A topics")
  ✓ Research publications or patents

FORBIDDEN — NEVER include these, even if they appear in the profile:
  ✗ JEE Mains percentile or rank
  ✗ EAMCET rank
  ✗ Any college entrance exam score
  ✗ School board exam grades (10th/12th)

If no allowed achievements exist in the profile, SKIP the entire \section{Honors \& Awards} block.
Use \resumeSubItem for each achievement bullet.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 9 — TRUTH & HALLUCINATION RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Use ONLY facts, projects, roles, skills, and tools explicitly stated in the candidate profile.
• You may rephrase to use JD keywords (e.g. "built API" → "engineered RESTful backend"), but you must NEVER fabricate metrics, tools, companies, degrees, awards, or technologies.
• You may NOT add placeholder text like [Your Name] or TODO in the output.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 10 — OVERFULL HBOX PREVENTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• If any bullet or heading might overflow the line width, split it or shorten it.
• \resumeProjectHeading titles must be short enough to fit on one line.
• Never put a raw URL as visible text. Always wrap in \href{url}{\underline{Label}}.
"""

    # ── LEAN USER MESSAGE (only variable data) ──────────────────────────────
    user_message = fr"""Generate the resume now using the rules above.

CANDIDATE:
  Name (short preferred): {candidate_name}
  Phone: {candidate_phone}
  Email: {candidate_email}
  LinkedIn URL: {candidate_linkedin}
  GitHub URL: https://{candidate_github}

FULL CANDIDATE PROFILE:
{profile_summary}

TARGET JOB DESCRIPTION:
{json.dumps(parsed_jd, indent=2)}
{feedback_block}

Output the complete LaTeX document now. Start with \documentclass."""

    res_text = await safe_groq_completion(
        model=None,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_message}
        ],
        temperature=0.15
    )
    if "</think>" in res_text:
        res_text = res_text.split("</think>")[-1].strip()
    if res_text.startswith("```latex"):
        res_text = res_text[8:]
    elif res_text.startswith("```"):
        res_text = res_text[3:]
    if res_text.endswith("```"):
        res_text = res_text[:-3]
    return clean_latex_code(res_text.strip())


async def generate_prep_and_outreach(
    parsed_jd: dict, 
    profile_summary: str,
    candidate_name: str,
    candidate_phone: str,
    candidate_email: str,
    candidate_linkedin: str,
    candidate_github: str
) -> tuple:
    """Generates outreach messages and interview prep material using GPT-OSS 120b."""
    prep_prompt = f"""
Generate structured Interview Readiness material (using LaTeX format for compiling into a beautiful PDF) based on the candidate's real profile and the job description.

Candidate Details:
- Name: {candidate_name}
- Phone: {candidate_phone}
- Email: {candidate_email}
- LinkedIn: {candidate_linkedin}
- GitHub: {candidate_github}

Candidate Profile:
{profile_summary}

Job Description:
{json.dumps(parsed_jd, indent=2)}

Provide at least 3 behavioral questions using the STAR method (Situation, Task, Action, Result) based on the candidate's real projects, and a tailored Data Structures & Algorithms prep strategy.
Return ONLY valid, compile-ready LaTeX document. No markdown ticks, starting with \\documentclass and ending with \\end{{document}}.
"""
    outreach_prompt = f"""
Generate professional outreach messages for this job application.
You MUST use the candidate's actual details below to populate all signatures, sender names, and contact details. Do NOT output generic bracketed placeholders (like "[Your Name]", "[Your Email]", "[Your LinkedIn]", or "[My Github]"):
- Candidate Name: {candidate_name}
- Candidate Phone: {candidate_phone}
- Candidate Email: {candidate_email}
- Candidate LinkedIn: {candidate_linkedin}
- Candidate GitHub: {candidate_github}

Candidate Profile:
{profile_summary}

Job Description:
{json.dumps(parsed_jd, indent=2)}

Provide two outreach messages in Markdown:
1. LinkedIn connection message (under 300 chars, highly personalized, using candidate details)
2. Cold email to the hiring manager or recruiter (complete email body with greeting, candidate details, signature, and subject line).
"""
    # Run requests
    prep_text = await safe_groq_completion(
        model=FLAGSHIP_MODEL,
        messages=[{"role": "user", "content": prep_prompt}],
        temperature=0.2
    )
    if "</think>" in prep_text:
        prep_text = prep_text.split("</think>")[-1].strip()
    if prep_text.startswith("```latex"):
        prep_text = prep_text[8:]
    elif prep_text.startswith("```"):
        prep_text = prep_text[3:]
    if prep_text.endswith("```"):
        prep_text = prep_text[:-3]
        
    outreach_text = await safe_groq_completion(
        model=FLAGSHIP_MODEL,
        messages=[{"role": "user", "content": outreach_prompt}],
        temperature=0.2
    )
    if "</think>" in outreach_text:
        outreach_text = outreach_text.split("</think>")[-1].strip()
    return clean_latex_code(prep_text.strip()), outreach_text.strip()

async def get_quick_ats_score(latex_code: str, parsed_jd: dict) -> dict:
    """Fast, text-based evaluator that scores a resume against the JD using Groq llama-3.3-70b-versatile."""
    prompt = f"""
You are an ATS Scoring Assistant running llama-3.3-70b-versatile.
Your task is to grade the following LaTeX resume against the target Job Description on a scale from 0 to 100.
Identify matching skills, project alignment, and potential gaps.

Job Description:
{json.dumps(parsed_jd, indent=2)}

LaTeX Resume:
{latex_code}

Return ONLY a valid JSON object in this format:
{{
  "total_score": 85,
  "improvements": ["Highlight Supabase database experiences", "Explain role on the web frontend"]
}}
"""
    try:
        res = await safe_groq_only_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        if "</think>" in res:
            res = res.split("</think>")[-1].strip()
        if res.startswith("```json"):
            res = res[7:]
        if res.endswith("```"):
            res = res[:-3]
        return json.loads(res.strip())
    except Exception as e:
        print(f"Quick ATS scoring failed: {e}")
        return {"total_score": 75, "improvements": ["Improve formatting alignment"]}

async def process_job_application(user_id: str, jd_text: str) -> dict:
    """Executes the entire multi-agent pipeline for a job description."""
    update_status(user_id, "Initializing", "Retrieving historical career profile and mental models from Hindsight Cloud...")
    mem_mgr = HindsightMemoryManager()
    await mem_mgr.initialize_bank()
    
    # 1. Profile & Memory Agent (Hindsight recall + mental model)
    memories = await mem_mgr.recall_memories("What are my core skills, experience, and project highlights?", [f"userId:{user_id}"])
    profile_summary = "\n".join(memories)
    
    preferences = await mem_mgr.fetch_user_mental_model(user_id)
    profile_summary += f"\nCandidate Preferences & Observations:\n{preferences}"
    
    # Retrieve the full, uncompressed static onboarding document directly from Hindsight Cloud
    candidate_name = user_id.capitalize()
    candidate_phone = ""
    candidate_email = "candidate@gmail.com"
    candidate_linkedin = ""
    candidate_github = f"github.com/{user_id}"
    
    try:
        doc = await mem_mgr.client.documents.get_document(mem_mgr.bank_id, f"{user_id}_onboarding_static")
        if doc and hasattr(doc, "original_text") and doc.original_text:
            text = doc.original_text
            # Prepend the raw, uncompressed onboarding doc so the LLM has complete context (projects, experiences like ASKD, etc.)
            profile_summary = f"RAW CANDIDATE PROFILE DETAILS:\n{text}\n\n---\nAdditional Context:\n" + profile_summary
            
            # Parse contact details
            name_match = re.search(r"-\s*Name:\s*(.*)", text)
            email_match = re.search(r"-\s*Email:\s*(.*)", text)
            linkedin_match = re.search(r"-\s*LinkedIn:\s*(.*)", text)
            github_match = re.search(r"-\s*Username:\s*(.*)", text)
            phone_match = re.search(r"-\s*Phone:\s*(.*)", text) # Check if phone is in onboarding doc
            
            if name_match: candidate_name = name_match.group(1).strip()
            if email_match: candidate_email = email_match.group(1).strip()
            if linkedin_match: candidate_linkedin = linkedin_match.group(1).strip()
            if github_match: candidate_github = f"github.com/{github_match.group(1).strip()}"
            if phone_match: candidate_phone = phone_match.group(1).strip()
    except Exception as e:
        print(f"Failed to fetch uncompressed onboarding document: {e}")
        

        
    # 2. Job Parser Agent (gemma-4-31b-it)
    update_status(user_id, "Parsing JD", "Extracting key role specifications and skill set keywords...")
    parsed_jd = await parse_job_description(jd_text)
    company = parsed_jd.get("company", "Company").replace(" ", "")
    role = parsed_jd.get("role", "Role").replace(" ", "_").replace("/", "_")
    
    output_dir = f"output/{company}_{role}"
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(f"{output_dir}/cache", exist_ok=True)
    
    # 3. Eligibility Agent (gemma-4-31b-it)
    update_status(user_id, "Evaluating Eligibility", "Assessing candidate eligibility and experience alignment...")
    eligibility = await evaluate_eligibility(user_id, parsed_jd, profile_summary)
    
    # Dynamic logic update: startup or remote preference check
    is_remote = "remote" in parsed_jd.get("location", "").lower()
    is_startup = parsed_jd.get("experience_years", 0) <= 2
    
    # Update memory with behavior event
    apply_event = f"Applied to {parsed_jd.get('role')} at {parsed_jd.get('company')}. Remote: {is_remote}. Startup: {is_startup}."
    await mem_mgr.retain_memory(
        content=apply_event,
        doc_id=f"apply_{company}_{role}",
        context="user_application_activity",
        tags=[f"userId:{user_id}"]
    )
    
    # Trigger refresh of the user mental model
    await mem_mgr.refresh_user_mental_model(user_id)
    
    # Auto-reject total mismatches
    if eligibility.get("status") == "Reject" or eligibility.get("match_percentage", 100) < 30:
        update_status(user_id, "Rejected", f"Auto-rejected due to misalignment. Reason: {eligibility.get('reason')}")
        await mem_mgr.close()
        return {
            "status": "Rejected",
            "eligibility": eligibility,
            "parsed_jd": parsed_jd,
            "reason": eligibility.get("reason", "Auto-rejected due to misalignment.")
        }
        

        
    # Save cache
    with open(f"{output_dir}/cache/githubcache.json", "w") as f:
        json.dump({"profile": profile_summary}, f)
        
    # Run the hiring-agent ResumeEvaluator ONCE on candidate profile to select projects/best skills
    update_status(user_id, "Hiring Agent Profile Check", "Running hiring-agent on candidate profile to select best projects & highlight strengths...")
    profile_eval_data = evaluate_candidate_profile(profile_summary)
    
    # Build feedback suggestions from the hiring-agent's profile evaluation
    feedback = f"Hiring Agent profile suggestions: {', '.join(profile_eval_data.get('improvements', []))}. Deductions to address: {profile_eval_data.get('deductions_reasons', 'none')}"
        
    # 4. Resume Builder Agent (gemma-4-31b-it) + 5. ATS Optimization Agent (Fast Loop)
    score_threshold = 80
    max_loops = 3
    current_loop = 0
    ats_score = 0
    best_score_data = {}
    best_tex = ""
    
    while current_loop < max_loops:
        update_status(user_id, "ATS Optimization", f"Loop {current_loop + 1}/{max_loops} - Generating optimized LaTeX Resume...")
        print(f"ATS Optimization Loop {current_loop + 1}/{max_loops}...")
        latex_resume = await generate_resume_latex(
            parsed_jd=parsed_jd,
            profile_summary=profile_summary,
            feedback=feedback,
            candidate_name=candidate_name,
            candidate_phone=candidate_phone,
            candidate_email=candidate_email,
            candidate_linkedin=candidate_linkedin,
            candidate_github=candidate_github
        )
        
        # Save LaTeX source
        tex_path = f"{output_dir}/resume.tex"
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(latex_resume)
            
        update_status(user_id, "ATS Optimization", f"Loop {current_loop + 1}/{max_loops} - Compiling and validating LaTeX...")
        pdf_path = f"{output_dir}/resume.pdf"
        compile_success, compile_log = await compile_latex_to_pdf_with_log(latex_resume, pdf_path)
        
        if not compile_success:
            print(f"Loop {current_loop + 1} compilation failed. Error log:")
            # Extract log lines starting with !
            err_lines = [line for line in compile_log.splitlines() if line.strip().startswith("!")]
            err_summary = "\n".join(err_lines[:5]) if err_lines else compile_log[-300:]
            print(err_summary)
            feedback = f"CRITICAL: LaTeX compilation failed with the following errors:\n{err_summary}\n\nYou MUST fix these LaTeX compilation syntax errors in this loop! Make sure all special characters like &, %, _, $, # are escaped (e.g. use \\&, \\%, \\_, \\$, \\#) and all brackets match."
            current_loop += 1
            continue
            
        update_status(user_id, "ATS Optimization", f"Loop {current_loop + 1}/{max_loops} - Scoring resume via quick text evaluator...")
        # Get quick text-based ATS score
        quick_score_result = await get_quick_ats_score(latex_resume, parsed_jd)
        ats_score = quick_score_result.get("total_score", 0)
        print(f"Loop {current_loop + 1} Fast ATS Score: {ats_score}/100")
        
        # Format to match overall evaluation schema
        score_data = {
            "total_score": round(float(ats_score), 1),
            "max_score": 100,
            "strengths": profile_eval_data.get("strengths", ["Profile matches JD well"]),
            "improvements": quick_score_result.get("improvements", []),
            "bonus": profile_eval_data.get("bonus", 0),
            "deductions": profile_eval_data.get("deductions", 0),
            "deductions_reasons": profile_eval_data.get("deductions_reasons", ""),
            "raw_evaluation": quick_score_result
        }
        
        # Save results if better or first
        if ats_score > best_score_data.get("total_score", -1):
            best_score_data = score_data
            best_tex = latex_resume
            
        # If threshold reached, break
        if ats_score >= score_threshold:
            print("Fast ATS score threshold reached!")
            break
            
        # Construct feedback for next iteration
        feedback = f"ATS Score achieved: {ats_score}/100. Improvements needed: {', '.join(quick_score_result.get('improvements', []))}"
        current_loop += 1
        
    if not best_tex:
        print("Warning: All optimized LaTeX runs failed to compile. Falling back to raw generated version.")
        # Re-generate one final time with simple instructions for stability
        best_tex = await generate_resume_latex(
            parsed_jd=parsed_jd,
            profile_summary=profile_summary,
            feedback="CRITICAL: The previous versions failed to compile. Output a completely clean, valid, standard LaTeX document with no complex characters.",
            candidate_name=candidate_name,
            candidate_phone=candidate_phone,
            candidate_email=candidate_email,
            candidate_linkedin=candidate_linkedin,
            candidate_github=candidate_github
        )
        best_score_data = {
            "total_score": 60.0,
            "max_score": 100,
            "strengths": ["Basic profile fallback"],
            "improvements": ["Compile issues prevented optimization"],
            "bonus": 0,
            "deductions": 0,
            "deductions_reasons": "",
            "raw_evaluation": {}
        }
        
    # Finalize best resume files
    with open(f"{output_dir}/resume.tex", "w", encoding="utf-8") as f:
        f.write(best_tex)
    await compile_latex_to_pdf(best_tex, f"{output_dir}/resume.pdf")
    
    # Save resume cache
    with open(f"{output_dir}/cache/resumecache.json", "w") as f:
        json.dump(best_score_data, f)
        
    # Save ats_evaluation_summary.csv
    csv_path = f"{output_dir}/ats_evaluation_summary.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Metric", "Value"])
        writer.writerow(["ATS Score", best_score_data.get("total_score")])
        writer.writerow(["Max Possible", best_score_data.get("max_score")])
        writer.writerow(["Bonus Points", best_score_data.get("bonus")])
        writer.writerow(["Deductions", best_score_data.get("deductions")])
        writer.writerow(["Deductions Reasons", best_score_data.get("deductions_reasons")])
        writer.writerow(["Strengths", "; ".join(best_score_data.get("strengths", []))])
        writer.writerow(["Improvements Needed", "; ".join(best_score_data.get("improvements", []))])
        
    # 6. Interview Outreach Agent (gemma-4-31b-it)
    update_status(user_id, "Outreach & Prep", "Generating custom interview readiness PDF and outreach messages...")
    prep_latex, outreach_md = await generate_prep_and_outreach(
        parsed_jd=parsed_jd,
        profile_summary=profile_summary,
        candidate_name=candidate_name,
        candidate_phone=candidate_phone,
        candidate_email=candidate_email,
        candidate_linkedin=candidate_linkedin,
        candidate_github=candidate_github
    )
    
    # Save outreach markdown
    with open(f"{output_dir}/outreach_messages.md", "w", encoding="utf-8") as f:
        f.write(outreach_md)
        
    # Save and compile interview readiness PDF with log checking & retry
    prep_tex_path = f"{output_dir}/interview_readiness.tex"
    with open(prep_tex_path, "w", encoding="utf-8") as f:
        f.write(prep_latex)
        
    prep_pdf_path = f"{output_dir}/interview_readiness.pdf"
    prep_success, prep_log = await compile_latex_to_pdf_with_log(prep_latex, prep_pdf_path)
    if not prep_success:
        print("Interview readiness LaTeX failed to compile. Retrying once with error log...")
        err_lines = [line for line in prep_log.splitlines() if line.strip().startswith("!")]
        err_summary = "\n".join(err_lines[:5]) if err_lines else prep_log[-300:]
        
        # Retry once with error log feedback
        retry_prompt = f"""
The previous LaTeX document for Interview Readiness failed to compile with the following error:
{err_summary}

Please fix the LaTeX syntax error and output a corrected, compile-ready LaTeX document.
Return ONLY valid, compile-ready LaTeX, starting with \\documentclass and ending with \\end{{document}}.
"""
        try:
            prep_latex = await safe_groq_completion(
                model=None,
                messages=[
                    {"role": "user", "content": f"Previous prompt context: {profile_summary[:1000]}"},
                    {"role": "user", "content": retry_prompt}
                ],
                temperature=0.1
            )
            if "</think>" in prep_latex:
                prep_latex = prep_latex.split("</think>")[-1].strip()
            if prep_latex.startswith("```latex"):
                prep_latex = prep_latex[8:]
            elif prep_latex.startswith("```"):
                prep_latex = prep_latex[3:]
            if prep_latex.endswith("```"):
                prep_latex = prep_latex[:-3]
            prep_latex = clean_latex_code(prep_latex.strip())
            
            with open(prep_tex_path, "w", encoding="utf-8") as f:
                f.write(prep_latex)
            await compile_latex_to_pdf(prep_latex, prep_pdf_path)
        except Exception as e:
            print("Failed to self-correct interview readiness PDF:", e)
            
    # Save update event in memory
    final_event = f"Successfully generated resume and outreach materials for {company} {parsed_jd.get('role')}. ATS Score: {best_score_data.get('total_score')}."
    await mem_mgr.retain_memory(
        content=final_event,
        doc_id=f"success_{company}_{role}",
        context="pipeline_completion",
        tags=[f"userId:{user_id}"]
    )
    
    await mem_mgr.close()
    
    update_status(user_id, "Completed", f"Optimization complete! Final ATS Score: {best_score_data.get('total_score')}/100")
    return {
        "status": "Success",
        "parsed_jd": parsed_jd,
        "eligibility": eligibility,
        "ats_score": best_score_data.get("total_score"),
        "key_strengths": best_score_data.get("strengths", []),
        "improvements": best_score_data.get("improvements", []),
        "output_dir": output_dir
    }
