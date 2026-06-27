import React from "react";
import { Icons } from "./icons";
import { RadialProgress } from "./RadialProgress";
import { RenderMarkdown } from "./RenderMarkdown";

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

interface ApplicationDetailsDrawerProps {
  app: Application | null;
  onClose: () => void;
  API_BASE: string;
  isLoadingAppDetails: boolean;
  appOutreachContent: string;
  appDrawerTab: "metrics" | "preview" | "outreach" | "prep";
  setAppDrawerTab: (tab: "metrics" | "preview" | "outreach" | "prep") => void;
  copyToClipboard: (text: string, title: string) => void;
  openInOverleaf: (appId: string) => void;
}

export const ApplicationDetailsDrawer = ({
  app,
  onClose,
  API_BASE,
  isLoadingAppDetails,
  appOutreachContent,
  appDrawerTab,
  setAppDrawerTab,
  copyToClipboard,
  openInOverleaf
}: ApplicationDetailsDrawerProps) => {
  if (!app) return null;

  return (
    <>
      <div 
        className="fixed inset-0 bg-navy/60 backdrop-blur-sm z-[90] animate-fade-in" 
        onClick={onClose} 
      />
      <div className="fixed top-0 right-0 h-full w-full sm:w-[650px] md:w-[800px] bg-antiwhite border-l-4 border-navy shadow-[-10px_0px_30px_rgba(43,45,66,0.35)] z-[95] overflow-y-auto animate-drawer-in flex flex-col justify-between">
        <div className="p-6 flex-1 flex flex-col min-h-0">
          
          {/* Header block */}
          <div className="flex justify-between items-start border-b-4 border-navy pb-3 mb-4 shrink-0">
            <div>
              <h2 className="text-xl sm:text-2xl font-black uppercase text-navy leading-none">{app.role}</h2>
              <p className="text-sm font-black uppercase text-vibrantred tracking-wide mt-1">{app.company}</p>
            </div>
            <button 
              onClick={onClose}
              className="bg-white hover:bg-frenchgray/20 border-2 border-navy p-1.5 text-navy cursor-pointer transition-all shrink-0"
            >
              <Icons.Close />
            </button>
          </div>

          {/* Subnavigation Tabs inside Application Drawer */}
          <div className="flex flex-wrap border-2 border-navy mb-6 bg-white font-sans shrink-0">
            {[
              { id: "metrics", label: "ATS Analysis" },
              { id: "preview", label: "Resume Preview" },
              { id: "outreach", label: "Outreach Copy" },
              { id: "prep", label: "Prep Guide" }
            ].map(t => (
              <button
                key={t.id}
                onClick={() => setAppDrawerTab(t.id as any)}
                className={`flex-1 text-[10px] font-black uppercase py-2.5 px-2 text-center border-r last:border-r-0 border-navy transition-all cursor-pointer ${
                  appDrawerTab === t.id ? "bg-navy text-antiwhite" : "bg-white text-navy hover:bg-frenchgray/10"
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>

          {/* Action Bar for Downloads */}
          <div className="flex flex-wrap items-center gap-2 p-3 bg-white border-2 border-navy mb-6 text-xs uppercase font-bold font-sans shrink-0">
            <span className="text-[9px] text-frenchgray font-black uppercase mr-2">Downloadable Resources:</span>
            
            {app.has_pdf && (
              <a
                href={`${API_BASE}/api/download/${app.id}/resume.pdf`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 bg-navy text-antiwhite px-3 py-1 border-2 border-navy text-[9px] font-black shadow-[1.5px_1.5px_0px_0px_rgba(0,0,0,1)] hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-none transition-all"
              >
                <Icons.Download /> PDF Resume
              </a>
            )}
            {app.has_tex && (
              <a
                href={`${API_BASE}/api/download/${app.id}/resume.tex`}
                download
                className="flex items-center gap-1 bg-white text-navy px-3 py-1 border-2 border-navy text-[9px] font-black shadow-[1.5px_1.5px_0px_0px_rgba(0,0,0,1)] hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-none transition-all"
              >
                <Icons.Terminal /> LaTeX Source
              </a>
            )}
            {app.has_prep && (
              <a
                href={`${API_BASE}/api/download/${app.id}/interview_readiness.pdf`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 bg-navy text-antiwhite px-3 py-1 border-2 border-navy text-[9px] font-black shadow-[1.5px_1.5px_0px_0px_rgba(0,0,0,1)] hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-none transition-all"
              >
                <Icons.Academic /> Prep PDF
              </a>
            )}
            {app.has_tex && (
              <button 
                onClick={() => openInOverleaf(app.id)} 
                className="flex items-center gap-1 bg-vibrantred text-antiwhite border-2 border-navy px-3 py-1 text-[9px] font-black shadow-[1.5px_1.5px_0px_0px_rgba(43,45,66,1)] hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-none transition-all cursor-pointer"
              >
                <Icons.ExternalLink /> Overleaf
              </button>
            )}
          </div>

          {isLoadingAppDetails ? (
            <div className="p-16 text-center shrink-0">
              <div className="w-8 h-8 border-3 border-vibrantred border-t-transparent rounded-full animate-spin mx-auto mb-4" />
              <p className="text-xs font-black uppercase text-frenchgray">Recalling Application Artifacts...</p>
            </div>
          ) : (
            <div className="flex-1 min-h-0 flex flex-col">
              {/* Tab A: ATS Analysis & Strengths/Improvements */}
              {appDrawerTab === "metrics" && (
                <div className="space-y-6 animate-fade-in font-sans overflow-y-auto pr-1">
                  <div className="flex items-center gap-4 bg-white border-3 border-navy p-4 shadow-[3px_3px_0px_0px_rgba(43,45,66,1)]">
                    <RadialProgress score={app.ats_score} size={64} strokeWidth={5} />
                    <div>
                      <h3 className="text-sm font-black uppercase text-navy">Targeted ATS Calibration</h3>
                      <p className="text-xs text-frenchgray font-semibold mt-1">
                        This score indicates the semantic alignment between your profile resources and the job specification.
                      </p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-white border-2 border-green-600/35 p-4 shadow-[2px_2px_0px_0px_rgba(22,163,74,0.15)]">
                      <h4 className="text-[10px] font-black uppercase text-green-700 mb-3 tracking-wider flex items-center gap-1.5">
                        <Icons.Check /> Highlighted Strengths
                      </h4>
                      {app.strengths.length > 0 ? (
                        <ul className="space-y-2">
                          {app.strengths.map((str, i) => (
                            <li key={i} className="text-xs font-bold text-navy leading-relaxed flex items-start gap-2">
                              <span className="text-green-600 font-extrabold select-none">•</span>
                              <span>{str}</span>
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <span className="text-xs text-frenchgray italic">Profile matching calibration successfully covered requirements.</span>
                      )}
                    </div>

                    <div className="bg-white border-2 border-amber-600/35 p-4 shadow-[2px_2px_0px_0px_rgba(217,119,6,0.15)]">
                      <h4 className="text-[10px] font-black uppercase text-amber-700 mb-3 tracking-wider flex items-center gap-1.5">
                        <Icons.Alert /> Calibrated Areas for Growth
                      </h4>
                      {app.improvements.length > 0 ? (
                        <ul className="space-y-2">
                          {app.improvements.map((imp, i) => (
                            <li key={i} className="text-xs font-bold text-navy leading-relaxed flex items-start gap-2">
                              <span className="text-amber-500 font-extrabold select-none">•</span>
                              <span>{imp}</span>
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <span className="text-xs text-frenchgray italic">No gaps in key competency requirements identified.</span>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Tab B: targeted Resume Sheet Preview */}
              {appDrawerTab === "preview" && (
                <div className="animate-fade-in font-sans flex-1 flex flex-col min-h-0">
                  <p className="text-[10px] font-black uppercase text-frenchgray tracking-wider leading-none mb-3">
                    Targeted LaTeX Resume PDF Document (rendered inline)
                  </p>
                  
                  {app.has_pdf ? (
                    <iframe
                      src={`${API_BASE}/api/download/${app.id}/resume.pdf#toolbar=0&navpanes=0&scrollbar=1`}
                      className="w-full flex-1 border-3 border-navy bg-white shadow-[4px_4px_0px_0px_rgba(43,45,66,1)] min-h-[500px]"
                      title="Resume PDF Document"
                    />
                  ) : (
                    <div className="p-12 border-4 border-dashed border-frenchgray/40 text-center font-bold text-frenchgray/60 uppercase">
                      PDF compiled document not available. Verify TeX compiler logs.
                    </div>
                  )}
                </div>
              )}

              {/* Tab C: Outreach Messages templates */}
              {appDrawerTab === "outreach" && (
                <div className="space-y-4 animate-fade-in font-sans flex-1 flex flex-col min-h-0">
                  <div className="flex justify-between items-center shrink-0">
                    <span className="text-[10px] font-black uppercase text-frenchgray tracking-wider">Generated outreach email/message templates</span>
                    <button
                      onClick={() => copyToClipboard(appOutreachContent, "Outreach message")}
                      className="bg-white hover:bg-frenchgray/20 border-2 border-navy text-[10px] font-black uppercase px-2.5 py-1 flex items-center gap-1 cursor-pointer transition-all shadow-[1.5px_1.5px_0px_0px_rgba(0,0,0,1)] active:translate-y-0.5 active:shadow-none"
                    >
                      <Icons.Copy /> Copy Outreach Text
                    </button>
                  </div>
                  
                  <div className="bg-white border-3 border-navy p-5 font-semibold text-xs leading-loose text-navy shadow-[3px_3px_0px_0px_rgba(43,45,66,1)] flex-1 overflow-y-auto min-h-0">
                    {appOutreachContent ? (
                      <RenderMarkdown text={appOutreachContent} />
                    ) : (
                      <span className="text-frenchgray/60 uppercase text-[10px] font-black">No outreach templates found for this applicant pipeline.</span>
                    )}
                  </div>
                </div>
              )}

              {/* Tab D: Interview Prep guides */}
              {appDrawerTab === "prep" && (
                <div className="animate-fade-in font-sans flex-1 flex flex-col min-h-0">
                  <p className="text-[10px] font-black uppercase text-frenchgray tracking-wider leading-none mb-3">
                    Interview Readiness Preparation Guide PDF (rendered inline)
                  </p>
                  
                  {app.has_prep ? (
                    <iframe
                      src={`${API_BASE}/api/download/${app.id}/interview_readiness.pdf#toolbar=0&navpanes=0&scrollbar=1`}
                      className="w-full flex-1 border-3 border-navy bg-white shadow-[4px_4px_0px_0px_rgba(43,45,66,1)] min-h-[500px]"
                      title="Interview Prep Guide PDF"
                    />
                  ) : (
                    <div className="p-12 border-4 border-dashed border-frenchgray/40 text-center font-bold text-frenchgray/60 uppercase">
                      Preparation PDF guide not available. Verify agent output.
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        <div className="p-6 bg-white border-t-4 border-navy flex justify-end font-sans shrink-0">
          <button
            onClick={onClose}
            className="bg-navy hover:bg-frenchgray text-antiwhite font-black text-xs uppercase px-5 py-2 border-3 border-navy cursor-pointer transition-all shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] active:translate-y-0.5 active:shadow-none"
          >
            Close Dashboard
          </button>
        </div>
      </div>
    </>
  );
};
