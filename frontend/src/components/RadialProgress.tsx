import React from "react";

export const RadialProgress = ({ score, size = 44, strokeWidth = 4 }: { score: number; size?: number; strokeWidth?: number }) => {
  const radius = (size - strokeWidth * 2) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (score / 100) * circumference;
  
  let color = "stroke-vibrantred";
  if (score >= 85) color = "stroke-green-600";
  else if (score >= 70) color = "stroke-amber-500";

  return (
    <div className="relative flex items-center justify-center shrink-0">
      <svg width={size} height={size} className="radial-progress-ring">
        <circle
          className="stroke-frenchgray/20"
          fill="transparent"
          strokeWidth={strokeWidth}
          r={radius}
          cx={size / 2}
          cy={size / 2}
        />
        <circle
          className={`${color} transition-all duration-500`}
          fill="transparent"
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          r={radius}
          cx={size / 2}
          cy={size / 2}
        />
      </svg>
      <span className="absolute text-[10px] font-black text-navy">{Math.round(score)}%</span>
    </div>
  );
};
