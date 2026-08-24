"use client";

import React, { useState } from "react";
import {
  Search,
  Filter,
  Sparkles,
  Zap,
  MapPin,
  Building2,
  DollarSign,
  Globe2,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  ChevronRight,
  Send,
  FileText,
  Sliders,
} from "lucide-react";

export interface JobItem {
  id: string;
  title: string;
  employer: string;
  location: string;
  work_mode: string;
  salary_min?: number | null;
  salary_max?: number | null;
  currency?: string | null;
  canonical_url: string;
  description: string;
  features?: {
    skills_json: string[];
    visa_signal: string;
    remote_signal: string;
    industry?: string;
  };
  match?: {
    match_score: number;
    opportunity_score: number;
    explanation_json: {
      match_reasons?: string[];
      matched_skills?: string[];
      missing_skills?: string[];
      match_breakdown?: Record<string, number>;
      opportunity_breakdown?: Record<string, number>;
    };
    gaps_json: string[];
  };
}

interface JobFeedViewProps {
  jobs: JobItem[];
  onSelectJobForPackage: (job: JobItem) => void;
}

export const JobFeedView: React.FC<JobFeedViewProps> = ({
  jobs,
  onSelectJobForPackage,
}) => {
  const [searchQuery, setSearchQuery] = useState("");
  const [minMatchFilter, setMinMatchFilter] = useState<number>(0);
  const [minOppFilter, setMinOppFilter] = useState<number>(0);
  const [selectedLocation, setSelectedLocation] = useState<string>("all");
  const [selectedJob, setSelectedJob] = useState<JobItem | null>(null);

  const filteredJobs = jobs.filter((job) => {
    const q = searchQuery.toLowerCase();
    const matchesQuery =
      !q ||
      job.title.toLowerCase().includes(q) ||
      job.employer.toLowerCase().includes(q) ||
      job.description.toLowerCase().includes(q);

    const mScore = job.match?.match_score || 0;
    const oppScore = job.match?.opportunity_score || 0;

    const matchesScore = mScore >= minMatchFilter && oppScore >= minOppFilter;

    const matchesLoc =
      selectedLocation === "all" ||
      (selectedLocation === "nigeria" && (job.location.toLowerCase().includes("nigeria") || job.location.toLowerCase().includes("abuja") || job.location.toLowerCase().includes("lagos"))) ||
      (selectedLocation === "remote" && (job.work_mode.toLowerCase().includes("remote") || job.location.toLowerCase().includes("remote"))) ||
      (selectedLocation === "international" && !job.location.toLowerCase().includes("nigeria"));

    return matchesQuery && matchesScore && matchesLoc;
  });

  return (
    <div className="space-y-6">
      {/* ─── Search & Advanced Filter Bar ─── */}
      <div className="glass-panel p-4 rounded-2xl flex flex-col md:flex-row gap-4 items-center justify-between">
        <div className="relative w-full md:w-96">
          <Search className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search roles, skills (e.g. Azure, Cybersecurity, ICT)..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-white/5 border border-white/10 rounded-xl pl-10 pr-4 py-2.5 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500/60 transition-colors"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2.5 w-full md:w-auto">
          {/* Match Score Filter */}
          <div className="flex items-center space-x-1 bg-white/5 border border-white/10 rounded-xl p-1 text-xs">
            <span className="text-gray-400 px-2 text-[11px] font-mono">Match:</span>
            {[0, 80, 90, 95].map((score) => (
              <button
                key={score}
                onClick={() => setMinMatchFilter(score)}
                className={`px-2.5 py-1 rounded-lg text-xs font-mono transition-all ${
                  minMatchFilter === score
                    ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-bold"
                    : "text-gray-400 hover:text-gray-200"
                }`}
              >
                {score === 0 ? "All" : `>=${score}%`}
              </button>
            ))}
          </div>

          {/* Location Filter */}
          <div className="flex items-center space-x-1 bg-white/5 border border-white/10 rounded-xl p-1 text-xs">
            {[
              { id: "all", label: "All Geographies" },
              { id: "nigeria", label: "Nigeria" },
              { id: "remote", label: "Remote" },
              { id: "international", label: "International / NGO" },
            ].map((loc) => (
              <button
                key={loc.id}
                onClick={() => setSelectedLocation(loc.id)}
                className={`px-2.5 py-1 rounded-lg text-xs transition-all ${
                  selectedLocation === loc.id
                    ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-semibold"
                    : "text-gray-400 hover:text-gray-200"
                }`}
              >
                {loc.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ─── Job List & Split Detail Drawer ─── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Job Cards */}
        <div className={`space-y-3.5 ${selectedJob ? "lg:col-span-6" : "lg:col-span-12"}`}>
          <div className="flex items-center justify-between text-xs font-mono text-gray-400 px-1">
            <span>Showing {filteredJobs.length} Ranked Positions</span>
            <span>Sorted by Dual Weighted Intelligence</span>
          </div>

          {filteredJobs.map((job) => {
            const mScore = job.match?.match_score || 88;
            const oppScore = job.match?.opportunity_score || 92;
            const isSelected = selectedJob?.id === job.id;
            const visaSignal = job.features?.visa_signal || "unknown";

            return (
              <div
                key={job.id}
                onClick={() => setSelectedJob(job)}
                className={`glass-panel p-5 rounded-2xl cursor-pointer transition-all duration-300 ${
                  isSelected
                    ? "border-cyan-500/60 bg-cyan-950/20 shadow-lg shadow-cyan-500/10"
                    : "hover:border-white/20 hover:scale-[1.008]"
                }`}
              >
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center space-x-2">
                      <h3 className="font-heading font-bold text-base text-white hover:text-cyan-300 transition-colors">
                        {job.title}
                      </h3>
                      {job.work_mode === "remote" && (
                        <span className="px-2 py-0.5 text-[10px] uppercase font-mono font-bold tracking-wider bg-purple-500/15 text-purple-300 border border-purple-500/30 rounded-md">
                          Remote
                        </span>
                      )}
                    </div>

                    <div className="flex flex-wrap items-center gap-3 text-xs text-gray-400 mt-2 font-mono">
                      <div className="flex items-center space-x-1">
                        <Building2 className="w-3.5 h-3.5 text-gray-500" />
                        <span className="text-gray-200">{job.employer}</span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <MapPin className="w-3.5 h-3.5 text-gray-500" />
                        <span>{job.location}</span>
                      </div>
                      {job.salary_max && (
                        <div className="flex items-center space-x-1 text-emerald-400 font-semibold">
                          <DollarSign className="w-3.5 h-3.5" />
                          <span>
                            {job.currency} {job.salary_min?.toLocaleString()} - {job.salary_max?.toLocaleString()}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Dual Score Badges */}
                  <div className="flex sm:flex-col items-center sm:items-end gap-2 shrink-0">
                    <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-xl bg-emerald-500/15 border border-emerald-500/30">
                      <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
                      <span className="text-xs font-mono font-bold text-emerald-400">
                        {mScore}% Match
                      </span>
                    </div>
                    <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-xl bg-amber-500/15 border border-amber-500/30">
                      <Zap className="w-3.5 h-3.5 text-amber-400" />
                      <span className="text-xs font-mono font-bold text-amber-400">
                        {oppScore}% Opp
                      </span>
                    </div>
                  </div>
                </div>

                {/* Match Reasons & Signal Tags */}
                <div className="mt-3.5 pt-3 border-t border-white/5 flex flex-wrap items-center justify-between gap-2">
                  <div className="flex flex-wrap gap-1.5">
                    {job.features?.skills_json?.slice(0, 3).map((s, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-0.5 rounded-md bg-white/5 border border-white/10 text-[11px] text-gray-300 font-mono"
                      >
                        {s}
                      </span>
                    ))}
                    {visaSignal === "indicated" && (
                      <span className="px-2 py-0.5 rounded-md bg-amber-500/10 border border-amber-500/30 text-[11px] text-amber-400 font-mono">
                        ✦ Visa Sponsorship Indicated
                      </span>
                    )}
                  </div>

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelectJobForPackage(job);
                    }}
                    className="glass-button-primary px-3 py-1.5 rounded-lg text-xs font-medium text-white flex items-center space-x-1.5 cursor-pointer ml-auto"
                  >
                    <Send className="w-3 h-3" />
                    <span>Prepare Package</span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {/* Right Column: Recruitment Intelligence Report Drawer */}
        {selectedJob && (
          <div className="lg:col-span-6 glass-panel-glow p-6 rounded-2xl space-y-5 sticky top-24 max-h-[85vh] overflow-y-auto">
            <div className="flex items-start justify-between pb-3 border-b border-white/10">
              <div>
                <span className="text-[10px] font-mono uppercase tracking-widest text-cyan-400 font-bold">
                  Intelligence Dossier
                </span>
                <h2 className="text-xl font-heading font-bold text-white mt-1">
                  {selectedJob.title}
                </h2>
                <p className="text-xs text-gray-300 mt-0.5">
                  {selectedJob.employer} • {selectedJob.location}
                </p>
              </div>
              <button
                onClick={() => setSelectedJob(null)}
                className="text-gray-400 hover:text-white text-xs px-2 py-1 bg-white/5 rounded-lg"
              >
                Close ✕
              </button>
            </div>

            {/* Score Breakdown Analysis */}
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/25">
                <div className="text-[11px] font-mono uppercase text-emerald-400 font-bold">
                  Match Score
                </div>
                <div className="text-3xl font-heading font-bold text-white mt-1">
                  {selectedJob.match?.match_score || 94}%
                </div>
                <p className="text-[10px] text-emerald-300 mt-1">
                  Strong candidate skill & infrastructure grounding
                </p>
              </div>

              <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/25">
                <div className="text-[11px] font-mono uppercase text-amber-400 font-bold">
                  Opportunity Score
                </div>
                <div className="text-3xl font-heading font-bold text-white mt-1">
                  {selectedJob.match?.opportunity_score || 97}%
                </div>
                <p className="text-[10px] text-amber-300 mt-1">
                  High relocation/compensation desirability
                </p>
              </div>
            </div>

            {/* Verified Strengths */}
            <div>
              <h4 className="text-xs font-mono uppercase tracking-wider text-cyan-400 font-bold mb-2">
                Grounding & Match Factors
              </h4>
              <div className="space-y-1.5">
                {selectedJob.match?.explanation_json?.match_reasons?.map((reason, idx) => (
                  <div key={idx} className="flex items-center space-x-2 text-xs text-gray-200">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                    <span>{reason}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Skill Gaps (if any) */}
            {selectedJob.match?.gaps_json && selectedJob.match.gaps_json.length > 0 && (
              <div>
                <h4 className="text-xs font-mono uppercase tracking-wider text-orange-400 font-bold mb-2">
                  Potential Evidence Gaps
                </h4>
                <div className="space-y-1.5">
                  {selectedJob.match.gaps_json.map((gap, idx) => (
                    <div key={idx} className="flex items-center space-x-2 text-xs text-gray-300">
                      <AlertCircle className="w-3.5 h-3.5 text-orange-400 shrink-0" />
                      <span>{gap}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Full Normalized Job Description */}
            <div>
              <h4 className="text-xs font-mono uppercase tracking-wider text-gray-400 font-bold mb-1.5">
                Job Overview
              </h4>
              <p className="text-xs text-gray-300 leading-relaxed bg-white/5 p-3.5 rounded-xl border border-white/10">
                {selectedJob.description}
              </p>
            </div>

            {/* Actions */}
            <div className="flex items-center space-x-3 pt-2">
              <button
                onClick={() => onSelectJobForPackage(selectedJob)}
                className="w-full glass-button-primary py-3 rounded-xl text-xs font-semibold text-white flex items-center justify-center space-x-2 cursor-pointer shadow-lg"
              >
                <Sparkles className="w-4 h-4 text-cyan-300" />
                <span>Generate Application Package</span>
              </button>
              <a
                href={selectedJob.canonical_url}
                target="_blank"
                rel="noreferrer"
                className="glass-button p-3 rounded-xl text-gray-300 hover:text-white"
              >
                <ExternalLink className="w-4 h-4" />
              </a>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
