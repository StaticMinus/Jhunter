"use client";

import React, { useState } from "react";
import { ExecutiveHeader } from "@/components/dashboard/ExecutiveHeader";
import { KPIGrid } from "@/components/dashboard/KPIGrid";
import { ThreeRadarGlobe } from "@/components/canvas/ThreeRadarGlobe";
import { JobFeedView, JobItem } from "@/components/jobs/JobFeedView";
import { KanbanPipeline, ApplicationItem } from "@/components/pipeline/KanbanPipeline";
import { CandidateStudio } from "@/components/profile/CandidateStudio";
import { DocumentStudio } from "@/components/documents/DocumentStudio";
import { IntegrationsHub } from "@/components/integrations/IntegrationsHub";
import {
  Sparkles,
  Zap,
  ShieldCheck,
  Send,
  Building2,
  MapPin,
  ExternalLink,
  ArrowRight,
  TrendingUp,
} from "lucide-react";

const DEMO_JOBS: JobItem[] = [
  {
    id: "job-1",
    title: "ICT Specialist & Systems Administrator",
    employer: "International Humanitarian Health Org",
    location: "Abuja, Nigeria",
    work_mode: "hybrid",
    salary_min: 750000,
    salary_max: 950000,
    currency: "NGN",
    canonical_url: "https://reliefweb.int/job/ict-specialist-abuja",
    description:
      "Seeking a senior ICT Specialist to manage regional infrastructure, secure VPN tunnels, Starlink satellite connectivity, Active Directory, server virtualization, and disaster recovery backup systems for healthcare response teams in Nigeria.",
    features: {
      skills_json: ["LAN/WAN & TCP/IP", "Active Directory", "Linux & Windows Admin", "Cybersecurity & IDS/IPS", "Disaster Recovery", "ICT4D"],
      visa_signal: "indicated",
      remote_signal: "hybrid",
      industry: "NGO / Humanitarian Health",
    },
    match: {
      match_score: 94,
      opportunity_score: 97,
      explanation_json: {
        match_reasons: [
          "Humanitarian ICT & telecommunications experience directly aligned",
          "Strong match: Active Directory, Starlink, IDS/IPS, and disaster recovery",
          "Full salary baseline satisfaction (₦750k–₦950k/mo vs ₦600k baseline)",
          "Visa/relocation support officially indicated",
        ],
        matched_skills: ["LAN/WAN & TCP/IP", "Active Directory", "Cybersecurity & IDS/IPS", "Disaster Recovery"],
        missing_skills: ["ITIL certification (Not evidenced in CV)"],
      },
      gaps_json: ["ITIL certification not found in CV"],
    },
  },
  {
    id: "job-2",
    title: "Senior Python & Cloud Infrastructure Engineer",
    employer: "Fintech Global Solutions",
    location: "Worldwide / Remote",
    work_mode: "remote",
    salary_min: 6500,
    salary_max: 8500,
    currency: "USD",
    canonical_url: "https://remoteok.com/remote-jobs/senior-python-infra-engineer",
    description:
      "Lead Python backend architecture, high-throughput REST APIs, Azure cloud integration, security incident response, and containerized microservices. 100% remote with international relocation sponsorship potential.",
    features: {
      skills_json: ["Python & FastAPI", "Azure & Entra ID", "Linux Administration", "Cybersecurity", "Full Stack Web"],
      visa_signal: "possible",
      remote_signal: "full_remote",
      industry: "Fintech / Cloud Infrastructure",
    },
    match: {
      match_score: 91,
      opportunity_score: 95,
      explanation_json: {
        match_reasons: [
          "Python backend & Azure security API background matches core stack",
          "100% Remote flexibility with USD FX compensation tier ($6,500 - $8,500/mo)",
          "Senior technical leadership / CTO background recognized",
        ],
        matched_skills: ["Python & FastAPI", "Azure & Entra ID", "Cybersecurity"],
        missing_skills: ["Kubernetes operator deployment"],
      },
      gaps_json: ["Kubernetes experience not explicitly evidenced"],
    },
  },
  {
    id: "job-3",
    title: "ICT4D Technology & Digital Transformation Lead",
    employer: "United Nations / International NGO Consortium",
    location: "Geneva / Amsterdam / Remote",
    work_mode: "remote",
    salary_min: 7000,
    salary_max: 9000,
    currency: "EUR",
    canonical_url: "https://reliefweb.int/job/ict4d-technology-digital-lead",
    description:
      "Lead global digital technology strategy, mobile assessment tools, telehealth integrations, humanitarian IT compliance, and stakeholder technical mentoring across country offices.",
    features: {
      skills_json: ["ICT4D & Humanitarian Tech", "Python & API Development", "Cybersecurity & IDS/IPS", "Communications", "LAN/WAN Networking"],
      visa_signal: "indicated",
      remote_signal: "full_remote",
      industry: "International Development / UN",
    },
    match: {
      match_score: 89,
      opportunity_score: 98,
      explanation_json: {
        match_reasons: [
          "Direct match with RedAid and Diverse Health Initiative ICT4D experience",
          "Highest tier opportunity with European headquarters relocation sponsorship",
          "Executive communication and documentary background aligned",
        ],
        matched_skills: ["ICT4D", "Python & APIs", "Cybersecurity", "Communications"],
        missing_skills: [],
      },
      gaps_json: [],
    },
  },
  {
    id: "job-4",
    title: "Enterprise Cybersecurity & Network Engineer",
    employer: "West African Telecoms Group",
    location: "Lagos, Nigeria",
    work_mode: "hybrid",
    salary_min: 800000,
    salary_max: 1100000,
    currency: "NGN",
    canonical_url: "https://hotnigerianjobs.com/jobs/enterprise-cybersecurity-engineer",
    description:
      "Responsible for core telecommunication network security, IDS/IPS hardening, multi-site failover disaster recovery, and SOC monitoring across enterprise infrastructure.",
    features: {
      skills_json: ["Cybersecurity & IDS/IPS", "LAN/WAN & TCP/IP", "Active Directory", "Disaster Recovery"],
      visa_signal: "no_indication",
      remote_signal: "hybrid",
      industry: "Telecommunications & Enterprise IT",
    },
    match: {
      match_score: 88,
      opportunity_score: 86,
      explanation_json: {
        match_reasons: [
          "Extensive telecom & enterprise network routing background verified",
          "High compensation (₦800,000 - ₦1,100,000/mo)",
        ],
        matched_skills: ["Cybersecurity & IDS/IPS", "LAN/WAN", "Disaster Recovery"],
        missing_skills: ["CheckPoint firewall certification"],
      },
      gaps_json: ["CheckPoint firewall certification not found"],
    },
  },
];

