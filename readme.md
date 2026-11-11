# ⚡ SkillTrack — Smart GDG Campaign Tracker & Analytics Engine

> **A desktop-grade campaign management, verification, and analytics tool built for Google Developer Group (GDG) organizers to track, evaluate, and accelerate student progress in the Google Skills / Learn With Communities Campaign.**

---

## 📖 Executive Summary

**SkillTrack** streamlines candidate evaluation during Google Developer Group skill campaigns. Organizers often deal with hundreds of public Google Skills profile URLs, making manual verification of badge counts slow, error-prone, and inefficient. 

SkillTrack automates profile parsing and badge calculation, offering real-time progress monitoring, rule-based outreach prioritization, automated message generation, and SQLite execution persistence—all delivered within a clean desktop interface styled with official Google Developer design principles.

---

## ✨ Key Features & Architectural Modules

### 🎯 1. Student Outreach Priority Index (`analytics.py`)
Automatically tags and ranks students based on completion status to help organizers prioritize outreach efforts effectively:
* **HIGH (Quick Win)**: Students with 8–9 badges who need just 1–2 badges to finish the campaign.
* **HIGH (Broken / Private)**: Profiles set to private or returning invalid URLs requiring manual organizer intervention.
* **MEDIUM (Onboarding Needed)**: Registered students with 0 badges who require initial setup assistance.
* **MEDIUM (Encouragement Needed)**: Active learners stuck at 1–7 badges.
* **LOW (Completed)**: Candidates who have earned all 10 badges.

### 🟢 2. Campaign Target Health Score & Velocity Indicator
Calculates an aggregate **Health Index Score (0% to 100%)** for the cohort using weighted completion metrics:
* **Status Categories**: `🟢 EXCELLENT`, `🟡 ON TRACK`, `🟠 NEEDS PUSH`, `🔴 CRITICAL`.
* Gives GDG leads a single metric to measure overall campaign velocity against target deadlines.

### 📢 3. Automated Copy-Paste Broadcast Intervention Templates
Generates pre-populated messaging templates formatted for Discord, WhatsApp, or email:
* **Quick Win Reminder**: Alerts candidates who are 1–2 badges away from completion.
* **Onboarding Push**: Reaches out to participants who haven't started.
* **Private Profile Warning**: Prompts candidates with private settings to make their profiles public.

### 🔍 4. Badge Gap Analyzer & Report Exporter
* Enables organizers to filter candidates by the exact number of missing badges (e.g., candidates needing exactly 1 badge vs. 2 badges).
* Provides dynamic export capabilities to generate detailed `.csv` audit reports for official submission and archive records.

### 💾 5. Database Execution Logging (`storage.py`)
* Integrates a local SQLite database (`skilltrack_history.db`) that automatically records batch run metadata and historical profile snapshots upon every verification run.

---

## 🛡️ Security Hardening & Robustness Features

SkillTrack incorporates core defense-in-depth security measures to ensure safe execution:

| Security Domain | Implementation Detail |
| :--- | :--- |
| **SSRF & Domain Allowlisting** | Restricts outbound HTTP requests strictly to official Google domains via `urlparse` scheme & netloc verification (`skills.google`, `cloudskillsboost.google`). Rejects non-HTTPS schemes or unauthorized domains. |
| **Input Sanitization** | Validates incoming profile URLs for structural integrity and sanitizes text inputs prior to parsing. |
| **File Guardrails & Memory Caps** | Enforces `.csv` file extension validation and applies a strict **5 MB file size limit** to prevent Denial-of-Service (DoS) via memory exhaustion. |
| **Request Timeout & Thread Protection** | Configures network request timeouts (10 seconds) to prevent hung sockets or unhandled network dropouts. |
| **Data Protection & Hygiene** | Configured with explicit `.gitignore` rules to prevent database leaks (`.db`), session caches (`__pycache__`), and sensitive environment configurations from being pushed to public repositories. |

---

## 🎨 UI/UX Design

The Desktop GUI (`app_gui.py`) is styled using Tkinter’s `ttk.Style` engine, featuring a clean Google Developer color palette:
* **Google Blue (`#1A73E8`)**: Header bar and key interactive controls.
* **Emerald Green (`#0F9D58`)**: Completion markers and verification actions.
* **Amber Yellow (`#F4B400`)** & **Coral Red (`#DB4437`)**: Quick-win highlights and private profile flags.
* **Status Pill Tags & Custom Cards**: Dynamic metric displays and alternating row colors (`#FFFFFF` vs. `#F8F9FA`) for enhanced table readability.

---

## 🛠️ Project Structure

```text
badgetrack/
├── analytics.py          # Core business logic, health calculations, & template generation
├── app_gui.py            # Primary Tkinter Desktop Application UI
├── scraper.py            # Profile scraper with SSRF allowlisting & rate limiting
├── storage.py            # SQLite database interface & batch run persistence
├── Dockerfile            # Container configuration file
├── .dockerignore         # Docker build exclusion rules
├── .gitignore            # Git tracking exclusions
├── requirements.txt      # Dependency specification file
└── README.md             # Project documentation
```

---

## 🚀 Getting Started

### Prerequisites
* **Python 3.9+** installed on your system.
* **Git** for version control.

### Installation & Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/YOUR_GITHUB_USERNAME/skilltrack.git
   cd skilltrack
   ```

2. **Create and Activate Virtual Environment**:
   * **Windows**:
     ```cmd
     python -m venv venv
     .\venv\Scripts\activate
     ```
   * **macOS / Linux**:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Launch the Desktop Application**:
   ```bash
   python app_gui.py
   ```

---

## 🐳 Running with Docker

SkillTrack includes a lightweight container configuration.

1. **Build the Docker Image**:
   ```bash
   docker build -t skilltrack:latest .
   ```

2. **Run the Container**:
   ```bash
   docker run -d -p 8501:8501 --name skilltrack_app skilltrack:latest
   ```

---

## 📄 License & Attribution

Developed for the **Google Developer Group (GDG) Learn With Communities Campaign**. Designed to empower community organizers with clear insights and automated workflows.