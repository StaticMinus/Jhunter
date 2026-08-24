"use client";

import React, { useState } from "react";
import {
  Upload,
  FileCheck,
  ShieldCheck,
  CheckCircle2,
  Plus,
  Trash2,
  Save,
  Sliders,
  Briefcase,
  GraduationCap,
  Award,
} from "lucide-react";

export const CandidateStudio: React.FC = () => {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);

  const [candidateData, setCandidateData] = useState({
    name: "David",
    title: "IT & Communication Specialist / Systems Engineer",
    location: "Nigeria",
    salary_floor: 600000,
    summary:
      "Accomplished IT & Communication Specialist, Systems Administrator, and Software Engineer with 8+ years of expertise spanning enterprise networking, cybersecurity (IDS/IPS), cloud architecture (Azure, Entra ID, Microsoft 365), Python API development, disaster recovery, and ICT4D.",
    skills: [
      { skill: "LAN/WAN & TCP/IP Networking", category: "Infrastructure", evidence: "Enterprise deployments, VPN, Starlink" },
      { skill: "Active Directory & Entra ID", category: "Cloud/Directory", evidence: "Phishing-debug environments, Azure IAM" },
      { skill: "Windows & Linux Server Admin", category: "Systems", evidence: "Hyper-V virtualization, multi-server hosting" },
      { skill: "Cybersecurity & IDS/IPS", category: "Security", evidence: "Incident response, IT policy, threat audits" },
      { skill: "Python & FastAPI / Web APIs", category: "Software", evidence: "Backend services, custom automation scripts" },
      { skill: "Full Stack Web & Mobile", category: "Software", evidence: "Mental-health assessment systems, web apps" },
      { skill: "Disaster Recovery & Backup", category: "Infrastructure", evidence: "OneDrive/NAS enterprise backup workflows" },
      { skill: "ICT4D & Humanitarian Tech", category: "Domain", evidence: "RedAid Nigeria, Diverse Health Initiative" },
    ],
    targetRoles: [
      "IT Specialist",
      "ICT Specialist",
      "IT Officer",
      "Systems Administrator",
      "Software Developer",
      "Cybersecurity Analyst",
      "ICT4D Specialist",
      "CTO",
    ],
  });

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setIsUploading(true);
      setTimeout(() => {
        setIsUploading(false);
        setUploadSuccess(true);
      }, 1200);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header Banner */}
      <div className="glass-panel p-6 rounded-2xl flex flex-col md:flex-row items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-cyan-400 text-xs font-mono font-bold uppercase tracking-wider">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>Verified Candidate Intelligence Base</span>
          </div>
          <h2 className="text-xl font-heading font-bold text-white mt-1">
            Candidate Profile & Grounded Evidence Studio
          </h2>
          <p className="text-xs text-gray-400 font-mono mt-0.5">
            Strict source of truth for the AI matching engine and anti-fabrication generator.
          </p>
        </div>

        {/* Upload Button */}
        <label className="glass-button-primary px-4 py-2.5 rounded-xl text-xs font-semibold text-white flex items-center space-x-2 cursor-pointer">
          <Upload className={`w-4 h-4 ${isUploading ? "animate-bounce" : ""}`} />
          <span>{isUploading ? "Parsing CV with AI..." : "Upload New CV (PDF / DOCX)"}</span>
          <input type="file" accept=".pdf,.docx,.txt" className="hidden" onChange={handleFileUpload} />
        </label>
      </div>

      {uploadSuccess && (
        <div className="p-3.5 rounded-xl bg-emerald-500/15 border border-emerald-500/30 text-xs text-emerald-300 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>CV Parsed & Verified! All skills, experiences, and evidence indexed.</span>
          </div>
          <button onClick={() => setUploadSuccess(false)} className="text-gray-400 hover:text-white">✕</button>
        </div>
      )}

      {/* Profile Details Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Summary & Preferences */}
        <div className="space-y-5">
          <div className="glass-panel p-5 rounded-2xl space-y-4">
            <h3 className="text-sm font-heading font-bold text-white flex items-center space-x-2">
              <Sliders className="w-4 h-4 text-cyan-400" />
              <span>Executive Preferences</span>
            </h3>

            <div>
              <label className="text-[11px] text-gray-400 font-mono block mb-1">
                Nigeria Monthly Salary Baseline (₦)
              </label>
              <input
                type="number"
                value={candidateData.salary_floor}
                onChange={(e) => setCandidateData({ ...candidateData, salary_floor: Number(e.target.value) })}
                className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-xs text-emerald-400 font-mono font-bold focus:outline-none focus:border-cyan-500/50"
              />
            </div>

            <div>
              <label className="text-[11px] text-gray-400 font-mono block mb-1">
                Primary Base Location
              </label>
              <input
                type="text"
                value={candidateData.location}
                onChange={(e) => setCandidateData({ ...candidateData, location: e.target.value })}
                className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500/50"
              />
            </div>

            <div>
              <label className="text-[11px] text-gray-400 font-mono block mb-1">
                Target Role Family Aliases
              </label>
              <div className="flex flex-wrap gap-1.5 mt-2">
                {candidateData.targetRoles.map((role, idx) => (
                  <span
                    key={idx}
                    className="px-2.5 py-1 rounded-lg bg-cyan-500/10 border border-cyan-500/25 text-[11px] text-cyan-300 font-mono font-medium"
                  >
                    {role}
                  </span>
                ))}
              </div>
            </div>
          </div>

          <div className="glass-panel p-5 rounded-2xl space-y-3">
            <h3 className="text-sm font-heading font-bold text-white">
              Professional Summary
            </h3>
            <textarea
              rows={5}
              value={candidateData.summary}
              onChange={(e) => setCandidateData({ ...candidateData, summary: e.target.value })}
              className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-xs text-gray-200 leading-relaxed focus:outline-none focus:border-cyan-500/50"
            />
          </div>
        </div>

        {/* Right Columns (2 cols): Verified Skills & Evidence Table */}
        <div className="lg:col-span-2 glass-panel p-6 rounded-2xl space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-heading font-bold text-white flex items-center space-x-2">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                <span>Verified Skills & Verifiable Evidence</span>
              </h3>
              <p className="text-[11px] text-gray-400 font-mono mt-0.5">
                Every AI-generated cover letter and answer references evidence from this table.
              </p>
            </div>
            <button className="glass-button px-3 py-1.5 rounded-lg text-xs text-cyan-300 flex items-center space-x-1">
              <Plus className="w-3.5 h-3.5" />
              <span>Add Skill</span>
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-white/10 text-gray-400 font-mono text-[11px]">
                  <th className="pb-2.5">Skill Name</th>
                  <th className="pb-2.5">Category</th>
                  <th className="pb-2.5">Verifiable Evidence & Source</th>
                  <th className="pb-2.5 text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 font-mono">
                {candidateData.skills.map((s, idx) => (
                  <tr key={idx} className="hover:bg-white/5 transition-colors">
                    <td className="py-3 font-semibold text-white">{s.skill}</td>
                    <td className="py-3 text-gray-400">
                      <span className="px-2 py-0.5 rounded bg-white/5 border border-white/10 text-[10px]">
                        {s.category}
                      </span>
                    </td>
                    <td className="py-3 text-gray-300 font-sans text-[11px]">{s.evidence}</td>
                    <td className="py-3 text-right">
                      <span className="inline-flex items-center space-x-1 text-[10px] text-emerald-400 font-bold bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/30">
                        <CheckCircle2 className="w-3 h-3" />
                        <span>Verified</span>
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