const DEMO_APPLICATIONS: ApplicationItem[] = [
  {
    id: "app-1",
    job_id: "job-1",
    title: "ICT Specialist & Systems Administrator",
    employer: "International Humanitarian Health Org",
    location: "Abuja, Nigeria",
    status: "PENDING_APPROVAL",
    approval_state: "REVIEW",
    match_score: 94,
    opportunity_score: 97,
    applied_at: null,
    method: "email",
  },
  {
    id: "app-2",
    job_id: "job-2",
    title: "Senior Python & Cloud Infrastructure Engineer",
    employer: "Fintech Global Solutions",
    location: "Worldwide / Remote",
    status: "APPLIED",
    approval_state: "AUTO",
    match_score: 91,
    opportunity_score: 95,
    applied_at: "2026-08-24T12:30:00Z",
    method: "email",
  },
  {
    id: "app-3",
    job_id: "job-3",
    title: "ICT4D Technology & Digital Transformation Lead",
    employer: "United Nations / International NGO Consortium",
    location: "Geneva / Amsterdam / Remote",
    status: "INTERVIEW",
    approval_state: "AUTO",
    match_score: 89,
    opportunity_score: 98,
    applied_at: "2026-08-22T09:15:00Z",
    method: "email",
  },
];

export default function HomePage() {
  const [activeTab, setActiveTab] = useState<string>("dashboard");
  const [isScanning, setIsScanning] = useState(false);
  const [applications, setApplications] = useState<ApplicationItem[]>(DEMO_APPLICATIONS);
  const [jobs, setJobs] = useState<JobItem[]>(DEMO_JOBS);

  const handleTriggerScan = () => {
    setIsScanning(true);
    setTimeout(() => {
      setIsScanning(false);
    }, 1500);
  };

  const handleSelectJobForPackage = (job: JobItem) => {
    // Switch to Document Studio tab
    setActiveTab("documents");
  };

  const handleApproveApplication = (id: string) => {
    setApplications((prev) =>
      prev.map((a) => (a.id === id ? { ...a, status: "APPLIED", applied_at: new Date().toISOString() } : a))
    );
  };

  const handleRejectApplication = (id: string) => {
    setApplications((prev) =>
      prev.map((a) => (a.id === id ? { ...a, status: "ARCHIVED", approval_state: "SKIP" } : a))
    );
  };

  return (
    <main className="flex-1 flex flex-col">
      {/* Executive Header */}
      <ExecutiveHeader
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onTriggerScan={handleTriggerScan}
        isScanning={isScanning}
      />

      {/* Main Content Area */}
      <div className="flex-1 max-w-7xl w-full mx-auto px-6 py-8 space-y-8">
        {/* ─── TAB 1: EXECUTIVE DASHBOARD ─── */}
        {activeTab === "dashboard" && (
          <div className="space-y-8 animate-in fade-in duration-300">
            {/* Holographic 3D Hero + Signal Banner */}
            <div className="glass-panel-glow p-8 rounded-3xl grid grid-cols-1 lg:grid-cols-12 gap-8 items-center relative overflow-hidden">
              <div className="lg:col-span-8 space-y-4">
                <div className="flex items-center space-x-2">
                  <span className="px-3 py-1 rounded-full text-xs font-mono font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
                    ✦ Executive Intelligence Active
                  </span>
                  <span className="text-xs text-gray-400 font-mono">
                    Candidate: David (Senior IT & Systems Lead)
                  </span>
                </div>

                <h1 className="text-3xl sm:text-4xl font-heading font-extrabold text-white tracking-tight leading-tight">
                  Autonomous Recruitment Engine & Opportunity Radar
                </h1>

                <p className="text-sm text-gray-300 leading-relaxed max-w-2xl">
                  Real-time continuous scanning across Nigerian boards, ReliefWeb humanitarian portals, and global remote networks. Grounded with strict zero-hallucination anti-fabrication rules, automated approval gates, and multi-channel Gmail/Telegram delivery.
                </p>

                <div className="flex flex-wrap items-center gap-3 pt-2">
                  <button
                    onClick={() => setActiveTab("jobs")}
                    className="glass-button-primary px-5 py-2.5 rounded-xl text-xs font-bold text-white flex items-center space-x-2 cursor-pointer"
                  >
                    <Sparkles className="w-4 h-4" />
                    <span>Explore 14 Live Ranked Roles</span>
                    <ArrowRight className="w-3.5 h-3.5 ml-1" />
                  </button>

                  <button
                    onClick={() => setActiveTab("pipeline")}
                    className="glass-button px-5 py-2.5 rounded-xl text-xs font-semibold text-gray-200 flex items-center space-x-2"
                  >
                    <Send className="w-4 h-4 text-cyan-400" />
                    <span>View Application Kanban</span>
                  </button>
                </div>
              </div>

              {/* 3D Holographic Radar Orb */}
              <div className="lg:col-span-4 flex justify-center">
                <ThreeRadarGlobe matchScore={94} opportunityScore={97} />
              </div>
            </div>

            {/* Real-time KPI Metric Telemetry */}
            <KPIGrid />

            {/* High-Signal Top Ranked Opportunities Preview */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-base font-heading font-bold text-white flex items-center space-x-2">
                    <Sparkles className="w-4 h-4 text-emerald-400" />
                    <span>Top Signal Matches (Match &gt;= 85% &amp; Opportunity &gt;= 90%)</span>
                  </h3>
                  <p className="text-xs text-gray-400 font-mono">
                    Highest alignment with your verifiable profile &amp; relocation signals.
                  </p>
                </div>
                <button
                  onClick={() => setActiveTab("jobs")}
                  className="text-xs font-mono text-cyan-400 hover:text-cyan-300 flex items-center space-x-1"
                >
                  <span>View All Positions</span>
                  <ArrowRight className="w-3 h-3" />
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {jobs.slice(0, 2).map((job) => (
                  <div
                    key={job.id}
                    onClick={() => setActiveTab("jobs")}
                    className="glass-panel p-5 rounded-2xl hover:border-cyan-500/50 transition-all cursor-pointer space-y-3"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <h4 className="font-heading font-bold text-sm text-white">
                          {job.title}
                        </h4>
                        <p className="text-xs text-gray-300 flex items-center space-x-1 mt-0.5">
                          <Building2 className="w-3 h-3 text-gray-400" />
                          <span>{job.employer}</span>
                          <span className="text-gray-500">•</span>
                          <span>{job.location}</span>
                        </p>
                      </div>
                      <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-xl bg-emerald-500/15 border border-emerald-500/30 text-xs font-mono font-bold text-emerald-400">
                        <Sparkles className="w-3.5 h-3.5" />
                        <span>{job.match?.match_score}%</span>
                      </div>
                    </div>

                    <p className="text-xs text-gray-300 line-clamp-2">
                      {job.description}
                    </p>

                    <div className="flex items-center justify-between pt-2 border-t border-white/5 text-[11px] font-mono text-gray-400">
                      <span className="text-amber-400">✦ Opportunity: {job.match?.opportunity_score}%</span>
                      <span className="text-cyan-400 flex items-center space-x-1">
                        <span>Inspect Dossier</span>
                        <ArrowRight className="w-3 h-3" />
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ─── TAB 2: OPPORTUNITY RADAR (JOB FEED) ─── */}
        {activeTab === "jobs" && (
          <div className="animate-in fade-in duration-300">
            <JobFeedView
              jobs={jobs}
              onSelectJobForPackage={handleSelectJobForPackage}
            />
          </div>
        )}

        {/* ─── TAB 3: APPLICATION PIPELINE KANBAN ─── */}
        {activeTab === "pipeline" && (
          <div className="animate-in fade-in duration-300">
            <KanbanPipeline
              applications={applications}
              onApprove={handleApproveApplication}
              onReject={handleRejectApplication}
              onViewDetails={() => setActiveTab("documents")}
            />
          </div>
        )}

        {/* ─── TAB 4: CANDIDATE INTELLIGENCE & CV STUDIO ─── */}
        {activeTab === "profile" && (
          <div className="animate-in fade-in duration-300">
            <CandidateStudio />
          </div>
        )}

        {/* ─── TAB 5: DOCUMENT STUDIO ─── */}
        {activeTab === "documents" && (
          <div className="animate-in fade-in duration-300">
            <DocumentStudio />
          </div>
        )}

        {/* ─── TAB 6: INTEGRATIONS & RULES ─── */}
        {activeTab === "integrations" && (
          <div className="animate-in fade-in duration-300">
            <IntegrationsHub />
          </div>
        )}
      </div>
    </main>
  );
}
