"use client";

import React from "react";
import {
  Radar,
  Sparkles,
  TrendingUp,
  CheckCircle2,
  Clock,
  Send,
  MessageSquareCode,
  Zap,
} from "lucide-react";

interface KPIGridProps {
  kpiData?: {
    jobs_scanned: number;
    new_jobs: number;
    strong_matches: number;
    high_opportunity: number;
    pending_approval: number;
    applied: number;
    interview: number;
    rejected: number;
    response_rate_percent: number;
  };
}

export const KPIGrid: React.FC<KPIGridProps> = ({ kpiData }) => {
  const data = kpiData || {
    jobs_scanned: 184,
    new_jobs: 14,
    strong_matches: 8,
    high_opportunity: 11,
    pending_approval: 3,
    applied: 6,
    interview: 2,
    rejected: 1,
    response_rate_percent: 33.3,
  };

  const cards = [
    {
      title: "Jobs Scanned",
      value: data.jobs_scanned,
      subtext: `+${data.new_jobs} unique new today`,
      icon: Radar,
      color: "cyan",
      glowClass: "hover:border-cyan-500/50 hover:shadow-cyan-500/10",
      textColor: "text-cyan-400",
    },
    {
      title: "Strong Matches",
      value: data.strong_matches,
      subtext: "Match Score >= 85%",
      icon: Sparkles,
      color: "emerald",
      glowClass: "hover:border-emerald-500/50 hover:shadow-emerald-500/10",
      textColor: "text-emerald-400",
    },
    {
      title: "High Opportunity",
      value: data.high_opportunity,
      subtext: "Visa / FX / Remote Signals",
      icon: Zap,
      color: "amber",
      glowClass: "hover:border-amber-500/50 hover:shadow-amber-500/10",
      textColor: "text-amber-400",
    },
    {
      title: "Pending Approval",
      value: data.pending_approval,
      subtext: "Tri-state review queue",
      icon: Clock,
      color: "purple",
      glowClass: "hover:border-purple-500/50 hover:shadow-purple-500/10",
      textColor: "text-purple-400",
    },
    {
      title: "Submitted Applications",
      value: data.applied,
      subtext: "Tracked via Gmail label",
      icon: Send,
      color: "blue",
      glowClass: "hover:border-blue-500/50 hover:shadow-blue-500/10",
      textColor: "text-blue-400",
    },
    {
      title: "Interview Invites",
      value: data.interview,
      subtext: "AI classified from inbox",
      icon: MessageSquareCode,
      color: "emerald",
      glowClass: "hover:border-emerald-500/50 hover:shadow-emerald-500/10",
      textColor: "text-emerald-300",
    },
    {
      title: "Response Rate",
      value: `${data.response_rate_percent}%`,
      subtext: "Industry benchmark: 3-5%",
      icon: TrendingUp,
      color: "cyan",
      glowClass: "hover:border-cyan-500/50 hover:shadow-cyan-500/10",
      textColor: "text-cyan-300",
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3.5 w-full">
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <div
            key={idx}
            className={`glass-panel p-4 rounded-2xl flex flex-col justify-between transition-all duration-300 ${card.glowClass} group cursor-default`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-mono uppercase tracking-wider text-gray-400">
                {card.title}
              </span>
              <Icon className={`w-4 h-4 ${card.textColor} opacity-75 group-hover:scale-110 transition-transform`} />
            </div>
            <div>
              <div className={`text-2xl font-heading font-bold ${card.textColor} tracking-tight`}>
                {card.value}
              </div>
              <div className="text-[10px] text-gray-400 mt-1 font-mono">
                {card.subtext}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};
