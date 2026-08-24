"use client";

import React, { useState } from "react";
import {
  Mail,
  Send,
  Sliders,
  CheckCircle2,
  Clock,
  ShieldCheck,
  Zap,
  Globe,
  Bell,
  RefreshCw,
} from "lucide-react";

export const IntegrationsHub: React.FC = () => {
  const [telegramStatus, setTelegramStatus] = useState("Connected");
  const [gmailStatus, setGmailStatus] = useState("Connected");
  const [scanInterval, setScanInterval] = useState(2); // hours
  const [minMatchAlert, setMinMatchAlert] = useState(85);
  const [testSent, setTestSent] = useState(false);

  const handleSendTestAlert = () => {
    setTestSent(true);
    setTimeout(() => setTestSent(false), 3000);
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="glass-panel p-6 rounded-2xl flex items-center justify-between">
        <div>
          <div className="flex items-center space-x-2 text-cyan-400 text-xs font-mono font-bold uppercase tracking-wider">
            <Sliders className="w-4 h-4 text-cyan-400" />
            <span>Autonomous Automation Rules & Integrations</span>
          </div>
          <h2 className="text-xl font-heading font-bold text-white mt-1">
            Connected Services & Rule Controls
          </h2>
          <p className="text-xs text-gray-400 font-mono mt-0.5">
            Configure Gmail OAuth2, Telegram alerts, scan frequency, and matching thresholds.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Gmail OAuth Integration Card */}
        <div className="glass-panel p-6 rounded-2xl space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-xl bg-red-500/10 border border-red-500/30 flex items-center justify-center text-red-400">
                <Mail className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-heading font-bold text-white">
                  Google Workspace / Gmail OAuth2
                </h3>
                <p className="text-xs text-gray-400 font-mono">
                  Least-privilege sending & inbox response tracking
                </p>
              </div>
            </div>
            <span className="px-2.5 py-1 rounded-full text-[10px] font-mono font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
              Active Sync
            </span>
          </div>

          <div className="p-3.5 rounded-xl bg-white/5 border border-white/10 space-y-2 text-xs font-mono">
            <div className="flex justify-between text-gray-300">
              <span className="text-gray-400">Account:</span>
              <span className="font-semibold text-white">david.hunter@example.com</span>
            </div>
            <div className="flex justify-between text-gray-300">
              <span className="text-gray-400">System Label:</span>
              <span className="text-cyan-400">AI-JOB-HUNTER/APPLIED</span>
            </div>
            <div className="flex justify-between text-gray-300">
              <span className="text-gray-400">Inbox Response Classifier:</span>
              <span className="text-emerald-400">Enabled (Interview / Reject)</span>
            </div>
          </div>

          <div className="flex space-x-2 pt-1">
            <button className="glass-button px-3.5 py-2 rounded-xl text-xs text-gray-300 hover:text-white">
              Reconnect Account
            </button>
            <button className="glass-button px-3.5 py-2 rounded-xl text-xs text-red-400 hover:bg-red-500/10">
              Disconnect
            </button>
          </div>
        </div>

        {/* Telegram Bot Integration Card */}
        <div className="glass-panel p-6 rounded-2xl space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-xl bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-400">
                <Send className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-heading font-bold text-white">
                  Telegram Bot Channel
                </h3>
                <p className="text-xs text-gray-400 font-mono">
                  Instant high-value opportunity cards & quick action buttons
                </p>
              </div>
            </div>
            <span className="px-2.5 py-1 rounded-full text-[10px] font-mono font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
              Connected
            </span>
          </div>

          <div className="p-3.5 rounded-xl bg-white/5 border border-white/10 space-y-2 text-xs font-mono">
            <div className="flex justify-between text-gray-300">
              <span className="text-gray-400">Bot Handle:</span>
              <span className="text-cyan-400">@JobHunterAI_Bot</span>
            </div>
            <div className="flex justify-between text-gray-300">
              <span className="text-gray-400">Chat Pairing:</span>
              <span className="text-emerald-400">David (Linked)</span>
            </div>
            <div className="flex justify-between text-gray-300">
              <span className="text-gray-400">Action Callbacks:</span>
              <span className="text-gray-200">[Apply] [Review] [Skip]</span>
            </div>
          </div>

          <button
            onClick={handleSendTestAlert}
            className="w-full glass-button-primary py-2.5 rounded-xl text-xs font-semibold text-white flex items-center justify-center space-x-2 cursor-pointer"
          >
            <Bell className="w-3.5 h-3.5" />
            <span>{testSent ? "Test Alert Sent to Telegram!" : "Dispatch Test Match Card to Telegram"}</span>
          </button>
        </div>

        {/* Scan Frequency & Automation Rules */}
        <div className="md:col-span-2 glass-panel p-6 rounded-2xl space-y-5">
          <h3 className="text-sm font-heading font-bold text-white flex items-center space-x-2">
            <Clock className="w-4 h-4 text-cyan-400" />
            <span>Automated Scanning & Alert Thresholds</span>
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <div className="flex justify-between text-xs font-mono mb-2">
                <span className="text-gray-400">Background Ingestion Frequency:</span>
                <span className="text-cyan-400 font-bold">Every {scanInterval} Hours</span>
              </div>
              <input
                type="range"
                min="1"
                max="12"
                value={scanInterval}
                onChange={(e) => setScanInterval(Number(e.target.value))}
                className="w-full accent-cyan-400 cursor-pointer"
              />
              <p className="text-[10px] text-gray-500 font-mono mt-1">
                Scans ReliefWeb, Hot Nigerian Jobs, RemoteOK with intelligent rate limiting.
              </p>
            </div>

            <div>
              <div className="flex justify-between text-xs font-mono mb-2">
                <span className="text-gray-400">Instant Alert Trigger Threshold:</span>
                <span className="text-emerald-400 font-bold">Match Score &gt;= {minMatchAlert}%</span>
              </div>
              <input
                type="range"
                min="60"
                max="95"
                step="5"
                value={minMatchAlert}
                onChange={(e) => setMinMatchAlert(Number(e.target.value))}
                className="w-full accent-emerald-400 cursor-pointer"
              />
              <p className="text-[10px] text-gray-500 font-mono mt-1">
                Only matches meeting or exceeding this threshold will trigger immediate push alerts.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
