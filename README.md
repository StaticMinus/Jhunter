# AI Job Hunter (Jhunter)

> **Autonomous Executive Recruitment Intelligence Suite**
> Engineered using **ECC (Everything Claude Code)** patterns and **Design DNA** $1,000,000 liquid glass visual standards with interactive 3D Three.js radar systems.

---

## Architecture Overview

```
JOB Hunter/
├── apps/
│   ├── api/                          # Python FastAPI Async Backend
│   │   ├── app/
│   │   │   ├── api/routes/           # auth, candidate, jobs, applications, integrations, notifications
│   │   │   ├── core/                 # security, config, middleware
│   │   │   ├── db/                   # SQLAlchemy async models & session
│   │   │   ├── schemas/              # Pydantic v2 validation models
│   │   │   └── services/             # matching_engine, cv_parser, application_generator
│   │   └── tests/                    # unit & scoring tests
│   └── web/                          # Next.js 15 App Router Frontend
│       ├── src/
│       │   ├── app/                  # layout, globals.css (Design DNA), page.tsx
│       │   └── components/           # ThreeBackground, ThreeRadarGlobe, KPIGrid, JobFeed, Kanban, Studios
├── workers/                          # Ingestion Adapters & Deduplication
│   ├── adapters/                     # ReliefWeb, RemoteOK, HotNigerianJobs
│   ├── deduplication.py              # SHA-256 fingerprinting & canonicalization
│   └── scheduler.py
├── plan/                             # Architecture & specification blueprints
│   ├── plan.md
│   ├── implementation.md
│   └── design_dna.json
├── docker-compose.yml
└── .env.example
```

---

## Key Features

1. **Candidate Intelligence & Grounded Evidence Studio**:
   - Parses CVs into structured entities: skills, verified evidence, employment history, certifications, preferences.
   - Zero hallucination guarantee: every generated document only references verified facts.
2. **Pluggable Multi-Source Ingestion**:
   - `JobSourceAdapter` connector interface with built-in rate-limiting and deduplication.
   - Adapters for ReliefWeb (UN/NGOs), RemoteOK, Nigerian career boards, and RSS feeds.
3. **Dual Weighted Scoring Engine**:
   - **Match Score (0-100)**: $30\%$ skills + $20\%$ experience + $15\%$ role/seniority + $10\%$ industry + $10\%$ education + $10\%$ location + $5\%$ communication.
   - **Opportunity Score (0-100)**: $25\%$ visa/relocation + $20\%$ work-mode + $20\%$ compensation quality + $15\%$ employer/sector + $10\%$ career growth + $10\%$ application feasibility.
4. **Anti-Fabrication Application Generator**:
   - Generates tailored CV variants, high-impact cover letters, and Q&A answers with confidence ratings and fact verification tags.
5. **Approval Workflow & Kanban Pipeline**:
   - Tri-state review gateway: `AUTO` (low risk), `REVIEW` (complex), `SKIP` (low match/duplicate).
6. **Multi-Channel Orchestration**:
   - **Gmail OAuth2**: Least-privilege sending & automatic response classification (Interview, Assessment, Rejection).
   - **Telegram Bot**: Instant high-opportunity cards with interactive `[Apply]` / `[Review]` / `[Skip]` action buttons.
7. **$1,000,000 Executive Design System**:
   - Obsidian dark theme, frosted liquid glass panels, and interactive 3D Three.js particle constellation and holographic match radar orb.

---

## Quickstart & Running Locally

### Backend (FastAPI):
```bash
cd apps/api
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend (Next.js 15):
```bash
cd apps/web
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

### Run Automated Tests:
```bash
npm run test:backend
```
