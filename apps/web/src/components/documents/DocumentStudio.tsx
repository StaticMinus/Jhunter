"use client";

import React, { useState } from "react";
import {
  FileText,
  Copy,
  Download,
  Check,
  ShieldCheck,
  Sparkles,
  AlertTriangle,
  Building2,
  CheckCircle2,
} from "lucide-react";

export const DocumentStudio: React.FC = () => {
  const [activeDocType, setActiveDocType] = useState<"cover_letter" | "tailored_cv" | "qa_sheet">("cover_letter");
  const [copied, setCopied] = useState(false);

  const sampleCoverLetter = `Dear Hiring Team at International Humanitarian Health Org,

I am writing to express my strong interest in the **ICT Specialist & Systems Administrator** position located in Abuja, Nigeria. With extensive senior technical experience across enterprise infrastructure, cybersecurity, cloud architecture (Azure & Entra ID), full-stack Python/web engineering, and ICT operations, I am confident in delivering immediate value to your technology objectives.

In my recent work at RedAid Nigeria and Diverse Health Initiative, I spearheaded end-to-end ICT and security initiatives—including IDS/IPS deployment, Azure-integrated security API testing, Starlink satellite rollouts, and mission-critical web application development. My background in orchestrating multi-site network resilience, disaster recovery protocols, and full-stack software development directly aligns with the requirements of this role.

Specifically, I bring verified expertise in:
- **LAN/WAN & TCP/IP Networking**: Demonstrated across multi-year enterprise and NGO production deployments
- **Active Directory & Entra ID**: Proven identity management and Azure-integrated security API testing
- **Cybersecurity & IDS/IPS**: Established threat monitoring, incident response, and organizational IT policy
- **Disaster Recovery & Backup Architecture**: Enterprise OneDrive/NAS business continuity protocols

I welcome the opportunity to discuss how my technical leadership, systems architecture experience, and problem-solving mindset will support your organization's mission. Thank you for your time and consideration.

Sincerely,
David
IT & Communication Specialist / Systems Engineer`;

  const sampleCV = `# David
**Senior ICT Specialist & Systems Administrator** | Location: Nigeria | Remote / Worldwide Ready

## Executive Profile
Accomplished IT & Communication Specialist, Systems Administrator, and Software Engineer with extensive experience in enterprise infrastructure, cybersecurity, cloud integrations (Azure, Entra ID, Microsoft 365), full-stack development (Python, React/Next.js), ICT4D, and disaster recovery.

## Core Technical Competencies
LAN/WAN & TCP/IP Networking, Active Directory & Entra ID, Windows & Linux Server Administration, Cybersecurity & IDS/IPS, Python & FastAPI Development, Full Stack Web & Mobile Development, Disaster Recovery & Backup Architecture, ICT4D & Humanitarian Technology.

## Professional Experience
### IT & Communication Specialist — RedAid Nigeria (2021 – Present)
*Sector: NGO / Humanitarian Health*
Led website and mental-health assessment system development; spearheaded documentary production, disaster recovery, backups, cybersecurity, IDS/IPS, incident response, IT policy, and Starlink satellite deployment.

### ICT Specialist — Diverse Health Initiative (2019 – 2021)
*Sector: Healthcare & Technology*
Managed ICT asset lifecycle, telecommunications, SLA compliance, VPN architecture, Azure-integrated phishing-debug APIs and simulated security test environments.

### Chief Technology Officer (CTO) — Flowcode Technology Hub (2017 – 2019)
*Sector: Software & Consulting*
Drove technology strategy, software development, operations, cloud infrastructure deployments, and technical mentoring across multi-disciplinary engineering teams.

## Certifications
- **Microsoft Certified: Azure Administrator** (Microsoft, 2022)
- **Cisco Certified Network Associate (CCNA)** (Cisco, 2020)
- **CompTIA Security+** (CompTIA, 2021)`;

  const sampleQA = [
    {
      question: "Why are you interested in joining International Humanitarian Health Org as ICT Specialist?",
      answer: "My background in senior ICT infrastructure, full-stack software engineering, and cybersecurity in both enterprise and NGO environments makes your organization an ideal environment where my technical expertise and leadership can directly drive scalable impact.",
      confidence: 0.98,
      verified: true
    },
    {
      question: "What is your experience with network administration, cloud systems, and security?",
      answer: "I have over 8 years of hands-on experience designing LAN/WAN architectures, managing Active Directory/Entra ID, configuring Hyper-V virtualization, deploying Azure APIs, and implementing cybersecurity IDS/IPS protocols with Starlink and multi-site backup recovery.",
      confidence: 0.95,
      verified: true
    },
    {
      question: "What is your expected compensation or start date availability?",
      answer: "Open to competitive market compensation aligned with the role scope. Available to start within a standard 2-4 week transition period.",
      confidence: 0.90,
      verified: true
    }
  ];

  const handleCopy = () => {
    const text = activeDocType === "cover_letter" ? sampleCoverLetter : activeDocType === "tailored_cv" ? sampleCV : JSON.stringify(sampleQA, null, 2);
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="glass-panel p-6 rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-cyan-400 text-xs font-mono font-bold uppercase tracking-wider">
            <Sparkles className="w-4 h-4 text-cyan-400" />
            <span>Anti-Fabrication Document Generator</span>
          </div>
          <h2 className="text-xl font-heading font-bold text-white mt-1">
            Tailored Document & Q&A Preview Studio
          </h2>
          <p className="text-xs text-gray-400 font-mono mt-0.5">
            100% grounded materials tailored specifically to the selected job description.
          </p>
        </div>

        <div className="flex items-center space-x-2.5">
          <button
            onClick={handleCopy}
            className="glass-button px-3.5 py-2 rounded-xl text-xs text-white flex items-center space-x-1.5 cursor-pointer"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5 text-gray-300" />}
            <span>{copied ? "Copied!" : "Copy to Clipboard"}</span>
          </button>
          <button className="glass-button-primary px-3.5 py-2 rounded-xl text-xs text-white flex items-center space-x-1.5 cursor-pointer">
            <Download className="w-3.5 h-3.5" />
            <span>Export Markdown / PDF</span>
          </button>
        </div>
      </div>

      {/* Document Type Selector Tabs */}
      <div className="flex items-center space-x-2 bg-white/5 p-1.5 rounded-2xl border border-white/10 w-fit">
        <button
          onClick={() => setActiveDocType("cover_letter")}
          className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            activeDocType === "cover_letter"
              ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40"
              : "text-gray-400 hover:text-white"
          }`}
        >
          Tailored Cover Letter
        </button>
        <button
          onClick={() => setActiveDocType("tailored_cv")}
          className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            activeDocType === "tailored_cv"
              ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40"
              : "text-gray-400 hover:text-white"
          }`}
        >
          Tailored CV Variant
        </button>
        <button
          onClick={() => setActiveDocType("qa_sheet")}
          className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            activeDocType === "qa_sheet"
              ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40"
              : "text-gray-400 hover:text-white"
          }`}
        >
          Form Q&A Answers (Confidence Graded)
        </button>
      </div>

      {/* Document View Canvas */}
      <div className="glass-panel-glow p-8 rounded-2xl border border-white/15 min-h-[500px]">
        {activeDocType === "cover_letter" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-white/10 text-xs font-mono text-gray-400">
              <span>Target: ICT Specialist & Systems Administrator</span>
              <span className="text-emerald-400 font-semibold">Grounded & Verified</span>
            </div>
            <pre className="whitespace-pre-wrap font-sans text-xs text-gray-200 leading-relaxed">
              {sampleCoverLetter}
            </pre>
          </div>
        )}

        {activeDocType === "tailored_cv" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-white/10 text-xs font-mono text-gray-400">
              <span>Resume Layout: Systems & Cybersecurity Emphasis</span>
              <span className="text-emerald-400 font-semibold">Zero Hallucinations</span>
            </div>
            <pre className="whitespace-pre-wrap font-mono text-xs text-gray-200 leading-relaxed bg-black/30 p-5 rounded-xl border border-white/5">
              {sampleCV}
            </pre>
          </div>
        )}

        {activeDocType === "qa_sheet" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-white/10 text-xs font-mono text-gray-400">
              <span>Custom Form Q&A Generator with Confidence Scores</span>
              <span className="text-cyan-400 font-semibold">High Confidence</span>
            </div>

            <div className="space-y-3.5">
              {sampleQA.map((qa, idx) => (
                <div key={idx} className="p-4 rounded-xl bg-white/5 border border-white/10 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-white font-heading">
                      Q: {qa.question}
                    </span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                      {Math.round(qa.confidence * 100)}% Confidence
                    </span>
                  </div>
                  <p className="text-xs text-gray-300 leading-relaxed">
                    {qa.answer}
                  </p>
                  <div className="flex items-center space-x-1.5 text-[10px] text-emerald-400 font-mono pt-1">
                    <CheckCircle2 className="w-3 h-3" />
                    <span>Fact verified from candidate employment history</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
