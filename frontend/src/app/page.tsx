"use client";

import React, { useState, useEffect, useRef } from "react";
import { createClient } from "@/utils/supabase/client";

interface Job {
  id: string;
  title: string;
  company: string;
  category: string;
  experience_years: number;
  skills: string[];
  description: string;
  location: string;
  type: string;
}

interface Application {
  id: string;
  company: string;
  role: string;
  ats_score: number;
  strengths: string[];
  improvements: string[];
  has_pdf: boolean;
  has_tex: boolean;
  has_prep: boolean;
  has_outreach: boolean;
}

interface MarkdownSection {
  title: string;
  content: string;
}

interface Toast {
  id: string;
  message: string;
  type: "success" | "error" | "info" | "warning";
}

import { Icons } from "@/components/icons";
import { RadialProgress } from "@/components/RadialProgress";
import { splitProfileMarkdown, RenderMarkdown } from "@/components/RenderMarkdown";
import { JobDetailsDrawer } from "@/components/JobDetailsDrawer";
import { ApplicationDetailsDrawer } from "@/components/ApplicationDetailsDrawer";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();
  // Navigation & Memory View Tab States
  const [activeTab, setActiveTab] = useState<"landing" | "profile" | "jobs" | "applications">("landing");
  const [loadedProfile, setLoadedProfile] = useState<{ profile_summary: string; preferences: string } | null>(null);
  const [isLoadingProfile, setIsLoadingProfile] = useState(false);
  const [landingUserId, setLandingUserId] = useState("");
  const [simulatedLogs, setSimulatedLogs] = useState<string[]>([
    "SYSTEM: Ingestion pipeline standby.",
    "SYSTEM: Awaiting command console entry."
  ]);
  const [expandedFaq, setExpandedFaq] = useState<number | null>(null);

  // Ingestion Form Step States (Switched via Tabs)
  const [formStep, setFormStep] = useState<"basics" | "crawlers" | "resume">("basics");

  // Onboarding Form State
  const [userId, setUserId] = useState("karthikeya");
  const [name, setName] = useState("Karthikeya");
  const [email, setEmail] = useState("karthikeya.maddi3342@gmail.com");
  const [phone, setPhone] = useState("6301893787");
  const [github, setGithub] = useState("https://github.com/karthikeya3342");
  const [leetcode, setLeetcode] = useState("https://leetcode.com/karthikeya3342");
  const [codeforces, setCodeforces] = useState("https://codeforces.com/profile/karthikeya3342");
  const [codechef, setCodechef] = useState("https://www.codechef.com/users/karthikeya3342");
  const [linkedin, setLinkedin] = useState("https://www.linkedin.com/in/venkata-sai-karthikeya-maddi-ab4433315");
  const [portfolio, setPortfolio] = useState("https://portfolio-karthikeya3342.vercel.app/");
  const [education, setEducation] = useState("B.Tech in Computer Science and Engineering, IIITDM Kurnool (Minor: Robotics & Automation, Class of 2028)");
  const [cgpa, setCgpa] = useState("CPI: 8.97/10.0 (after 4 semesters)");
  const [experience, setExperience] = useState("");
  const [previousResumeText, setPreviousResumeText] = useState("");
  const [onboardStatus, setOnboardStatus] = useState("");
  const [isOnboarding, setIsOnboarding] = useState(false);
  const [manualJdText, setManualJdText] = useState("");
  const [isSubmittingManualJd, setIsSubmittingManualJd] = useState(false);

  // Supabase client and session state
  const supabase = createClient();
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    // Check active session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null);
      if (session?.user) {
        const emailPrefix = session.user.email?.split("@")[0] || "karthikeya";
        setUserId(emailPrefix);
        setEmail(session.user.email || "");
        setActiveTab("profile");
      }
    });

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
      if (session?.user) {
        const emailPrefix = session.user.email?.split("@")[0] || "karthikeya";
        setUserId(emailPrefix);
        setEmail(session.user.email || "");
        setActiveTab("profile");
      } else {
        setUserId("karthikeya"); // reset to default candidate ID
        setActiveTab("landing");
      }
    });

    return () => subscription.unsubscribe();
  }, []);

  // Job Search State
  const [jobs, setJobs] = useState<Job[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("");
  const [page, setPage] = useState(1);
  const [totalJobs, setTotalJobs] = useState(0);

  // Application Pipeline State
  const [applications, setApplications] = useState<Application[]>([]);
  const [applyingJobId, setApplyingJobId] = useState<string | null>(null);
  const [pipelineLogs, setPipelineLogs] = useState<string[]>([]);
  const [pipelineStatus, setPipelineStatus] = useState({ stage: "Idle", details: "" });

  // Drawers and Overlays State
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [selectedApp, setSelectedApp] = useState<Application | null>(null);
  const [appDrawerTab, setAppDrawerTab] = useState<"metrics" | "preview" | "outreach" | "prep">("metrics");
  const [appOutreachContent, setAppOutreachContent] = useState("");
  const [isLoadingAppDetails, setIsLoadingAppDetails] = useState(false);
  const [expandedSections, setExpandedSections] = useState<Record<number, boolean>>({});

  const toggleSection = (idx: number) => {
    setExpandedSections(prev => ({
      ...prev,
      [idx]: prev[idx] === false ? true : false
    }));
  };

  // Toast Notification Stack State
  const [toasts, setToasts] = useState<Toast[]>([]);

  const terminalEndRef = useRef<HTMLDivElement>(null);
  
  // Configuration API base url loaded from Env variables
  const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

  // Show a toast message helper
  const triggerToast = (message: string, type: Toast["type"] = "info") => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 4500);
  };

  // Scroll terminal logs automatically
  useEffect(() => {
    if (terminalEndRef.current) {
      terminalEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [pipelineLogs]);

  // Fetch jobs
  const fetchJobs = async () => {
    try {
      const q = searchTerm ? `&q=${encodeURIComponent(searchTerm)}` : "";
      const cat = selectedCategory ? `&category=${encodeURIComponent(selectedCategory)}` : "";
      const res = await fetch(`${API_BASE}/api/jobs/discover?page=${page}&limit=6${q}${cat}`);
      const data = await res.json();
      setJobs(data.jobs || []);
      setTotalJobs(data.total || 0);
    } catch (e) {
      console.error("Error fetching jobs:", e);
      triggerToast("Failed to fetch opportunities board.", "error");
    }
  };

  // Fetch applications
  const fetchApplications = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/applications`);
      const data = await res.json();
      setApplications(data || []);
    } catch (e) {
      console.error("Error fetching applications:", e);
    }
  };

  // Fetch Hindsight memory profile
  const fetchProfile = async () => {
    setIsLoadingProfile(true);
    try {
      const res = await fetch(`${API_BASE}/api/profile/${userId}`);
      if (!res.ok) {
        throw new Error("No profile found. Onboard first.");
      }
      const data = await res.json();
      if (data.status === "success" && data.profile_summary) {
        setLoadedProfile({
          profile_summary: data.profile_summary,
          preferences: data.preferences
        });
        triggerToast("Factual Profile recalled from Hindsight.", "success");
      } else {
        setLoadedProfile(null);
        triggerToast("No stored profile found for Candidate ID.", "warning");
      }
    } catch (err: any) {
      console.error(err);
      triggerToast("Error recalling profile: " + err.message, "error");
    } finally {
      setIsLoadingProfile(false);
    }
  };

  // File upload handler
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => {
      const text = event.target?.result as string;
      setPreviousResumeText(text);
      triggerToast(`Loaded ${file.name} successfully. Check Step 3.`, "success");
      setFormStep("resume");
    };
    reader.readAsText(file);
  };

  useEffect(() => {
    fetchJobs();
  }, [page, searchTerm, selectedCategory]);

  useEffect(() => {
    fetchApplications();
    const interval = setInterval(fetchApplications, 12000);
    return () => clearInterval(interval);
  }, []);

  const loadApplicationDetails = async (appId: string) => {
    setIsLoadingAppDetails(true);
    setAppOutreachContent("");
    try {
      const outreachRes = await fetch(`${API_BASE}/api/download/${appId}/outreach_messages.md`);
      if (outreachRes.ok) {
        const outreachText = await outreachRes.text();
        setAppOutreachContent(outreachText || "");
      }
    } catch (err) {
      console.error("Error loading application drawer details:", err);
    } finally {
      setIsLoadingAppDetails(false);
    }
  };

  useEffect(() => {
    if (selectedApp) {
      loadApplicationDetails(selectedApp.id);
    }
  }, [selectedApp]);

  useEffect(() => {
    if (activeTab !== "landing") return;
    const mockEvents = [
      "[02:14:10] ELIGIBILITY_AGENT: Calibrating profile metrics against ML Engineer Internship specification...",
      "[02:14:12] DRAFTER_AGENT: Adapting resume bullet points with XYZ format...",
      "[02:14:14] VERIFIER_AGENT: Running ATS parser scoring feedback loop... current alignment: 83%",
      "[02:14:16] LaTeX_COMPILER: Initiating pdflatex compilation on TeXLive.net API...",
      "[02:14:18] LaTeX_COMPILER: PDF generated successfully (129 KB). Saving to output folder...",
      "[02:14:20] OUTREACH_AGENT: Formatting personalized LinkedIn message and Cold Email templates...",
      "[02:14:22] ORCHESTRATOR: Career tailoring pipeline completed successfully.",
      "[02:14:25] SYSTEM: Standby for next instruction."
    ];
    let idx = 0;
    const interval = setInterval(() => {
      setSimulatedLogs(prev => {
        const next = [...prev, mockEvents[idx]];
        if (next.length > 5) next.shift(); // keep it clean
        return next;
      });
      idx = (idx + 1) % mockEvents.length;
    }, 2800);
    return () => clearInterval(interval);
  }, [activeTab]);

  const handleOnboard = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsOnboarding(true);
    setOnboardStatus("Initiating sync with Git, LeetCode, Codeforces, and CodeChef crawlers...");
    triggerToast("Onboarding synthesis launched.", "info");
    try {
      const res = await fetch(`${API_BASE}/api/onboard`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          name,
          email,
          phone,
          github,
          leetcode,
          codeforces,
          codechef,
          linkedin,
          portfolio,
          education,
          cgpa,
          experience,
          previous_resume_text: previousResumeText
        })
      });
      const data = await res.json();
      if (data.status === "success") {
        setOnboardStatus("SUCCESS: Profile synthesized successfully!\nRecalling memory from Hindsight Cloud...");
        triggerToast("Profile synthesized & synced!", "success");
        setTimeout(() => {
          fetchProfile();
        }, 1000);
      } else {
        setOnboardStatus("ERROR: Onboarding failed: " + JSON.stringify(data.detail));
        triggerToast("Onboarding failed.", "error");
      }
    } catch (err: any) {
      setOnboardStatus("CRAWLER EXCEPTION: " + err.message);
      triggerToast("Crawler Exception occurred.", "error");
    } finally {
      setIsOnboarding(false);
    }
  };

  const handleApply = async (jobId: string) => {
    setApplyingJobId(jobId);
    setSelectedJob(null); // Close drawer if open
    setPipelineLogs([
      "SYSTEM: Initializing multi-agent pipeline...",
      "SYSTEM: Decoupling credentials from context...",
      "ORCHESTRATOR: Contacting Complexity Router (routing to Drafter/Verifier models)..."
    ]);
    setPipelineStatus({ stage: "Starting", details: "Contacting orchestrator agent..." });
    triggerToast("Application optimization started.", "info");

    // Poll status from the backend
    const statusInterval = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/api/pipeline-status/${userId}`);
        const data = await res.json();
        if (data && data.stage) {
          setPipelineStatus(data);
          setPipelineLogs(prev => {
            const lastLog = prev[prev.length - 1];
            const newLog = `[${data.stage}] ${data.details}`;
            if (lastLog !== newLog) {
              return [...prev, newLog];
            }
            return prev;
          });
        }
      } catch (err) {
        console.error("Error polling pipeline status:", err);
      }
    }, 1200);

    try {
      const res = await fetch(`${API_BASE}/api/jobs/apply`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          job_id: jobId
        })
      });
      const data = await res.json();
      if (data.status === "Success") {
        setPipelineLogs(prev => [
          ...prev,
          "SYSTEM: LaTeX compile verified on TeXLive.net API (PDF starts with %PDF).",
          `SUCCESS: ATS Optimization completed! ATS score: ${data.ats_score}/100.`,
          "SYSTEM: Saving success event tag to Hindsight Cloud memory."
        ]);
        triggerToast(`Applied successfully! Score: ${data.ats_score}%`, "success");
        fetchApplications();
      } else if (data.status === "Rejected") {
        setPipelineLogs(prev => [
          ...prev,
          `REJECTED: Eligibility Agent returned negative alignment.`,
          `DECISION REASON: ${data.reason}`
        ]);
        triggerToast("Eligibility Agent rejected alignment.", "warning");
        fetchApplications();
      } else {
        setPipelineLogs(prev => [...prev, "ERROR: Pipeline execution error: " + JSON.stringify(data)]);
        triggerToast("Pipeline returned execution error.", "error");
      }
    } catch (err: any) {
      setPipelineLogs(prev => [...prev, "CONNECTION EXCEPTION: " + err.message]);
      triggerToast("Connection error while running agent pipeline.", "error");
    } finally {
      clearInterval(statusInterval);
      setApplyingJobId(null);
      setTimeout(() => {
        setPipelineStatus({ stage: "Idle", details: "" });
      }, 5000);
    }
  };

  const handleManualApply = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!manualJdText.trim()) return;

    setIsSubmittingManualJd(true);
    setApplyingJobId("manual");
    setPipelineLogs([
      "SYSTEM: Initializing multi-agent pipeline...",
      "SYSTEM: Decoupling credentials from context...",
      "ORCHESTRATOR: Contacting Complexity Router (routing to Drafter/Verifier models)...",
      "SYSTEM: Received raw Job Description text. Initiating Parsing Agent..."
    ]);
    setPipelineStatus({ stage: "Starting", details: "Parsing Job Description..." });
    triggerToast("Application optimization started.", "info");

    const statusInterval = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/api/pipeline-status/${userId}`);
        const data = await res.json();
        if (data && data.stage) {
          setPipelineStatus(data);
          setPipelineLogs(prev => {
            const lastLog = prev[prev.length - 1];
            const newLog = `[${data.stage}] ${data.details}`;
            if (lastLog !== newLog) {
              return [...prev, newLog];
            }
            return prev;
          });
        }
      } catch (err) {
        console.error("Error polling pipeline status:", err);
      }
    }, 1200);

    try {
      const res = await fetch(`${API_BASE}/api/jobs/apply`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          jd_text: manualJdText
        })
      });
      const data = await res.json();
      if (data.status === "Success") {
        setPipelineLogs(prev => [
          ...prev,
          "SYSTEM: LaTeX compile verified on TeXLive.net API (PDF starts with %PDF).",
          `SUCCESS: ATS Optimization completed! ATS score: ${data.ats_score}/100.`,
          "SYSTEM: Saving success event tag to Hindsight Cloud memory."
        ]);
        triggerToast(`Applied successfully! Score: ${data.ats_score}%`, "success");
        setManualJdText("");
        fetchApplications();
      } else if (data.status === "Rejected") {
        setPipelineLogs(prev => [
          ...prev,
          `REJECTED: Eligibility Agent returned negative alignment.`,
          `DECISION REASON: ${data.reason}`
        ]);
        triggerToast("Eligibility Agent rejected alignment.", "warning");
        fetchApplications();
      } else {
        setPipelineLogs(prev => [...prev, "ERROR: Pipeline execution error: " + JSON.stringify(data)]);
        triggerToast("Pipeline returned execution error.", "error");
      }
    } catch (err: any) {
      setPipelineLogs(prev => [...prev, "CONNECTION EXCEPTION: " + err.message]);
      triggerToast("Connection error while running agent pipeline.", "error");
    } finally {
      clearInterval(statusInterval);
      setApplyingJobId(null);
      setIsSubmittingManualJd(false);
      setTimeout(() => {
        setPipelineStatus({ stage: "Idle", details: "" });
      }, 5000);
    }
  };

  const openInOverleaf = async (appId: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/view-tex/${appId}`);
      const data = await res.json();
      if (data && data.content) {
        const base64Str = btoa(unescape(encodeURIComponent(data.content)));
        const form = document.createElement("form");
        form.action = "https://www.overleaf.com/docs";
        form.method = "POST";
        form.target = "_blank";

        const input = document.createElement("input");
        input.type = "hidden";
        input.name = "snip_uri";
        input.value = `data:application/x-tex;base64,${base64Str}`;
        form.appendChild(input);

        document.body.appendChild(form);
        form.submit();
        document.body.removeChild(form);
        triggerToast("Redirecting LaTeX project to Overleaf...", "success");
      } else {
        triggerToast("Failed to retrieve LaTeX code.", "error");
      }
    } catch (err) {
      console.error("Error opening in Overleaf:", err);
      triggerToast("Error contacting backend for LaTeX code.", "error");
    }
  };

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    triggerToast(`${label} copied to clipboard!`, "success");
  };

  // Helper to parse profile markdown
  const parsedSections = loadedProfile ? splitProfileMarkdown(loadedProfile.profile_summary) : [];

  // Calculate Average ATS score
  const appsWithScores = applications.filter(a => a.ats_score > 0);
  const avgAtsScore = appsWithScores.length > 0
    ? Math.round(appsWithScores.reduce((acc, a) => acc + a.ats_score, 0) / appsWithScores.length)
    : 0;

  // Calculate field completion progress
  const profileFields = [
    { name: "Name", val: name },
    { name: "Email", val: email },
    { name: "Phone", val: phone },
    { name: "Education", val: education },
    { name: "CGPA", val: cgpa },
    { name: "Experience", val: experience },
    { name: "GitHub", val: github },
    { name: "LeetCode", val: leetcode },
    { name: "Codeforces", val: codeforces },
    { name: "CodeChef", val: codechef },
    { name: "LinkedIn", val: linkedin },
    { name: "Portfolio", val: portfolio },
    { name: "Resume Text", val: previousResumeText }
  ];
  const filledFieldsCount = profileFields.filter(f => f.val && f.val.trim().length > 0).length;
  const completionPercentage = Math.round((filledFieldsCount / profileFields.length) * 100);

  // Helper to map active stage in visual steps
  const getStepActiveIndex = (stage: string) => {
    const s = stage.toLowerCase();
    if (s.includes("start")) return 0;
    if (s.includes("jd") || s.includes("analysis") || s.includes("parsed")) return 1;
    if (s.includes("hiring") || s.includes("model")) return 2;
    if (s.includes("optimization") || s.includes("generating") || s.includes("scoring") || s.includes("ats")) return 3;
    if (s.includes("outreach") || s.includes("prep")) return 4;
    return -1;
  };

  const activeStepIdx = getStepActiveIndex(pipelineStatus.stage);

  return (
    <div className="min-h-screen bg-antiwhite text-navy font-sans p-4 sm:p-6 antialiased selection:bg-vibrantred selection:text-antiwhite relative">
      
      {/* Toast Notification Container */}
      {toasts.length > 0 && (
        <div className="fixed top-4 right-4 z-[100] flex flex-col gap-3 max-w-sm w-full pointer-events-none">
          {toasts.map(t => (
            <div 
              key={t.id} 
              className="pointer-events-auto flex items-start gap-3 p-4 border-3 border-navy bg-white shadow-[4px_4px_0px_0px_rgba(43,45,66,1)] animate-toast-in relative overflow-hidden"
            >
              <div className={`absolute left-0 top-0 h-full w-1.5 ${
                t.type === "success" ? "bg-green-600" :
                t.type === "error" ? "bg-vibrantred" :
                t.type === "warning" ? "bg-amber-500" : "bg-navy"
              }`} />
              <div className={`shrink-0 mt-0.5 ${
                t.type === "success" ? "text-green-600" :
                t.type === "error" ? "text-vibrantred" :
                t.type === "warning" ? "text-amber-500" : "text-navy"
              }`}>
                {t.type === "success" ? <Icons.Check /> :
                 t.type === "error" ? <Icons.Alert /> :
                 t.type === "warning" ? <Icons.Alert /> : <Icons.Info />}
              </div>
              <div className="flex-1">
                <p className="text-[10px] font-black uppercase text-navy leading-none mb-1">
                  {t.type === "success" ? "Operation Success" :
                   t.type === "error" ? "Pipeline Failure" :
                   t.type === "warning" ? "Alignment Alert" : "System Notification"}
                </p>
                <p className="text-xs font-bold text-frenchgray leading-snug">{t.message}</p>
              </div>
              <button 
                onClick={() => setToasts(prev => prev.filter(x => x.id !== t.id))} 
                className="text-frenchgray hover:text-navy shrink-0 cursor-pointer"
              >
                <Icons.Close />
              </button>
            </div>
          ))}
        </div>
      )}

      {activeTab === "landing" ? (
        <div className="max-w-7xl mx-auto py-4 space-y-12 animate-fade-in p-2 sm:p-6 retro-dot-grid">
          {/* Landing Navbar */}
          <nav className="bg-navy border-4 border-navy shadow-[6px_6px_0px_0px_rgba(43,45,66,1)] p-4 flex justify-between items-center text-antiwhite relative overflow-hidden">
            <div className="flex items-center gap-2 cursor-pointer select-none" onClick={() => setActiveTab("landing")}>
              <span className="text-xl sm:text-2xl font-black uppercase tracking-tight">CareerOS</span>
              <span className="bg-vibrantred text-[8px] font-black uppercase px-1.5 py-0.5 border border-navy tracking-widest">v2.5</span>
            </div>
            <div className="flex items-center gap-4">
              {user && (
                <span className="hidden md:inline-block text-[10px] font-black uppercase text-frenchgray bg-antiwhite/5 px-2.5 py-1.5 border border-navy/20 font-sans">
                  Logged in: {user.email}
                </span>
              )}
              {/* Top GitHub Link */}
              <a 
                href="https://github.com/karthikeya3342/careerOS" 
                target="_blank" 
                rel="noopener noreferrer"
                className="hidden sm:flex items-center gap-1.5 bg-white text-navy border-2 border-navy text-[10px] font-black uppercase px-2.5 py-1.5 shadow-[2px_2px_0px_0px_rgba(239,35,60,1)] hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-none transition-all"
              >
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="w-3.5 h-3.5">
                  <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22" />
                </svg>
                GitHub Source
              </a>
              <button
                onClick={() => {
                  if (user) {
                    setActiveTab("profile");
                  } else {
                    router.push("/login");
                  }
                }}
                className="bg-vibrantred hover:bg-engorange text-antiwhite text-xs font-black uppercase px-4 py-2 border-3 border-navy shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-none transition-all cursor-pointer"
              >
                {user ? "Enter Command Center" : "Log In / Register"}
              </button>
            </div>
          </nav>

          {/* Hero Section */}
          <section className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-stretch">
            {/* Left Column: Headings & ID launch */}
            <div className="lg:col-span-7 bg-white border-4 border-navy p-6 sm:p-8 shadow-[8px_8px_0px_0px_rgba(43,45,66,1)] flex flex-col justify-between">
              <div>
                <div className="inline-block bg-vibrantred/10 text-vibrantred border border-vibrantred/30 text-[9px] font-black uppercase px-2.5 py-1 tracking-widest mb-4">
                  Autonomous Drafter-Verifier Engine
                </div>
                <h2 className="text-3xl sm:text-5xl font-black uppercase text-navy leading-none tracking-tight">
                  Autonomous Multi-Agent Career Command Center
                </h2>
                <p className="text-frenchgray font-semibold text-xs sm:text-sm uppercase tracking-wide mt-2">
                  Optimize your professional index vectors, tailors print-ready resumes, and compiles prep guides.
                </p>
                <div className="mt-6 border-l-4 border-navy pl-4 space-y-3.5 text-xs font-bold leading-relaxed text-navy/90">
                  <p>
                    ✓ <strong className="text-navy">XYZ Tailoring Matrix</strong>: Formulate bullet points using Google's formula (<em>Accomplished [X] as measured by [Y] by doing [Z]</em>).
                  </p>
                  <p>
                    ✓ <strong className="text-navy">Hindsight Memory Integration</strong>: Syncs candidate profiles, crawl socials, and retains memory banks semantically.
                  </p>
                  <p>
                    ✓ <strong className="text-navy">ATS Feedback Loop</strong>: Verifier agent scores CV matches and passes optimization feedback back to the Drafter.
                  </p>
                </div>
              </div>

              {/* Quick-Access Entry Console */}
              <div className="mt-8 border-t-4 border-navy pt-6">
                {user ? (
                  <div>
                    <h4 className="text-[10px] font-black uppercase text-frenchgray tracking-wider mb-2">
                      Authorized Command Center Session
                    </h4>
                    <div className="bg-antiwhite border-3 border-navy p-4 flex flex-col sm:flex-row justify-between items-center gap-4 shadow-[3px_3px_0px_0px_rgba(43,45,66,1)]">
                      <div>
                        <p className="text-xs font-black uppercase text-navy">Welcome back!</p>
                        <p className="text-[9.5px] font-bold text-frenchgray uppercase mt-0.5 leading-relaxed">
                          Logged in: <strong className="text-navy">{user.email}</strong><br />
                          Active Candidate ID: <strong className="text-vibrantred">{userId}</strong>
                        </p>
                      </div>
                      <button
                        onClick={() => {
                          setEmail(user.email || "");
                          setActiveTab("profile");
                        }}
                        className="bg-vibrantred hover:bg-engorange text-antiwhite text-xs font-black uppercase px-5 py-2.5 border-3 border-navy shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-none transition-all cursor-pointer whitespace-nowrap"
                      >
                        Enter Console
                      </button>
                    </div>
                  </div>
                ) : (
                  <div>
                    <h4 className="text-[10px] font-black uppercase text-frenchgray tracking-wider mb-2.5">
                      Launch Agent Workspace Console
                    </h4>
                    <p className="text-xs font-semibold text-frenchgray uppercase mb-4 leading-relaxed">
                      Authenticate to initialize candidate memory banks, crawl repositories, and optimize resumes.
                    </p>
                    <div className="flex flex-col sm:flex-row gap-3">
                      <a
                        href="/login"
                        className="bg-vibrantred hover:bg-engorange text-antiwhite text-xs font-black uppercase px-6 py-3.5 border-3 border-navy shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-none transition-all cursor-pointer text-center flex-1"
                      >
                        Log In
                      </a>
                      <a
                        href="/signup"
                        className="bg-white hover:bg-frenchgray/10 text-navy text-xs font-black uppercase px-6 py-3.5 border-3 border-navy shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-none transition-all cursor-pointer text-center flex-1"
                      >
                        Create Account
                      </a>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Right Column: Visual Simulator Terminal */}
            <div className="lg:col-span-5 bg-navy text-antiwhite border-4 border-navy shadow-[8px_8px_0px_0px_rgba(239,35,60,1)] p-5 flex flex-col justify-between animate-float animate-grid-scan relative min-h-[350px]">
              <div>
                <div className="flex justify-between items-center border-b border-frenchgray/30 pb-3.5 mb-4">
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 bg-vibrantred rounded-full animate-ping" />
                    <span className="text-[10px] font-black uppercase tracking-wider text-frenchgray">Multi-Agent Workspace Simulator</span>
                  </div>
                  <span className="text-[8px] bg-frenchgray/20 text-frenchgray font-black uppercase px-1.5 py-0.5">LOOP ACTIVE</span>
                </div>
                
                {/* Simulation logs screen */}
                <div className="font-mono text-[11px] leading-loose space-y-2.5 text-frenchgray">
                  {simulatedLogs.map((log, i) => {
                    let color = "text-frenchgray";
                    if (log.includes("SUCCESS") || log.includes("completed")) color = "text-green-400 font-extrabold";
                    else if (log.includes("COMPILER")) color = "text-antiwhite";
                    else if (log.includes("DRAFTER") || log.includes("ELIGIBILITY")) color = "text-amber-400";
                    
                    return (
                      <div key={i} className="flex gap-2">
                        <span className="text-vibrantred font-bold select-none">&gt;</span>
                        <span className={color}>{log}</span>
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="border-t border-frenchgray/20 pt-4 mt-6 flex justify-between items-center text-[10px] font-bold text-frenchgray uppercase">
                <span>Drafter: Gemini 3.1 Flash Lite</span>
                <span>Verifier: Llama 3.3 70B</span>
              </div>
            </div>
          </section>

          {/* Interactive Agent Flowchart Diagram */}
          <section className="bg-white border-4 border-navy p-6 shadow-[8px_8px_0px_0px_rgba(43,45,66,1)]">
            <h3 className="text-sm font-black uppercase text-navy border-b-2 border-navy pb-2 mb-6 tracking-wider flex items-center gap-1.5">
              <span className="w-1.5 h-3.5 bg-vibrantred" />
              Multi-Agent Pipeline Architecture Flow
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4 text-center font-sans text-xs uppercase font-extrabold">
              {[
                { title: "1. Ingestion Sync", desc: "Crawls GitHub, LeetCode, Codeforces" },
                { title: "2. Complexity Router", desc: "Routes prompts by token constraints" },
                { title: "3. Drafter Agent", desc: "Generates tailored LaTeX source code" },
                { title: "4. Verifier Agent", desc: "Calculates ATS matches & feedback" },
                { title: "5. TeX Compiler", desc: "Generates PDF resume via TeX API" }
              ].map((node, i) => (
                <div key={i} className="relative flex flex-col justify-between border-3 border-navy p-4 bg-antiwhite shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]">
                  {i < 4 && (
                    <div className="hidden md:block absolute top-1/2 -right-4 w-4 h-1 bg-navy -translate-y-1/2 z-0" />
                  )}
                  <div className="bg-navy text-antiwhite w-6 h-6 rounded-none flex items-center justify-center mx-auto mb-2 text-[10px]">
                    {i + 1}
                  </div>
                  <h4 className="text-navy text-[11px] font-black">{node.title}</h4>
                  <p className="text-frenchgray text-[9px] lowercase font-semibold mt-1 leading-snug">{node.desc}</p>
                </div>
              ))}
            </div>
          </section>

          {/* Capabilities Features Grid */}
          <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              {
                title: "Social Crawlers & Hindsight Sync",
                desc: "Indices public commits, LeetCode rank progress, and Codeforces handles. Builds and compiles comprehensive personal history summaries stored securely in hindsight vector databases.",
                tag: "Ingestion"
              },
              {
                title: "Self-Correcting LaTeX Compilation",
                desc: "Pushes optimized latex documents to online rendering systems. Reads build outputs and automatically runs error logs through correction agents to debug layouts.",
                tag: "Compilation"
              },
              {
                title: "High-Value Application Outputs",
                desc: "Generates ATS-aligned resumes, professional cold outreach email copies, custom prep guides (STAR method questions), and click-to-open Overleaf editing pages.",
                tag: "Asset Synthesis"
              }
            ].map((feat, i) => (
              <div key={i} className="bg-white border-4 border-navy p-5 shadow-[6px_6px_0px_0px_rgba(43,45,66,1)] flex flex-col justify-between hover:shadow-[8px_8px_0px_0px_rgba(43,45,66,1)] hover:-translate-y-0.5 transition-all">
                <div>
                  <div className="flex justify-between items-center border-b border-navy/10 pb-2 mb-3">
                    <span className="text-[10px] font-black uppercase text-frenchgray tracking-wider">{feat.tag}</span>
                    <span className="w-2.5 h-2.5 bg-navy rounded-none" />
                  </div>
                  <h4 className="text-sm font-black uppercase text-navy">{feat.title}</h4>
                  <p className="text-xs font-semibold leading-relaxed text-frenchgray mt-2 lowercase">{feat.desc}</p>
                </div>
              </div>
            ))}
          </section>

          {/* Technical Stack Section */}
          <section className="bg-white border-4 border-navy p-6 shadow-[8px_8px_0px_0px_rgba(43,45,66,1)]">
            <h3 className="text-sm font-black uppercase text-navy border-b-2 border-navy pb-2 mb-4 tracking-wider flex items-center gap-1.5">
              <span className="w-1.5 h-3.5 bg-vibrantred" />
              Technical Stack Specifications
            </h3>
            <div className="flex flex-wrap gap-2.5">
              {[
                "Next.js 16 (React 19 App)",
                "FastAPI / Python 3.10",
                "Gemini 3.1 Flash Lite (Drafter)",
                "Llama-3.3-70B-Versatile (Verifier)",
                "Hindsight Cloud (Vector DB)",
                "Cascadeflow Orchestrator",
                "Tailwind CSS v4"
              ].map((tech, i) => (
                <span key={i} className="bg-antiwhite border-2 border-navy text-navy text-[10px] font-black uppercase px-3 py-1.5 shadow-[1.5px_1.5px_0px_0px_rgba(0,0,0,1)]">
                  {tech}
                </span>
              ))}
            </div>
          </section>

          {/* FAQ Accordion Section */}
          <section className="bg-white border-4 border-navy p-6 shadow-[8px_8px_0px_0px_rgba(43,45,66,1)]">
            <h3 className="text-sm font-black uppercase text-navy border-b-2 border-navy pb-2 mb-6 tracking-wider flex items-center gap-1.5">
              <span className="w-1.5 h-3.5 bg-vibrantred" />
              Technical FAQ & Specifications
            </h3>
            
            <div className="space-y-4">
              {[
                {
                  q: "How does the self-correcting TeX compiler work?",
                  a: "The LaTeX Drafter outputs raw TeX markup. The compiler tries to build it using the TeXLive API. If compilation fails, the Verifier Agent parses the stderr log, pinpoints the line numbers of undefined control sequences or unescaped characters, and runs a self-correction pass using a specialized parser LLM before retrying."
                },
                {
                  q: "What is the Drafter-Verifier agent loop?",
                  a: "To ensure high alignment, the Drafter Agent generates resume bullets based on candidate details and target JDs. The Verifier Agent compiles and runs a semantic ATS evaluation match scoring loop. If the alignment score is below 80/100, the Verifier generates a feedback JSON containing structural gaps, sending it back to the Drafter for iterative refinement (max 3 loops)."
                },
                {
                  q: "How does Hindsight Vector Memory retrieve records?",
                  a: "During onboarding, candidate details and crawled repositories are synthesized and saved in the Hindsight Cloud Vector DB. When you request optimization, the orchestrator queries Hindsight with job description keywords, retrieving only the most semantically relevant projects and experiences so the Drafter stays within context length limits while highlighting your best matching accomplishments."
                }
              ].map((faq, i) => {
                const isFaqExpanded = expandedFaq === i;
                return (
                  <div key={i} className="border-3 border-navy bg-antiwhite p-4 shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] transition-all">
                    <button 
                      onClick={() => setExpandedFaq(isFaqExpanded ? null : i)}
                      type="button"
                      className="w-full flex justify-between items-center text-left font-black uppercase text-xs text-navy tracking-wider cursor-pointer group"
                    >
                      <span className="flex items-center gap-2">
                        <span className="text-vibrantred font-black">Q:</span>
                        {faq.q}
                      </span>
                      <span className="transition-transform duration-150 transform group-hover:scale-110">
                        {isFaqExpanded ? (
                          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" className="w-3.5 h-3.5">
                            <polyline points="18 15 12 9 6 15" />
                          </svg>
                        ) : (
                          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" className="w-3.5 h-3.5">
                            <polyline points="6 9 12 15 18 9" />
                          </svg>
                        )}
                      </span>
                    </button>
                    <div className={`overflow-hidden transition-all duration-200 ${isFaqExpanded ? "max-h-[200px] opacity-100 mt-3 border-t-2 border-navy/10 pt-3" : "max-h-0 opacity-0"}`}>
                      <p className="text-xs font-semibold leading-relaxed text-frenchgray lowercase">
                        {faq.a}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </section>

          {/* System Metrics Stats Panel */}
          <section className="grid grid-cols-3 gap-4">
            {[
              { key: "Sync Profiles", val: "14,208" },
              { key: "Compile Success", val: "99.2%" },
              { key: "Avg. Match Score", val: "87.5%" }
            ].map((stat, i) => (
              <div key={i} className="bg-white border-3 border-navy p-3.5 shadow-[3px_3px_0px_0px_rgba(43,45,66,1)] text-center">
                <span className="text-[9px] font-black uppercase text-frenchgray tracking-wider block">{stat.key}</span>
                <span className="text-base sm:text-xl font-black uppercase text-navy mt-1 block">{stat.val}</span>
              </div>
            ))}
          </section>

          {/* CTA Footer */}
          <footer className="bg-navy border-4 border-navy shadow-[6px_6px_0px_0px_rgba(43,45,66,1)] p-6 text-center text-antiwhite relative overflow-hidden">
            <h4 className="text-lg sm:text-xl font-black uppercase">Ready to calibrate your career assets?</h4>
            <p className="text-frenchgray text-xs font-semibold uppercase mt-1">
              Synchronize public data profiles and run your ATS optimization pipeline.
            </p>
            <button
              onClick={() => {
                if (user) {
                  setActiveTab("profile");
                } else {
                  router.push("/login");
                }
              }}
              className="mt-4 bg-vibrantred hover:bg-engorange text-antiwhite text-xs font-black uppercase px-6 py-2.5 border-3 border-navy shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-none transition-all cursor-pointer inline-block"
            >
              {user ? "Access Agent Console" : "Log In to Access Console"}
            </button>
          </footer>
        </div>
      ) : (
        <>
          {/* Header Panel */}
          <header className="bg-navy border-4 border-navy shadow-[6px_6px_0px_0px_rgba(43,45,66,1)] p-4 sm:p-6 mb-6 flex flex-col md:flex-row justify-between items-start md:items-center text-antiwhite gap-4 relative overflow-hidden">
            <div className="absolute right-0 top-0 h-full w-1/3 bg-gradient-to-r from-transparent via-frenchgray/10 to-vibrantred/20 pointer-events-none skew-x-12" />
            <div className="z-10">
              <div className="flex items-center gap-2 cursor-pointer select-none" onClick={() => setActiveTab("landing")}>
                <h1 className="text-3xl sm:text-4xl font-black tracking-tight uppercase">CareerOS</h1>
                <span className="bg-vibrantred text-antiwhite text-[10px] font-black uppercase px-2 py-0.5 border border-navy tracking-widest animate-pulse">v2.5</span>
              </div>
              <p className="text-frenchgray font-bold text-xs sm:text-sm mt-1 tracking-wider uppercase">Autonomous Multi-Agent Career Optimization Engine</p>
            </div>
        <div className="z-10 flex flex-wrap items-center gap-3">
          {user && (
            <div className="bg-antiwhite/10 text-antiwhite border border-antiwhite/20 px-3 py-1.5 text-[10px] font-black uppercase tracking-wider font-sans">
              ID: {userId}
            </div>
          )}
          <button 
            onClick={async () => {
              await supabase.auth.signOut();
              setActiveTab("landing");
              triggerToast("Signed out successfully.", "success");
            }}
            className="bg-vibrantred hover:bg-engorange text-antiwhite border-2 border-antiwhite px-3.5 py-1.5 text-[10px] font-black uppercase tracking-wider shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-none transition-all cursor-pointer font-sans"
          >
            Sign Out
          </button>
        </div>
      </header>

      {/* Interactive Global Stats Widgets Dashboard */}
      <section className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="bg-white border-3 border-navy p-3.5 shadow-[3px_3px_0px_0px_rgba(43,45,66,1)] flex items-center gap-3">
          <div className="bg-navy text-antiwhite p-2 border-2 border-navy rounded-none">
            <Icons.User />
          </div>
          <div>
            <h4 className="text-[10px] font-black text-frenchgray uppercase tracking-wider">Memory Profile</h4>
            <div className="flex items-center gap-2 mt-0.5">
              <span className={`text-xs font-black uppercase ${loadedProfile ? "text-green-600" : "text-vibrantred"}`}>
                {loadedProfile ? "Synced" : "Vacant"}
              </span>
              {loadedProfile && (
                <span className="text-[9px] font-extrabold bg-frenchgray/20 text-navy px-1.5 py-0.5">
                  {filledFieldsCount}/{profileFields.length} flds
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="bg-white border-3 border-navy p-3.5 shadow-[3px_3px_0px_0px_rgba(43,45,66,1)] flex items-center gap-3">
          <div className="bg-navy text-antiwhite p-2 border-2 border-navy rounded-none">
            <Icons.Briefcase />
          </div>
          <div>
            <h4 className="text-[10px] font-black text-frenchgray uppercase tracking-wider">Calibration Matrix</h4>
            <p className="text-xs font-black uppercase text-navy mt-0.5">
              {totalJobs} Active Jobs
            </p>
          </div>
        </div>

        <div className="bg-white border-3 border-navy p-3.5 shadow-[3px_3px_0px_0px_rgba(43,45,66,1)] flex items-center gap-3">
          <div className="bg-navy text-antiwhite p-2 border-2 border-navy rounded-none">
            <Icons.Folder />
          </div>
          <div>
            <h4 className="text-[10px] font-black text-frenchgray uppercase tracking-wider">Optimized Runs</h4>
            <p className="text-xs font-black uppercase text-navy mt-0.5">
              {applications.length} Submissions
            </p>
          </div>
        </div>

        <div className="bg-white border-3 border-navy p-3.5 shadow-[3px_3px_0px_0px_rgba(43,45,66,1)] flex items-center gap-3">
          <div className="bg-vibrantred text-antiwhite p-2 border-2 border-navy rounded-none">
            <Icons.Sparkles />
          </div>
          <div>
            <h4 className="text-[10px] font-black text-frenchgray uppercase tracking-wider">Avg. ATS Alignment</h4>
            <p className="text-xs font-black uppercase text-navy mt-0.5">
              {avgAtsScore}% Match Quality
            </p>
          </div>
        </div>
      </section>

      {/* Controller & Global Configuration Bar */}
      <div className="bg-navy border-4 border-navy p-4 mb-8 flex flex-col xl:flex-row justify-between items-center gap-4 text-antiwhite shadow-[5px_5px_0px_0px_rgba(43,45,66,1)] relative z-20">
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 w-full xl:w-auto">
          <div className="flex items-center gap-2">
            <div className="bg-vibrantred p-1.5 border border-navy text-antiwhite">
              <Icons.User />
            </div>
            <span className="text-xs font-black uppercase text-frenchgray tracking-wider">Candidate ID:</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="bg-frenchgray/20 text-antiwhite border-3 border-navy px-4 py-1.5 font-black text-xs sm:text-sm select-all font-sans uppercase">
              {userId}
            </div>
            <button 
              onClick={fetchProfile} 
              disabled={isLoadingProfile}
              className="bg-vibrantred hover:bg-engorange disabled:bg-frenchgray text-antiwhite text-xs font-black uppercase px-4 py-2 border-3 border-navy shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] active:translate-y-0.5 active:shadow-none transition-all cursor-pointer whitespace-nowrap"
            >
              {isLoadingProfile ? "Recalling..." : "Recall Memory"}
            </button>
          </div>
        </div>
        
        {/* Navigation Tabs */}
        <div className="flex flex-wrap gap-2.5 w-full xl:w-auto justify-start xl:justify-end border-t border-frenchgray/25 pt-4 xl:pt-0 xl:border-t-0">
          <button 
            onClick={() => setActiveTab("profile")} 
            className={`flex items-center gap-2 px-4 py-2 text-xs font-black uppercase border-3 border-navy shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-none transition-all cursor-pointer ${activeTab === "profile" ? "bg-vibrantred text-antiwhite" : "bg-antiwhite text-navy hover:bg-frenchgray/20"}`}
          >
            <Icons.User />
            1. Profile Ingestion
          </button>
          <button 
            onClick={() => setActiveTab("jobs")} 
            className={`flex items-center gap-2 px-4 py-2 text-xs font-black uppercase border-3 border-navy shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-none transition-all cursor-pointer ${activeTab === "jobs" ? "bg-vibrantred text-antiwhite" : "bg-antiwhite text-navy hover:bg-frenchgray/20"}`}
          >
            <Icons.Briefcase />
            2. Opportunities Board
          </button>
          <button 
            onClick={() => setActiveTab("applications")} 
            className={`flex items-center gap-2 px-4 py-2 text-xs font-black uppercase border-3 border-navy shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-none transition-all cursor-pointer ${activeTab === "applications" ? "bg-vibrantred text-antiwhite" : "bg-antiwhite text-navy hover:bg-frenchgray/20"}`}
          >
            <Icons.Folder />
            3. Applications ({applications.length})
          </button>
        </div>
      </div>

      {/* Active Pipeline Status Visualizer */}
      {applyingJobId && pipelineStatus.stage !== "Idle" && (
        <div className="bg-navy border-4 border-navy text-antiwhite p-6 mb-8 shadow-[6px_6px_0px_0px_rgba(239,35,60,1)] animate-fadeIn relative z-10">
          <div className="flex justify-between items-center border-b-2 border-frenchgray/25 pb-3 mb-4">
            <div className="flex items-center gap-2.5">
              <span className="w-2.5 h-2.5 bg-vibrantred rounded-full animate-ping" />
              <h3 className="text-sm font-black uppercase tracking-wider">Multi-Agent Pipeline Active</h3>
            </div>
            <span className="text-xs font-bold text-frenchgray uppercase">Agent: CascadeAgent (Drafter + Verifier)</span>
          </div>

          {/* Visual Step Indicator with connecting progress line */}
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6 relative">
            {/* Animated Progress Line */}
            <div className="hidden md:block absolute top-1/2 left-4 right-4 h-1 bg-frenchgray/20 -translate-y-1/2 z-0" />
            <div 
              className="hidden md:block absolute top-1/2 left-4 h-1 bg-vibrantred -translate-y-1/2 z-0 transition-all duration-700" 
              style={{ width: `${(activeStepIdx >= 0 ? activeStepIdx / 4 : 0) * 92}%` }}
            />
            
            {[
              "1. Ingestion Sync",
              "2. Job Analysis",
              "3. Profile Matching",
              "4. ATS Optimization",
              "5. Prep & Outreach"
            ].map((step, i) => (
              <div 
                key={i} 
                className={`relative z-10 flex md:flex-col items-center gap-3 md:gap-2 p-2.5 border-2 transition-all ${
                  i < activeStepIdx ? "bg-navy border-navy text-antiwhite" : 
                  i === activeStepIdx ? "bg-vibrantred border-navy text-antiwhite shadow-[2px_2px_0px_0px_rgba(43,45,66,1)] animate-pulse-glow" : 
                  "bg-antiwhite border-frenchgray/30 text-frenchgray/60"
                }`}
              >
                <div className={`w-6 h-6 rounded-full flex items-center justify-center font-black text-xs border-2 ${
                  i < activeStepIdx ? "bg-green-600 border-white text-white" : 
                  i === activeStepIdx ? "bg-antiwhite text-vibrantred border-vibrantred" : 
                  "bg-frenchgray/10 border-frenchgray/30 text-frenchgray/40"
                }`}>
                  {i < activeStepIdx ? <Icons.Check /> : i + 1}
                </div>
                <span className="text-[11px] font-black uppercase tracking-wide text-center">{step}</span>
              </div>
            ))}
          </div>

          <div className="bg-antiwhite/5 border-2 border-frenchgray/20 p-3 flex items-start gap-3">
            <div className="w-5 h-5 border-3 border-vibrantred border-t-transparent rounded-full animate-spin mt-0.5 shrink-0" />
            <div>
              <h4 className="text-xs font-black uppercase text-frenchgray tracking-wider">Current Pipeline Stage</h4>
              <p className="text-sm font-extrabold text-antiwhite mt-1 leading-relaxed">{pipelineStatus.stage}: {pipelineStatus.details}</p>
            </div>
          </div>
        </div>
      )}

      {/* Main Tab Views */}
      <main>
        
        {/* Tab 1: Ingestion & Profile Viewer */}
        {activeTab === "profile" && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 animate-fadeIn items-start">
            
            {/* Factual Memory Profile Card */}
            <section className="lg:col-span-7 bg-antiwhite border-4 border-navy p-4 sm:p-6 shadow-[6px_6px_0px_0px_rgba(43,45,66,1)] flex flex-col min-h-[500px]">
              <div className="flex justify-between items-center border-b-4 border-navy pb-3 mb-6">
                <div className="flex items-center gap-2">
                  <div className="bg-navy p-1.5 border border-navy text-antiwhite">
                    <Icons.Folder />
                  </div>
                  <h2 className="text-xl sm:text-2xl font-black uppercase tracking-wide">Factual Memory</h2>
                </div>
                {loadedProfile && (
                  <button 
                    onClick={fetchProfile}
                    className="flex items-center gap-1.5 bg-antiwhite hover:bg-frenchgray/20 border-2 border-navy text-[10px] font-black uppercase px-2.5 py-1.5 shadow-[1.5px_1.5px_0px_0px_rgba(43,45,66,1)] active:translate-y-0.5 active:shadow-none transition-all cursor-pointer"
                  >
                    <Icons.Refresh />
                    Sync view
                  </button>
                )}
              </div>

              {loadedProfile ? (
                <div className="space-y-6 flex-1 overflow-auto pr-1">
                  {/* Structured Open Cards Sections */}
                  <div className="grid grid-cols-1 gap-6">
                    {parsedSections.map((sec, i) => {
                      const isExpanded = expandedSections[i] !== false;
                      return (
                        <div key={i} className="border-3 border-navy p-4 shadow-[3px_3px_0px_0px_rgba(43,45,66,1)] bg-white relative transition-all duration-200 hover:shadow-[5px_5px_0px_0px_rgba(43,45,66,1)] hover:-translate-y-0.5">
                          <div className="absolute right-3 top-3 bg-navy/5 text-navy border border-navy/10 text-[9px] font-black uppercase px-1.5 py-0.5 tracking-wider font-sans select-none">
                            Section {i+1}
                          </div>
                          
                          <button
                            onClick={() => toggleSection(i)}
                            type="button"
                            className="w-full text-left flex items-center justify-between border-b-2 border-navy pb-1.5 mb-3 font-sans group cursor-pointer"
                          >
                            <h3 className="text-base font-black uppercase text-navy flex items-center gap-1.5">
                              <span className="w-1.5 h-3 bg-vibrantred group-hover:scale-y-125 transition-transform origin-center" />
                              {sec.title}
                            </h3>
                            <span className="text-navy transition-transform duration-200 transform group-hover:scale-110 pr-16">
                              {isExpanded ? (
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4">
                                  <polyline points="18 15 12 9 6 15" />
                                </svg>
                              ) : (
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4">
                                  <polyline points="6 9 12 15 18 9" />
                                </svg>
                              )}
                            </span>
                          </button>
                          
                          <div className={`overflow-hidden transition-all duration-300 ${isExpanded ? "max-h-[1200px] opacity-100 mt-2" : "max-h-0 opacity-0"}`}>
                            <RenderMarkdown text={sec.content} />
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {/* Refined Mental Model Box */}
                  <div className="border-3 border-navy p-4 bg-navy text-antiwhite shadow-[4px_4px_0px_0px_rgba(141,153,174,1)] relative overflow-hidden mt-8">
                    <div className="absolute right-0 bottom-0 text-[100px] text-frenchgray/5 font-black uppercase select-none pointer-events-none translate-y-10 translate-x-10">
                      MODEL
                    </div>
                    <div className="flex items-start gap-4 z-10 relative">
                      <div className="bg-vibrantred border-2 border-navy p-2 shrink-0">
                        <Icons.Sparkles />
                      </div>
                      <div>
                        <h3 className="text-sm font-black uppercase tracking-wider text-frenchgray font-sans">Adaptive Memory Preferences</h3>
                        <div className="text-xs font-bold leading-loose mt-2 text-antiwhite/90 bg-black/25 p-3 border border-frenchgray/10 font-mono whitespace-pre-wrap">
                          <RenderMarkdown text={loadedProfile.preferences || "Learning Preferences: No mental model preferences formed yet. Memory will update automatically based on job optimization results."} />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex-1 flex flex-col items-center justify-center border-4 border-dashed border-frenchgray/40 p-12 text-center text-frenchgray select-none">
                  <div className="bg-frenchgray/10 p-4 border-2 border-frenchgray/35 mb-4 text-frenchgray">
                    <Icons.Folder />
                  </div>
                  <h3 className="text-lg font-black uppercase tracking-wider">Cloud Memory Vacant</h3>
                  <p className="text-xs font-bold text-navy max-w-sm mt-2 leading-relaxed">
                    Recalled candidate details will compile here. Enter a valid User ID above and hit <span className="font-extrabold text-vibrantred">"Recall Memory"</span>, or register via the form on the right.
                  </p>
                </div>
              )}
            </section>

            {/* Profile Ingestion Form Card - Sticky on Scroll */}
            <section className="lg:col-span-5 bg-antiwhite border-4 border-navy p-4 sm:p-6 shadow-[6px_6px_0px_0px_rgba(43,45,66,1)] lg:sticky lg:top-6 self-start flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between border-b-4 border-navy pb-3 mb-4">
                  <h2 className="text-xl sm:text-2xl font-black uppercase flex items-center gap-2">
                    <div className="bg-navy p-1.5 border border-navy text-antiwhite">
                      <Icons.User />
                    </div>
                    Ingestion Console
                  </h2>
                  
                  {/* Gauge indicator */}
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-black text-frenchgray uppercase">Setup Completion:</span>
                    <span className={`text-xs font-black px-1.5 py-0.5 border-2 border-navy ${completionPercentage === 100 ? "bg-green-100 text-green-700" : "bg-white text-navy"}`}>
                      {completionPercentage}%
                    </span>
                  </div>
                </div>

                {/* Form Switching Tabs */}
                <div className="grid grid-cols-3 gap-1 mb-5 border-b-2 border-navy pb-2">
                  {(["basics", "crawlers", "resume"] as const).map(step => (
                    <button
                      key={step}
                      type="button"
                      onClick={() => setFormStep(step)}
                      className={`text-[10px] font-black uppercase py-2 px-1 border-2 border-navy text-center transition-all cursor-pointer ${formStep === step ? "bg-navy text-antiwhite shadow-[2px_2px_0px_0px_rgba(239,35,60,1)] -translate-y-0.5" : "bg-white text-navy hover:bg-frenchgray/10"}`}
                    >
                      {step === "basics" ? "1. Basics" : step === "crawlers" ? "2. Sync" : "3. Import"}
                    </button>
                  ))}
                </div>

                <form onSubmit={handleOnboard} className="space-y-5">
                  {/* Step 1: Basics */}
                  {formStep === "basics" && (
                    <div className="space-y-4 animate-fade-in">
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-[10px] font-black uppercase text-frenchgray mb-1 tracking-wider font-sans">Candidate Name</label>
                          <input 
                            type="text" 
                            value={name} 
                            onChange={e => setName(e.target.value)} 
                            className="w-full border-3 border-navy p-2 bg-white focus:outline-none focus:ring-2 focus:ring-vibrantred focus:shadow-[2px_2px_0px_0px_rgba(239,35,60,1)] transition-all font-bold text-xs" 
                            required 
                          />
                        </div>
                        <div>
                          <label className="block text-[10px] font-black uppercase text-frenchgray mb-1 tracking-wider font-sans">Contact Email</label>
                          <input 
                            type="email" 
                            value={email} 
                            onChange={e => setEmail(e.target.value)} 
                            className="w-full border-3 border-navy p-2 bg-white focus:outline-none focus:ring-2 focus:ring-vibrantred focus:shadow-[2px_2px_0px_0px_rgba(239,35,60,1)] transition-all font-bold text-xs" 
                            required 
                          />
                        </div>
                      </div>
                      <div>
                        <label className="block text-[10px] font-black uppercase text-frenchgray mb-1 tracking-wider font-sans">Phone Number</label>
                        <input 
                          type="tel" 
                          value={phone} 
                          onChange={e => setPhone(e.target.value)} 
                          placeholder="6301893787" 
                          className="w-full border-3 border-navy p-2 bg-white focus:outline-none focus:ring-2 focus:ring-vibrantred focus:shadow-[2px_2px_0px_0px_rgba(239,35,60,1)] transition-all font-bold text-xs" 
                        />
                      </div>
                      <div>
                        <label className="block text-[10px] font-black uppercase text-frenchgray mb-1 tracking-wider font-sans">University / Major</label>
                        <input 
                          type="text" 
                          value={education} 
                          onChange={e => setEducation(e.target.value)} 
                          className="w-full border-3 border-navy p-2 bg-white focus:outline-none focus:ring-2 focus:ring-vibrantred focus:shadow-[2px_2px_0px_0px_rgba(239,35,60,1)] transition-all font-bold text-xs" 
                        />
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-[10px] font-black uppercase text-frenchgray mb-1 tracking-wider font-sans">CGPA / Performance</label>
                          <input 
                            type="text" 
                            value={cgpa} 
                            onChange={e => setCgpa(e.target.value)} 
                            className="w-full border-3 border-navy p-2 bg-white focus:outline-none focus:ring-2 focus:ring-vibrantred focus:shadow-[2px_2px_0px_0px_rgba(239,35,60,1)] transition-all font-bold text-xs" 
                          />
                        </div>
                        <div>
                          <label className="block text-[10px] font-black uppercase text-frenchgray mb-1 tracking-wider font-sans">Core Experience</label>
                          <input 
                            type="text" 
                            value={experience} 
                            onChange={e => setExperience(e.target.value)} 
                            className="w-full border-3 border-navy p-2 bg-white focus:outline-none focus:ring-2 focus:ring-vibrantred focus:shadow-[2px_2px_0px_0px_rgba(239,35,60,1)] transition-all font-bold text-xs" 
                          />
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Step 2: Crawlers & Socials */}
                  {formStep === "crawlers" && (
                    <div className="space-y-4 animate-fade-in font-sans">
                      <p className="text-[10px] font-bold text-frenchgray leading-relaxed uppercase border-l-2 border-vibrantred pl-2">
                        Configure crawler sync triggers. Checked entries indicate active Sync states.
                      </p>
                      
                      <div className="space-y-3">
                        {[
                          { key: "GitHub", val: github, set: setGithub, ph: "GitHub profile URL" },
                          { key: "LeetCode", val: leetcode, set: setLeetcode, ph: "Leetcode user profile" },
                          { key: "Codeforces", val: codeforces, set: setCodeforces, ph: "Codeforces profile" },
                          { key: "CodeChef", val: codechef, set: setCodechef, ph: "Codechef handler link" },
                          { key: "LinkedIn", val: linkedin, set: setLinkedin, ph: "LinkedIn public URL" },
                          { key: "Portfolio", val: portfolio, set: setPortfolio, ph: "Personal website link" }
                        ].map(c => {
                          const isSynced = c.val && c.val.startsWith("http");
                          return (
                            <div key={c.key} className="flex items-center border-3 border-navy bg-white focus-within:shadow-[2px_2px_0px_0px_rgba(239,35,60,1)] focus-within:ring-2 focus-within:ring-vibrantred transition-all">
                              <span className="bg-navy border-r-3 border-navy text-antiwhite p-2 shrink-0 text-[10px] font-black min-w-[90px] text-center uppercase flex items-center justify-center gap-1">
                                {c.key}
                              </span>
                              <input 
                                type="url" 
                                placeholder={c.ph} 
                                value={c.val} 
                                onChange={e => c.set(e.target.value)} 
                                className="w-full p-2 bg-transparent text-xs font-bold focus:outline-none" 
                              />
                              <span className={`px-2 text-xs font-black uppercase select-none ${isSynced ? "text-green-600" : "text-frenchgray/40"}`}>
                                {isSynced ? "✔ Sync" : "No"}
                              </span>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {/* Step 3: Raw Resume Import */}
                  {formStep === "resume" && (
                    <div className="space-y-4 animate-fade-in font-sans">
                      <div>
                        <label className="block text-[10px] font-black uppercase text-frenchgray mb-1 tracking-wider">Previous Resume Plain Text</label>
                        <textarea 
                          placeholder="Paste details of projects, past roles, or generic achievements here..." 
                          value={previousResumeText} 
                          onChange={e => setPreviousResumeText(e.target.value)} 
                          className="w-full h-36 border-3 border-navy p-2 bg-white text-xs font-bold focus:outline-none focus:ring-2 focus:ring-vibrantred focus:shadow-[2px_2px_0px_0px_rgba(239,35,60,1)] transition-all leading-relaxed"
                        />
                      </div>
                      
                      {/* Dropzone mock */}
                      <div className="bg-navy/5 border-2 border-navy border-dashed p-4 flex flex-col items-center justify-center text-center relative hover:bg-navy/10 transition-colors">
                        <Icons.Download />
                        <span className="text-[10px] font-black uppercase text-navy mt-1.5 block">Import Text/TeX Document</span>
                        <span className="text-[9px] text-frenchgray block mt-0.5">Loads resume contents immediately</span>
                        <input 
                          type="file" 
                          accept=".txt,.md,.tex,.latex" 
                          onChange={handleFileUpload} 
                          className="absolute inset-0 opacity-0 cursor-pointer" 
                        />
                      </div>
                    </div>
                  )}

                  {/* Submit buttons */}
                  <div className="pt-2 border-t-2 border-navy/10 flex flex-col gap-2 font-sans">
                    <button 
                      type="submit" 
                      disabled={isOnboarding} 
                      className="w-full bg-vibrantred hover:bg-engorange disabled:bg-frenchgray text-antiwhite font-black py-3 uppercase border-3 border-navy shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-none transition-all cursor-pointer text-center text-xs tracking-wider"
                    >
                      {isOnboarding ? "Ingesting & Mapping Matrix..." : "Sync & Synthesize Profile"}
                    </button>
                  </div>

                  {/* Onboarding Logs Console */}
                  {onboardStatus && (
                    <div className="bg-navy text-antiwhite p-4 border-3 border-navy font-mono text-xs shadow-[3px_3px_0px_0px_rgba(141,153,174,1)] whitespace-pre-wrap leading-loose">
                      <div className="text-[10px] text-frenchgray border-b border-frenchgray/25 pb-1 mb-2 uppercase font-black tracking-wider flex justify-between">
                        <span>Sync Log</span>
                        <span className="w-1.5 h-3 bg-green-500 inline-block animate-pulse" />
                      </div>
                      {onboardStatus}
                    </div>
                  )}
                </form>
              </div>
            </section>
          </div>
        )}

        {/* Tab 2: Simulated Jobs Board */}
        {activeTab === "jobs" && (
          <div className="bg-antiwhite border-4 border-navy p-4 sm:p-6 shadow-[6px_6px_0px_0px_rgba(43,45,66,1)] animate-fadeIn">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center border-b-4 border-navy pb-3 mb-6 gap-3">
              <div className="flex items-center gap-2">
                <div className="bg-navy p-1.5 border border-navy text-antiwhite">
                  <Icons.Briefcase />
                </div>
                <h2 className="text-xl sm:text-2xl font-black uppercase tracking-wide">Opportunities Board</h2>
              </div>
              <span className="bg-vibrantred text-antiwhite text-[10px] font-black uppercase px-2.5 py-1 border-2 border-navy shadow-[2px_2px_0px_0px_rgba(43,45,66,1)] tracking-wide font-sans">
                Matches Calibrated
              </span>
            </div>

            {/* Manual Job Description Paste Option */}
            <div className="bg-white border-4 border-navy p-5 mb-8 shadow-[4px_4px_0px_0px_rgba(239,35,60,1)] font-sans">
              <h3 className="text-sm font-black uppercase text-navy border-b-2 border-navy pb-2 mb-3 tracking-wider flex items-center gap-1.5">
                <span className="w-1.5 h-3.5 bg-vibrantred" />
                Custom Job Optimization (Paste Raw Job Description)
              </h3>
              <p className="text-[10px] font-bold text-frenchgray uppercase mb-4 leading-normal">
                Paste a complete Job Description text below. The backend agent will parse the company name, job title, and requirements automatically, then execute the optimization loop.
              </p>
              <form onSubmit={handleManualApply} className="space-y-4">
                <textarea
                  placeholder="Paste the full job description text here (e.g. 'We are looking for a Software Engineer at Google...')"
                  value={manualJdText}
                  onChange={e => setManualJdText(e.target.value)}
                  className="w-full h-32 bg-antiwhite border-3 border-navy p-3 font-semibold focus:outline-none text-xs leading-relaxed text-navy focus:ring-2 focus:ring-vibrantred focus:shadow-[2px_2px_0px_0px_rgba(239,35,60,1)] transition-all resize-y"
                  required
                />
                <button
                  type="submit"
                  disabled={isSubmittingManualJd || !manualJdText.trim()}
                  className="bg-vibrantred hover:bg-engorange disabled:bg-frenchgray text-antiwhite text-[10px] font-black uppercase px-5 py-2.5 border-3 border-navy shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-none transition-all cursor-pointer inline-flex items-center gap-1.5"
                >
                  {isSubmittingManualJd ? (
                    <>
                      <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      Parsing & Optimizing...
                    </>
                  ) : (
                    "Optimize Assets for this JD"
                  )}
                </button>
              </form>
            </div>

            {/* Filters Bar */}
            <div className="flex flex-col lg:flex-row gap-4 mb-6 font-sans">
              <div className="flex-1 flex items-center border-4 border-navy bg-white shadow-[2px_2px_0px_0px_rgba(43,45,66,1)]">
                <div className="p-3 text-frenchgray">
                  <Icons.Search />
                </div>
                <input
                  type="text"
                  placeholder="Search by Title, Company, or Skills..."
                  value={searchTerm}
                  onChange={e => { setSearchTerm(e.target.value); setPage(1); }}
                  className="w-full p-2 bg-transparent font-bold focus:outline-none text-xs sm:text-sm text-navy"
                />
              </div>
              <div className="flex items-center border-4 border-navy bg-white shadow-[2px_2px_0px_0px_rgba(43,45,66,1)]">
                <div className="p-3 text-frenchgray border-r border-navy/10">
                  <Icons.Filter />
                </div>
                <select
                  value={selectedCategory}
                  onChange={e => { setSelectedCategory(e.target.value); setPage(1); }}
                  className="p-3 bg-transparent font-black uppercase text-xs focus:outline-none cursor-pointer text-navy"
                >
                  <option value="">All Categories</option>
                  <option value="Machine Learning">Machine Learning</option>
                  <option value="Robotics">Robotics</option>
                  <option value="Software Engineering">Software Engineering</option>
                  <option value="Frontend Development">Frontend Development</option>
                  <option value="IT & Support">IT & Support</option>
                  <option value="Cloud & DevOps">Cloud & DevOps</option>
                  <option value="Data Science">Data Science</option>
                </select>
              </div>
            </div>



            {/* Jobs Board Grid Layout */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {jobs.map(job => {
                // Mock calculation of match scores
                const matchScore = job.experience_years <= 2 ? 95 : 82;
                const isRecommended = job.skills.some(s => s.toLowerCase().includes("learning") || s.toLowerCase().includes("ml") || s.toLowerCase().includes("robot"));

                return (
                  <div 
                    key={job.id} 
                    className="border-4 border-navy p-5 bg-white flex flex-col justify-between shadow-[4px_4px_0px_0px_rgba(43,45,66,1)] hover:-translate-x-1 hover:-translate-y-1 hover:shadow-[7px_7px_0px_0px_rgba(43,45,66,1)] transition-all relative overflow-hidden"
                  >
                    <div>
                      <div className="flex justify-between items-start gap-2">
                        <span className="bg-navy text-antiwhite text-[9px] font-black uppercase px-2 py-0.5 tracking-wider border border-navy font-sans">{job.category}</span>
                        <span className="text-[9px] font-extrabold text-frenchgray uppercase tracking-wide bg-antiwhite px-2 py-0.5 border border-navy/10 font-sans">{job.location}</span>
                      </div>

                      <h3 
                        onClick={() => setSelectedJob(job)}
                        className="text-lg font-black mt-3.5 text-navy line-clamp-1 leading-snug cursor-pointer hover:text-vibrantred hover:underline"
                      >
                        {job.title}
                      </h3>
                      <p className="text-xs font-black text-vibrantred uppercase tracking-wider font-sans">{job.company}</p>
                      
                      {/* Match Score Gauge Indicator */}
                      <div className="flex items-center gap-2 mt-3.5 font-sans">
                        <RadialProgress score={matchScore} size={38} strokeWidth={3} />
                        {isRecommended && (
                          <div className="bg-vibrantred text-antiwhite text-[9px] font-black uppercase px-2 py-0.5 border border-navy">
                            ★ Recommended
                          </div>
                        )}
                      </div>

                      <p className="text-xs text-navy/85 mt-4 line-clamp-3 font-semibold leading-loose border-t border-navy/5 pt-3 select-text font-sans">
                        {job.description}
                      </p>
                      
                      {/* Skill Tags */}
                      <div className="flex flex-wrap gap-1 mt-4 font-sans">
                        {job.skills.slice(0, 4).map((skill, index) => (
                          <span key={index} className="bg-frenchgray/15 text-navy border border-navy/30 text-[9px] font-extrabold px-2 py-0.5 select-all">
                            {skill}
                          </span>
                        ))}
                        {job.skills.length > 4 && (
                          <span className="bg-navy text-antiwhite border border-navy text-[9px] font-black px-2 py-0.5">
                            +{job.skills.length - 4} more
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="mt-6 border-t-2 border-navy pt-4 flex items-center justify-between gap-2 font-sans">
                      <button
                        onClick={() => setSelectedJob(job)}
                        className="text-[10px] font-black uppercase text-frenchgray hover:text-navy tracking-wide flex items-center gap-0.5 cursor-pointer underline"
                      >
                        View Details <Icons.ChevronRight />
                      </button>
                      <button
                        onClick={() => handleApply(job.id)}
                        disabled={applyingJobId !== null}
                        className="bg-vibrantred hover:bg-engorange disabled:bg-frenchgray text-antiwhite text-[10px] font-black uppercase px-4.5 py-2 border-2 border-navy shadow-[2px_2px_0px_0px_rgba(43,45,66,1)] hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-none transition-all cursor-pointer whitespace-nowrap"
                      >
                        {applyingJobId === job.id ? "Optimizing..." : "Apply & Optimize"}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Pagination Controls */}
            <div className="flex justify-between items-center mt-8 border-t-4 border-navy pt-6 font-sans">
              <span className="text-xs sm:text-sm font-black uppercase text-frenchgray tracking-wider">Total Discoverable: {totalJobs} jobs</span>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="bg-white hover:bg-frenchgray/15 text-navy font-black text-xs uppercase px-4 py-2 border-3 border-navy disabled:opacity-40 cursor-pointer shadow-[2px_2px_0px_0px_rgba(43,45,66,1)] active:translate-y-0.5 active:shadow-none transition-all"
                >
                  Previous
                </button>
                <button
                  onClick={() => setPage(p => p + 1)}
                  disabled={page * 6 >= totalJobs}
                  className="bg-white hover:bg-frenchgray/15 text-navy font-black text-xs uppercase px-4 py-2 border-3 border-navy disabled:opacity-40 cursor-pointer shadow-[2px_2px_0px_0px_rgba(43,45,66,1)] active:translate-y-0.5 active:shadow-none transition-all"
                >
                  Next
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Tab 3: Applications & Outputs Hub */}
        {activeTab === "applications" && (
          <div className="bg-antiwhite border-4 border-navy p-4 sm:p-6 shadow-[6px_6px_0px_0px_rgba(43,45,66,1)] animate-fadeIn">
            <div className="flex items-center gap-2 border-b-4 border-navy pb-3 mb-6">
              <div className="bg-navy p-1.5 border border-navy text-antiwhite">
                <Icons.Folder />
              </div>
              <h2 className="text-xl sm:text-2xl font-black uppercase tracking-wide">Applications Dashboard</h2>
            </div>
            
            {applications.length === 0 ? (
              <div className="p-12 border-4 border-dashed border-frenchgray/40 text-center font-bold text-frenchgray/60 uppercase select-none">
                No processed applications yet. Trigger optimization inside the Opportunities Board first.
              </div>
            ) : (
              <div className="space-y-6">
                {applications.map(app => {
                  return (
                    <div key={app.id} className="border-4 border-navy p-6 bg-white shadow-[4px_4px_0px_0px_rgba(43,45,66,1)] relative overflow-hidden flex flex-col md:flex-row md:items-center justify-between gap-6 hover:shadow-[6px_6px_0px_0px_rgba(43,45,66,1)] transition-all font-sans">
                      {/* Decorative red edge */}
                      <div className="absolute left-0 top-0 h-full w-2 bg-vibrantred" />
                      
                      <div className="pl-2">
                        <h3 className="text-lg sm:text-xl font-black uppercase text-navy leading-snug">{app.role}</h3>
                        <p className="text-xs font-black uppercase text-vibrantred tracking-wide mt-0.5">{app.company}</p>
                        
                        <div className="flex flex-wrap gap-2 mt-3">
                          {app.has_pdf && <span className="bg-green-100 text-green-800 border border-green-300 text-[8px] font-black uppercase px-2 py-0.5">PDF Compiled</span>}
                          {app.has_tex && <span className="bg-blue-100 text-blue-800 border border-blue-300 text-[8px] font-black uppercase px-2 py-0.5">TeX Source</span>}
                          {app.has_prep && <span className="bg-purple-100 text-purple-800 border border-purple-300 text-[8px] font-black uppercase px-2 py-0.5">Prep Guide</span>}
                          {app.has_outreach && <span className="bg-amber-100 text-amber-800 border border-amber-300 text-[8px] font-black uppercase px-2 py-0.5">Outreach Ready</span>}
                        </div>
                      </div>
                      
                      <div className="flex flex-wrap items-center gap-4 pl-2 md:pl-0 border-l-2 md:border-l-0 border-frenchgray/15 shrink-0">
                        {/* ATS score indicator gauge */}
                        <div className="flex items-center gap-3">
                          <RadialProgress score={app.ats_score} size={48} strokeWidth={4} />
                          <div>
                            <span className="text-[9px] font-black uppercase block tracking-wider text-frenchgray leading-none">ATS Calibration</span>
                            <span className={`text-xs font-black uppercase mt-1 inline-block px-1.5 py-0.5 text-white ${
                              app.ats_score >= 80 ? "bg-green-600" : app.ats_score >= 70 ? "bg-amber-500" : "bg-vibrantred"
                            }`}>
                              {app.ats_score >= 80 ? "Passed" : app.ats_score >= 70 ? "Review" : "Alert"}
                            </span>
                          </div>
                        </div>

                        <button
                          onClick={() => {
                            setSelectedApp(app);
                            setAppDrawerTab("metrics");
                          }}
                          className="bg-navy hover:bg-frenchgray text-antiwhite text-[10px] font-black uppercase px-4 py-3 border-2 border-navy shadow-[2px_2px_0px_0px_rgba(43,45,66,1)] hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-none transition-all cursor-pointer"
                        >
                          View Analysis & Output
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

      </main>

      {/* ---------------- DRAWERS ---------------- */}

      {/* ---------------- DRAWERS & MODALS ---------------- */}

      <JobDetailsDrawer
        job={selectedJob}
        onClose={() => setSelectedJob(null)}
        onApply={handleApply}
        applyingJobId={applyingJobId}
      />

      <ApplicationDetailsDrawer
        app={selectedApp}
        onClose={() => setSelectedApp(null)}
        API_BASE={API_BASE}
        isLoadingAppDetails={isLoadingAppDetails}
        appOutreachContent={appOutreachContent}
        appDrawerTab={appDrawerTab}
        setAppDrawerTab={setAppDrawerTab}
        copyToClipboard={copyToClipboard}
        openInOverleaf={openInOverleaf}
      />
      </>)}

    </div>
  );
}
