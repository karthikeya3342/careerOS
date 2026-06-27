import React from "react";

export interface MarkdownSection {
  title: string;
  content: string;
}

// Splits the Hindsight candidate profile markdown by its headers into separate card sections
export function splitProfileMarkdown(md: string): MarkdownSection[] {
  if (!md) return [];
  const sections: MarkdownSection[] = [];
  const lines = md.split("\n");
  let currentSection: MarkdownSection = { title: "Overview", content: "" };
  
  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith("## ") || trimmed.startsWith("# ") || (trimmed.startsWith("### ") && currentSection.title === "Overview")) {
      if (currentSection.content.trim() || currentSection.title !== "Overview") {
        sections.push({
          title: currentSection.title,
          content: currentSection.content.trim()
        });
      }
      currentSection = {
        title: trimmed.replace(/^#+\s+/, "").trim(),
        content: ""
      };
    } else {
      currentSection.content += line + "\n";
    }
  }
  
  if (currentSection.content.trim() || currentSection.title !== "Overview") {
    sections.push({
      title: currentSection.title,
      content: currentSection.content.trim()
    });
  }
  
  return sections;
}

// Helper to render bold text and format lines from raw text inputs
export function parseBoldText(text: string) {
  if (!text) return "";
  const parts = text.split(/\*\*(.*?)\*\*/g);
  return parts.map((part, index) => {
    // Every odd index is a bold text match
    if (index % 2 === 1) {
      return <strong key={index} className="font-extrabold text-navy">{part}</strong>;
    }
    return part;
  });
}

// Component to dynamically format and render Markdown documents in the UI
export const RenderMarkdown = ({ text }: { text: string }) => {
  if (!text) return null;
  
  // Clean LaTeX symbols
  const cleanedText = text
    .replace(/\$\\rightarrow\$/g, "→")
    .replace(/\$\\leftarrow\$/g, "←")
    .replace(/\\rightarrow/g, "→")
    .replace(/\\leftarrow/g, "←")
    .replace(/\$\$/g, "");

  const lines = cleanedText.split("\n");
  return (
    <div className="space-y-3 select-text font-sans">
      {lines.map((line, i) => {
        const trimmed = line.trim();
        if (!trimmed) return <div key={i} className="h-1" />;
        
        // Check indentation level for nested lists
        const leadingSpaces = line.match(/^\s*/)?.[0].length || 0;
        const isNested = leadingSpaces >= 2;
        
        // Headers
        if (trimmed.startsWith("### ")) {
          return (
            <h4 key={i} className="text-xs font-black uppercase text-navy border-b border-navy/15 pb-1 mt-4 mb-2">
              {trimmed.substring(4)}
            </h4>
          );
        }
        if (trimmed.startsWith("## ")) {
          return (
            <h3 key={i} className="text-sm font-black uppercase text-vibrantred border-b-2 border-navy pb-1 mt-5 mb-3">
              {trimmed.substring(3)}
            </h3>
          );
        }
        if (trimmed.startsWith("# ")) {
          return (
            <h2 key={i} className="text-base font-black uppercase text-navy border-b-4 border-navy pb-1.5 mt-6 mb-4">
              {trimmed.substring(2)}
            </h2>
          );
        }
        
        // Bullets
        if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
          const bulletContent = trimmed.substring(2);
          return (
            <div key={i} className={`flex items-start gap-2.5 text-xs leading-relaxed ${isNested ? "pl-6 text-navy/80" : "pl-2"}`}>
              <span className="text-vibrantred mt-1 shrink-0">{isNested ? "◦" : "•"}</span>
              <span>{parseBoldText(bulletContent)}</span>
            </div>
          );
        }

        // Ordered lists
        const olMatch = trimmed.match(/^(\d+)\.\s+(.*)/);
        if (olMatch) {
          return (
            <div key={i} className="flex items-start gap-2 text-xs leading-relaxed pl-2">
              <span className="text-vibrantred font-bold shrink-0">{olMatch[1]}.</span>
              <span>{parseBoldText(olMatch[2])}</span>
            </div>
          );
        }

        // Standard text line
        return (
          <p key={i} className={`text-xs leading-loose text-navy/90 ${isNested ? "pl-6" : ""}`}>
            {parseBoldText(trimmed)}
          </p>
        );
      })}
    </div>
  );
};
