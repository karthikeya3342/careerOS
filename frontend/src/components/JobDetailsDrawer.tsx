import React from "react";
import { Icons } from "./icons";

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

interface JobDetailsDrawerProps {
  job: Job | null;
  onClose: () => void;
  onApply: (jobId: string) => void;
  applyingJobId: string | null;
}

export const JobDetailsDrawer = ({ job, onClose, onApply, applyingJobId }: JobDetailsDrawerProps) => {
  if (!job) return null;

  return (
    <>
      <div 
        className="fixed inset-0 bg-navy/60 backdrop-blur-sm z-[90] animate-fade-in" 
        onClick={onClose} 
      />
      <div className="fixed top-0 right-0 h-full w-full sm:w-[600px] md:w-[700px] bg-antiwhite border-l-4 border-navy shadow-[-10px_0px_30px_rgba(43,45,66,0.35)] z-[95] overflow-y-auto animate-drawer-in flex flex-col justify-between">
        <div className="p-6">
          <div className="flex justify-between items-start border-b-4 border-navy pb-3 mb-6">
            <div>
              <span className="bg-navy text-antiwhite text-[9px] font-black uppercase px-2 py-0.5 border border-navy">{job.category}</span>
              <h2 className="text-2xl font-black uppercase text-navy mt-2 leading-tight">{job.title}</h2>
              <p className="text-sm font-black uppercase text-vibrantred tracking-wide">{job.company}</p>
            </div>
            <button 
              onClick={onClose}
              className="bg-white hover:bg-frenchgray/20 border-2 border-navy p-1.5 text-navy cursor-pointer transition-all shrink-0"
            >
              <Icons.Close />
            </button>
          </div>

          {/* Stats Bar */}
          <div className="grid grid-cols-3 gap-2 bg-white border-2 border-navy p-3 mb-6 font-bold text-xs uppercase text-center font-sans">
            <div>
              <span className="text-[9px] text-frenchgray block">Location</span>
              <span className="text-navy font-black text-[10px] mt-0.5 block">{job.location}</span>
            </div>
            <div className="border-x border-navy/10">
              <span className="text-[9px] text-frenchgray block">Job Type</span>
              <span className="text-navy font-black text-[10px] mt-0.5 block">{job.type}</span>
            </div>
            <div>
              <span className="text-[9px] text-frenchgray block">Min Experience</span>
              <span className="text-navy font-black text-[10px] mt-0.5 block">{job.experience_years} Years</span>
            </div>
          </div>

          {/* Match alignment estimation */}
          <div className="border-3 border-navy p-4 bg-white shadow-[3px_3px_0px_0px_rgba(43,45,66,1)] mb-6 font-sans">
            <h3 className="text-xs font-black uppercase text-navy border-b border-navy/10 pb-1.5 mb-3 flex items-center gap-1.5 font-sans">
              <Icons.Sparkles /> Match Alignment Analysis
            </h3>
            <div className="space-y-3 text-xs">
              <div>
                <span className="font-extrabold uppercase text-[9px] text-green-600 block">Matched Core Skills</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {job.skills.slice(0, 3).map((s, i) => (
                    <span key={i} className="bg-green-50 text-green-700 border border-green-200 px-2 py-0.5 text-[10px] font-semibold">
                      ✓ {s}
                    </span>
                  ))}
                </div>
              </div>
              <div>
                <span className="font-extrabold uppercase text-[9px] text-amber-600 block">Optimizable Opportunities</span>
                <p className="text-[11px] font-medium leading-relaxed mt-0.5 text-navy/80">
                  The ATS pipeline will automatically align your experience in Robotics & ML to highlights in {job.skills.slice(3).join(", ") || "the core specifications"}.
                </p>
              </div>
            </div>
          </div>

          {/* JD description */}
          <div className="space-y-3 font-sans">
            <h3 className="text-xs font-black uppercase text-frenchgray tracking-wider">Job Specification</h3>
            <p className="text-xs font-semibold leading-loose text-navy bg-white p-4 border-2 border-navy select-text whitespace-pre-line">
              {job.description}
            </p>
          </div>

          {/* Skills checklist */}
          <div className="mt-6 space-y-2 font-sans">
            <h3 className="text-xs font-black uppercase text-frenchgray tracking-wider">Key Target Competencies</h3>
            <div className="flex flex-wrap gap-1.5">
              {job.skills.map((skill, index) => (
                <span key={index} className="bg-frenchgray/15 text-navy border border-navy/30 text-[10px] font-black px-2.5 py-1">
                  {skill}
                </span>
              ))}
            </div>
          </div>
        </div>

        <div className="p-6 bg-white border-t-4 border-navy flex items-center justify-end gap-3 font-sans">
          <button
            onClick={onClose}
            className="bg-white hover:bg-frenchgray/10 text-navy font-black text-xs uppercase px-4 py-2 border-3 border-navy cursor-pointer transition-all"
          >
            Close
          </button>
          <button
            onClick={() => onApply(job.id)}
            disabled={applyingJobId !== null}
            className="bg-vibrantred hover:bg-engorange disabled:bg-frenchgray text-antiwhite text-xs font-black uppercase px-6 py-2.5 border-3 border-navy shadow-[3px_3px_0px_0px_rgba(43,45,66,1)] hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-none transition-all cursor-pointer"
          >
            {applyingJobId === job.id ? "Optimizing..." : "Apply & Optimize Resume"}
          </button>
        </div>
      </div>
    </>
  );
};
