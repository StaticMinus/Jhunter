# AI Job Hunter (Jhunter) — Master Plan

> **Enterprise Autonomous Recruitment Intelligence System**
> Engineered using ECC (Everything Claude Code) architecture patterns and Design DNA $1,000,000 UI/UX visual standards.

---

## 1. Project Overview & Objectives

**AI Job Hunter** is an autonomous recruitment intelligence engine and application assistant designed to automate discovery, matching, tailored material generation, and multi-channel notifications (Gmail & Telegram) without sacrificing application quality or hallucinating candidate data.

### Core Goals:
1. **Candidate Intelligence**: One-time CV ingestion & parsing into a structured, verifiable profile (skills, evidence, experience, certifications, preferences).
2. **Multi-Source Job Ingestion**: Pluggable source adapters (`JobSourceAdapter`) scanning Nigerian boards (Hot Nigerian Jobs), NGO/humanitarian portals (ReliefWeb/UN), Remote boards (RemoteOK/WeWorkRemotely), and company career feeds.
3. **Dual Weighted Scoring Engine**:
   - **Match Score**: Skills (30%), Experience (20%), Role/Seniority (15%), Industry (10%), Education (10%), Location/Work Mode (10%), Communication (5%).
   - **Opportunity Score**: Visa/Relocation (25%), Work Mode (20%), Compensation (20%), Employer Relevance (15%), Career Growth (10%), Feasibility (10%).
4. **Anti-Fabrication Application Generator**: Tailored CV variants, cover letters, and Q&A answers strictly grounded in candidate facts.
5. **Human-in-the-Loop & Auto Triage**: `AUTO` (low risk), `REVIEW` (ambiguous/complex), `SKIP` (low match/duplicate).
6. **Unified Integrations**: Least-privilege Gmail OAuth2 (sending & response classifier), Telegram Bot (real-time alerts & action buttons).
7. **$1,000,000 Executive Design System**: Next.js 15 + Liquid Glass + Obsidian Dark Theme + GSAP/Framer Motion micro-interactions.

---

## 2. Monorepo Architecture

```
JOB Hunter/
├── apps/
│   ├── api/                          # FastAPI Backend
│   │   ├── app/
│   │   │   ├── api/routes/           # auth, candidate, jobs, applications, integrations, notifications
│   │   │   ├── core/                 # security, config, middleware, database
│   │   │   ├── db/                   # models, session, migrations
│   │   │   ├── schemas/              # Pydantic v2 schemas
│   │   │   └── services/             # cv_parser, matching, app_gen, gmail, telegram
│   │   ├── tests/                    # pytest unit & integration tests
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   └── web/                          # Next.js 15 App Router Frontend
│       ├── src/
│       │   ├── app/                  # pages (dashboard, jobs, applications, profile, documents, integrations, settings)
│       │   ├── components/           # liquid glass UI, job cards, kanban, editor, charts
│       │   ├── hooks/                # reactive queries & store
│       │   ├── lib/                  # api client, design tokens, formatters
│       │   └── types/                # TypeScript interfaces
│       ├── tailwind.config.ts
│       ├── package.json
│       └── next.config.ts
├── workers/                          # Background Ingestion & Scheduling Workers
│   ├── adapters/                     # hot_nigerian_jobs, reliefweb, remote_ok, rss
│   ├── normalizer.py                 # schema normalization
│   ├── deduplicator.py               # SHA-256 fingerprinting & similarity scoring
│   ├── scheduler.py                  # interval-based scan orchestrator
│   └── response_monitor.py           # Gmail inbox triage worker
├── packages/
│   └── shared/                       # Shared types, scoring constants, rules
├── plan/                             # Project planning & architecture specs
│   ├── plan.md
│   ├── implementation.md
│   └── design_dna.json
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 3. Implementation Phases (10-Phase Roadmap)

| Phase | Deliverable | Definition of Done |
|---|---|---|
| **Phase 1: Foundation** | Monorepo, DB Schema, Auth | Monorepo set up, PostgreSQL models configured, Google OAuth & JWT auth working. |
| **Phase 2: CV Intelligence** | CV Parsing & Profile Studio | PDF/DOCX CV parser extracting verified structured profile, editable in UI. |
| **Phase 3: Job Ingestion** | Source Adapters & Normalization | 3+ working source adapters, deduplication (fingerprints + similarity), audit logs. |
| **Phase 4: Matching Engine** | Feature Extraction & Dual Scoring | Automated Match Score & Opportunity Score calculation with explainable reasons. |
| **Phase 5: Job Dashboard** | Search, Filters & Intelligence Cards | Real-time filterable job grid, detail drawer, score breakdowns, saved jobs. |
| **Phase 6: Application Engine** | Anti-Fabrication Package Gen | Tailored CV layout, cover letter, and Q&A answers with zero hallucination. |
| **Phase 7: Approval Workflow** | Kanban Pipeline & Tri-State Triage | `AUTO` / `REVIEW` / `SKIP` state machine, timeline tracking, and audit ledger. |
| **Phase 8: Gmail Integration** | OAuth, Sending & Inbox Classifier | Send authorized emails, classify incoming responses (interview, reject, etc.). |
| **Phase 9: Telegram Integration** | Telegram Bot Alerts & Actions | Instant card notifications with interactive Apply / Review / Skip inline buttons. |
| **Phase 10: Hardening & Deploy** | Rate limiting, Retries, CI/CD | Error recovery, exponential backoff, Docker setup, GitHub remote push. |

---

## 4. Design DNA & Visual Identity Guidelines

Inspired by `design-dna-main` and Apple's **Liquid Glass Design System**:
- **Aesthetic**: Sovereign Intelligence Agency & Ultra-High-End Executive Suite.
- **Palette**:
  - Background Base: `#080B11` (Deep Space Obsidian)
  - Surface Glass: `rgba(17, 24, 39, 0.75)` with `backdrop-filter: blur(20px)`
  - Primary Accent: `#06B6D4` (Radiant Cyan / High Signal)
  - Success / Match High: `#10B981` (Emerald Match >= 85%)
  - Opportunity / Visa Signal: `#F59E0B` (Amber Gold)
  - Warning / Gap: `#F97316` (Sunset Orange)
  - Error / Low Match: `#EF4444` (Crimson)
  - Text Primary: `#F9FAFB` (Pure White Slate)
  - Text Secondary: `#9CA3AF` (Muted Steel)
- **Micro-Interactions**: Smooth hover lift, subtle glowing borders on card focus, pulsing live status dots, radar animation for matching engine.
