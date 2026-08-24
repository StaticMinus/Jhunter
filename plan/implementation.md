# AI Job Hunter (Jhunter) — Technical Implementation Blueprint

Detailed technical implementation specs based on the MVP Specification (Pages 1–14), ECC backend/frontend patterns, and Design DNA guidelines.

---

## 1. Data Schema & Models (PostgreSQL / SQLAlchemy)

### Database Entities:

```sql
-- 1. Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    timezone VARCHAR(64) DEFAULT 'UTC',
    google_tokens_encrypted TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Candidate Profiles
CREATE TABLE candidate_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    summary TEXT,
    seniority VARCHAR(64),
    location VARCHAR(128),
    salary_floor NUMERIC(12, 2),
    preferences_json JSONB DEFAULT '{}'::jsonb,
    version INT DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Candidate Skills
CREATE TABLE candidate_skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID REFERENCES candidate_profiles(id) ON DELETE CASCADE,
    skill VARCHAR(128) NOT NULL,
    category VARCHAR(64),
    proficiency VARCHAR(32), -- Expert, Advanced, Intermediate
    evidence TEXT,           -- Verifiable projects / years / citations
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Experiences
CREATE TABLE experiences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID REFERENCES candidate_profiles(id) ON DELETE CASCADE,
    employer VARCHAR(255) NOT NULL,
    title VARCHAR(255) NOT NULL,
    start_date DATE,
    end_date DATE,
    description TEXT,
    sector VARCHAR(128)
);

-- 5. Education & Certifications
CREATE TABLE education (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID REFERENCES candidate_profiles(id) ON DELETE CASCADE,
    institution VARCHAR(255) NOT NULL,
    qualification VARCHAR(255) NOT NULL,
    dates VARCHAR(64),
    field VARCHAR(128)
);

CREATE TABLE certifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID REFERENCES candidate_profiles(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    issuer VARCHAR(255) NOT NULL,
    year INT
);

-- 6. Job Sources & Ingested Jobs
CREATE TABLE job_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(128) NOT NULL,
    type VARCHAR(64) NOT NULL, -- scraper, api, rss, career_page
    base_url TEXT NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    last_run_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID REFERENCES job_sources(id) ON DELETE SET NULL,
    external_id VARCHAR(255),
    canonical_url TEXT NOT NULL UNIQUE,
    title VARCHAR(255) NOT NULL,
    employer VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    work_mode VARCHAR(32), -- remote, hybrid, onsite, unknown
    salary_min NUMERIC(12, 2),
    salary_max NUMERIC(12, 2),
    currency VARCHAR(16),
    description TEXT NOT NULL,
    posted_at TIMESTAMP WITH TIME ZONE,
    raw_hash VARCHAR(64) NOT NULL, -- SHA-256 for dedup
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE job_features (
    job_id UUID PRIMARY KEY REFERENCES jobs(id) ON DELETE CASCADE,
    skills_json JSONB DEFAULT '[]'::jsonb,
    seniority VARCHAR(64),
    industry VARCHAR(128),
    visa_signal VARCHAR(32),   -- indicated, possible, unknown, no_indication
    remote_signal VARCHAR(32), -- full_remote, hybrid, onsite, unknown
    extracted_salary JSONB,
    requirements_json JSONB DEFAULT '[]'::jsonb,
    extracted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 7. Matches, Applications & Documents
CREATE TABLE job_matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    profile_id UUID REFERENCES candidate_profiles(id) ON DELETE CASCADE,
    match_score INT NOT NULL,
    opportunity_score INT NOT NULL,
    explanation_json JSONB NOT NULL,
    gaps_json JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(job_id, profile_id)
);

CREATE TABLE applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    profile_id UUID REFERENCES candidate_profiles(id) ON DELETE CASCADE,
    status VARCHAR(32) DEFAULT 'DRAFT', -- DRAFT, PENDING_APPROVAL, APPLIED, INTERVIEW, REJECTED, ARCHIVED
    approval_state VARCHAR(32) DEFAULT 'REVIEW', -- AUTO, REVIEW, SKIP
    applied_at TIMESTAMP WITH TIME ZONE,
    method VARCHAR(32), -- email, web_form, api, manual
    external_reference TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID REFERENCES applications(id) ON DELETE CASCADE,
    type VARCHAR(32) NOT NULL, -- tailored_cv, cover_letter, qa_sheet
    storage_path TEXT NOT NULL,
    version INT DEFAULT 1,
    content_markdown TEXT,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE application_answers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID REFERENCES applications(id) ON DELETE CASCADE,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    confidence NUMERIC(3, 2), -- 0.00 to 1.00
    reviewed BOOLEAN DEFAULT FALSE,
    flagged_for_review BOOLEAN DEFAULT FALSE
);

CREATE TABLE communications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID REFERENCES applications(id) ON DELETE SET NULL,
    channel VARCHAR(32) NOT NULL, -- gmail, telegram
    direction VARCHAR(16) NOT NULL, -- inbound, outbound
    message_id TEXT,
    subject TEXT,
    body_snippet TEXT,
    received_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    classification VARCHAR(64) -- interview, assessment, rejection, shortlist, acknowledgment, general
);

CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    channel VARCHAR(32) NOT NULL,
    type VARCHAR(64) NOT NULL,
    payload_json JSONB NOT NULL,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    read_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE scan_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID REFERENCES job_sources(id) ON DELETE SET NULL,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    finished_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(32) DEFAULT 'RUNNING',
    jobs_found INT DEFAULT 0,
    jobs_new INT DEFAULT 0,
    error_log TEXT
);

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(64) NOT NULL,
    entity_type VARCHAR(64) NOT NULL,
    entity_id UUID,
    metadata_json JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

## 2. Deterministic & AI Scoring Algorithms

### Match Score (0 to 100)
$$\text{Match} = 0.30 \cdot S_{\text{skills}} + 0.20 \cdot S_{\text{exp}} + 0.15 \cdot S_{\text{role}} + 0.10 \cdot S_{\text{ind}} + 0.10 \cdot S_{\text{edu}} + 0.10 \cdot S_{\text{loc}} + 0.05 \cdot S_{\text{comm}}$$

- $S_{\text{skills}}$: Jaccard & Semantic similarity between candidate verified skills and extracted job requirements.
- $S_{\text{exp}}$: Years of experience vs requested range.
- $S_{\text{role}}$: Candidate target roles vs job title.
- $S_{\text{ind}}$: Industry alignment (e.g. IT, NGO, Telecomm, Enterprise).
- $S_{\text{edu}}$: Degree / certification fulfillment.
- $S_{\text{loc}}$: Location compatibility (Nigeria / Remote / Worldwide).
- $S_{\text{comm}}$: Documentation / client-facing / leadership presence.

### Opportunity Score (0 to 100)
$$\text{Opportunity} = 0.25 \cdot O_{\text{visa}} + 0.20 \cdot O_{\text{mode}} + 0.20 \cdot O_{\text{comp}} + 0.15 \cdot O_{\text{emp}} + 0.10 \cdot O_{\text{growth}} + 0.10 \cdot O_{\text{feas}}$$

- $O_{\text{visa}}$: Visa sponsorship status (`indicated` = 100, `possible` = 70, `unknown` = 50, `no_indication` = 20).
- $O_{\text{mode}}$: Remote (100) > Hybrid (75) > Onsite (50).
- $O_{\text{comp}}$: Compensation vs Nigeria baseline (₦500,000–₦600,000/mo) or FX currency (USD/EUR/GBP).
- $O_{\text{emp}}$: Global NGO / UN / Multinational / Tech Tier-1.
- $O_{\text{growth}}$: Seniority / leadership elevation potential.
- $O_{\text{feas}}$: Application barrier & direct contact feasibility.

---

## 3. Anti-Fabrication Generation Engine

1. **Context Grounding**: Prompt injects the candidate's strictly verified profile JSON.
2. **Prohibited Generations**:
   - Inventing unverified employers or job titles.
   - Fabricating certifications (e.g. ITIL, PMP, CISSP) not present in candidate records.
   - Claiming false visa status or fabricating numbers.
3. **Structured Outputs**:
   - Tailored CV: Markdown resume emphasizing relevant real achievements.
   - Tailored Cover Letter: 3-4 paragraph high-impact executive pitch.
   - Q&A Form Generator: Question-answering with `confidence` score (0.0 to 1.0) and automatic flag for review if confidence < 0.85.
   - Gap Analysis: Clear distinction between "Missing Skill" vs "Missing Evidence in CV".

---

## 4. Multi-Channel Integrations

### Gmail API:
- Google OAuth2 with `https://www.googleapis.com/auth/gmail.send` & `https://www.googleapis.com/auth/gmail.readonly`.
- Auto-label applied emails: `AI-JOB-HUNTER/APPLIED`.
- Sentiment & intent classifier on incoming recruiter replies:
  - `INTERVIEW_INVITE` -> High-priority Telegram alert + Kanban stage advancement.
  - `ASSESSMENT` -> Alert + timeline update.
  - `REJECTION` -> Automated status update + feedback extraction.
  - `SHORTLIST` -> Notification.

### Telegram Bot API:
- Send structured rich markdown cards with high-priority matches (Match >= 85% or Opportunity >= 85%).
- Inline action keyboard:
  - `[ 🚀 Apply Now ]` -> Triggers Gmail/Automated submission.
  - `[ 📝 Review Package ]` -> Deep link to web application studio.
  - `[ ❌ Skip / Archive ]` -> Archives match.
