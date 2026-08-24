"use client";

import React, { useState } from "react";
import {
  Radar,
  Sparkles,
  Bell,
  Mail,
  Send,
  RefreshCw,
  SlidersHorizontal,
  ShieldCheck,
  CheckCircle2,
} from "lucide-react";

interface ExecutiveHeaderProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  onTriggerScan: () => void;
  isScanning: boolean;
}

export const ExecutiveHeader: React.FC<ExecutiveHeaderProps> = ({
  activeTab,
  setActiveTab,
  onTriggerScan,
  isScanning,
}) => {
  const [showNotifications, setShowNotifications] = useState(false);

  const navItems = [
    { id: "dashboard", label: "Executive Dashboard", icon: Radar },
    { id: "jobs", label: "Opportunity Radar", icon: Sparkles },
    { id: "pipeline", label: "Application Pipeline", icon: Send },
    { id: "profile", label: "Candidate Intelligence", icon: ShieldCheck },
    { id: "documents", label: "Document Studio", icon: SlidersHorizontal },
    { id: "integrations", label: "Integrations & Rules", icon: Mail },
  ];

  return (
    <header className="sticky top-0 z-40 w-full border-b border-white/10 glass-panel px-6 py-3.5">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Brand & Live Telemetry Pill */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-500 to-emerald-400 p-0.5 shadow-lg shadow-cyan-500/20 flex items-center justify-center">
              <div className="w-full h-full bg-[#080B11] rounded-[10px] flex items-center justify-center">
                <Radar className="w-5 h-5 text-cyan-400 animate-pulse" />
              </div>
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-heading font-bold text-lg text-white tracking-wide">
                  JHUNTER<span className="text-cyan-400">.AI</span>
                </span>
                <span className="px-2 py-0.5 text-[10px] uppercase font-mono font-bold tracking-widest bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 rounded-full">
                  Enterprise Suite
                </span>
              </div>
              <p className="text-[11px] text-gray-400 font-mono">
                Autonomous Executive Recruitment Intelligence
              </p>
            </div>
          </div>

          <div className="hidden lg:flex items-center space-x-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-xs font-mono text-gray-300">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
            <span className="text-emerald-400 font-medium">Scanner Active</span>
            <span className="text-gray-500">|</span>
            <span>ReliefWeb • HotNigerianJobs • RemoteOK</span>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="hidden md:flex items-center space-x-1 p-1 bg-white/5 border border-white/10 rounded-xl">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  isActive
                    ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm"
                    : "text-gray-400 hover:text-gray-200 hover:bg-white/5"
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Action Toolbar */}
        <div className="flex items-center space-x-3">
          <button
            onClick={onTriggerScan}
            disabled={isScanning}
            className="glass-button-primary px-3.5 py-2 rounded-xl text-xs font-medium text-white flex items-center space-x-2 cursor-pointer disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isScanning ? "animate-spin" : ""}`} />
            <span>{isScanning ? "Scanning Feeds..." : "Run Global Scan"}</span>
          </button>

          <div className="relative">
            <button
              onClick={() => setShowNotifications(!showNotifications)}
              className="glass-button p-2 rounded-xl text-gray-300 hover:text-white relative"
            >
              <Bell className="w-4 h-4" />
              <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
            </button>

            {showNotifications && (
              <div className="absolute right-0 mt-2 w-80 glass-panel-glow rounded-2xl p-4 shadow-2xl z-50 animate-in fade-in zoom-in-95">
                <div className="flex items-center justify-between mb-3 border-b border-white/10 pb-2">
                  <span className="text-xs font-bold uppercase tracking-wider text-cyan-400 font-mono">
                    Live Event Stream
                  </span>
                  <span className="text-[10px] text-gray-400">2 New Alerts</span>
                </div>
                <div className="space-y-2.5 text-xs">
                  <div className="p-2.5 rounded-xl bg-white/5 border border-white/10">
                    <div className="flex items-center justify-between text-emerald-400 font-semibold mb-1">
                      <span>94% High Match Alert</span>
                      <span className="text-[10px] font-mono text-gray-400">2m ago</span>
                    </div>
                    <p className="text-gray-300">
                      ICT Specialist & Systems Administrator at International NGO.
                    </p>
                  </div>
                  <div className="p-2.5 rounded-xl bg-white/5 border border-white/10">
                    <div className="flex items-center justify-between text-amber-400 font-semibold mb-1">
                      <span>Gmail Signal: Interview</span>
                      <span className="text-[10px] font-mono text-gray-400">1h ago</span>
                    </div>
                    <p className="text-gray-300">
                      Invitation for technical interview from Fintech Global.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="hidden sm:flex items-center space-x-2 pl-2 border-l border-white/10">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-400 to-emerald-500 p-0.5">
              <div className="w-full h-full bg-[#080B11] rounded-full flex items-center justify-center font-bold text-xs text-cyan-300">
                D
              </div>
            </div>
            <div className="text-left">
              <div className="text-xs font-semibold text-white">David</div>
              <div className="text-[10px] text-gray-400 font-mono">IT & Comm Specialist</div>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
