"use client";

import React from "react";
import {
  Clock,
  Send,
  MessageSquareCode,
  CheckCircle2,
  XCircle,
  FileText,
  Building2,
  ChevronRight,
  ShieldCheck,
} from "lucide-react";

export interface ApplicationItem {
  id: string;
  job_id: string;
  title: string;
  employer: string;
  location: string;
  status: "DRAFT" | "PENDING_APPROVAL" | "APPLIED" | "INTERVIEW" | "ARCHIVED";
  approval_state: "AUTO" | "REVIEW" | "SKIP";
  match_score?: number;
  opportunity_score?: number;
  applied_at?: string | null;
  method?: string;
}

interface KanbanPipelineProps {
  applications: ApplicationItem[];
  onApprove: (id: string) => void;
  onReject: (id: string) => void;
  onViewDetails: (app: ApplicationItem) => void;
}

export const KanbanPipeline: React.FC<KanbanPipelineProps> = ({
  applications,
  onApprove,
  onReject,
  onViewDetails,
}) => {
  const columns = [
    {
      id: "PENDING_APPROVAL",
      title: "Review & Approval Queue",
      subtitle: "Tri-state AI decision gateway",
      color: "border-purple-500/30 text-purple-400 bg-purple-500/10",
      badgeColor: "bg-purple-500/20 text-purple-300",
    },
    {
      id: "APPLIED",
      title: "Submitted & Monitored",
      subtitle: "Tracked via Gmail/Telegram",
      color: "border-blue-500/30 text-blue-400 bg-blue-500/10",
      badgeColor: "bg-blue-500/20 text-blue-300",
    },
    {
      id: "INTERVIEW",
      title: "Interview / Assessment",
      subtitle: "Active recruiter dialogue",
      color: "border-emerald-500/30 text-emerald-400 bg-emerald-500/10",
      badgeColor: "bg-emerald-500/20 text-emerald-300",
    },
    {
      id: "ARCHIVED",
      title: "Archived / Resolved",
      subtitle: "Historical record",
      color: "border-gray-500/30 text-gray-400 bg-gray-500/10",
      badgeColor: "bg-gray-500/20 text-gray-300",
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-heading font-bold text-white">
            Application Pipeline Kanban
          </h2>
          <p className="text-xs text-gray-400 font-mono">
            State-machine tracked from package generation to Gmail confirmation.
          </p>
        </div>
        <div className="flex items-center space-x-2 text-xs text-cyan-400 font-mono">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span>Immutable Audit Ledger Active</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {columns.map((col) => {
          const colApps = applications.filter((a) => a.status === col.id);

          return (
            <div
              key={col.id}
              className="glass-panel p-4 rounded-2xl flex flex-col h-[70vh] border border-white/10"
            >
              {/* Column Header */}
              <div className="flex items-center justify-between pb-3 border-b border-white/10 mb-3">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-bold text-white">{col.title}</span>
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-bold ${col.badgeColor}`}>
                      {colApps.length}
                    </span>
                  </div>
                  <p className="text-[10px] text-gray-400 font-mono mt-0.5">{col.subtitle}</p>
                </div>
              </div>

              {/* Cards Container */}
              <div className="flex-1 overflow-y-auto space-y-3 pr-1">
                {colApps.length === 0 ? (
                  <div className="h-32 flex flex-col items-center justify-center text-gray-500 text-xs font-mono border border-dashed border-white/10 rounded-xl">
                    No active applications
                  </div>
                ) : (
                  colApps.map((app) => (
                    <div
                      key={app.id}
                      onClick={() => onViewDetails(app)}
                      className="p-3.5 rounded-xl bg-white/5 border border-white/10 hover:border-cyan-500/40 hover:bg-white/10 transition-all cursor-pointer space-y-2.5"
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <h4 className="font-heading font-bold text-xs text-white line-clamp-1">
                            {app.title}
                          </h4>
                          <p className="text-[11px] text-gray-300 flex items-center space-x-1 mt-0.5">
                            <Building2 className="w-3 h-3 text-gray-400" />
                            <span>{app.employer}</span>
                          </p>
                        </div>
                        {app.match_score && (
                          <span className="px-2 py-0.5 rounded-md bg-emerald-500/15 border border-emerald-500/30 text-[10px] font-mono font-bold text-emerald-400">
                            {app.match_score}%
                          </span>
                        )}
                      </div>

                      <div className="flex items-center justify-between text-[10px] font-mono text-gray-400 pt-1 border-t border-white/5">
                        <span>Mode: {app.approval_state}</span>
                        <span>{app.location}</span>
                      </div>

                      {/* Action Buttons for Pending Approval */}
                      {col.id === "PENDING_APPROVAL" && (
                        <div className="flex items-center space-x-2 pt-2">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              onApprove(app.id);
                            }}
                            className="flex-1 py-1.5 rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 border border-emerald-500/40 text-[11px] font-semibold text-emerald-300 flex items-center justify-center space-x-1"
                          >
                            <CheckCircle2 className="w-3 h-3" />
                            <span>Approve & Send</span>
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              onReject(app.id);
                            }}
                            className="py-1.5 px-2.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 text-[11px] text-red-400"
                          >
                            <XCircle className="w-3 h-3" />
                          </button>
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
