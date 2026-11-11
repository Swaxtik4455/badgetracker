import pandas as pd
from typing import Dict, List, Any, Tuple

TARGET_BADGES = 10

def classify_participant(badge_count: int, status: str) -> Tuple[str, str]:
    if status != "Verified":
        return ("Manual Verification", "Contact student directly to make profile public.")
    if badge_count >= TARGET_BADGES:
        return ("Completed", "Celebrate completion & issue credentials.")
    elif badge_count in [8, 9]:
        return ("Almost Completed", f"Nudge student: Only {TARGET_BADGES - badge_count} badge(s) left!")
    elif 1 <= badge_count <= 7:
        return ("Needs Attention", "Share GDG beginner study resources.")
    else:
        return ("Not Started", "Send onboarding setup guide.")

def calculate_outreach_priority(badge_count: int, status: str) -> str:
    if status != "Verified":
        return "HIGH (Broken / Private)"
    if badge_count in [8, 9]:
        return "HIGH (Quick Win)"
    if badge_count == 0:
        return "MEDIUM (Onboarding Needed)"
    if 1 <= badge_count <= 7:
        return "MEDIUM (Encouragement Needed)"
    return "LOW (Completed)"

def calculate_campaign_health(df: pd.DataFrame) -> Dict[str, Any]:
    """Feature 1: Calculates overall Campaign Health Index & Velocity."""
    total = len(df)
    if total == 0:
        return {"health_score": 0.0, "status": "NO DATA", "completion_rate": 0.0}

    verified_df = df[df["Verification Status"] == "Verified"]
    completed_count = len(df[df["Campaign Status"] == "Completed"])
    almost_count = len(df[df["Campaign Status"] == "Almost Completed"])
    
    completion_rate = (completed_count / total) * 100
    # Weighted Health Index: completed counts 100%, almost completed counts 50%
    health_score = round(((completed_count + (almost_count * 0.5)) / total) * 100, 1)

    if health_score >= 80:
        status = "🟢 EXCELLENT — On track to exceed targets"
    elif health_score >= 50:
        status = "🟡 ON TRACK — Strong progress, push quick wins"
    elif health_score >= 25:
        status = "🟠 NEEDS PUSH — Targeted interventions required"
    else:
        status = "🔴 CRITICAL — Heavy onboarding required"

    return {
        "health_score": health_score,
        "health_status": status,
        "completion_rate": round(completion_rate, 1),
        "total": total,
        "completed": completed_count,
        "almost": almost_count
    }

def generate_outreach_templates(df: pd.DataFrame) -> Dict[str, str]:
    """Feature 2: Generates ready-to-send broadcast messaging templates."""
    almost_count = len(df[df["Campaign Status"] == "Almost Completed"])
    not_started_count = len(df[df["Campaign Status"] == "Not Started"])
    manual_count = len(df[df["Verification Status"] != "Verified"])

    return {
        "Quick Win Reminder": (
            f"🚀 **GDG Campaign Update**: {almost_count} students are just 1–2 badges away from "
            f"completing the Google Skills Campaign! Finish your remaining labs today to claim your recognition!"
        ),
        "Onboarding Push": (
            f"👋 **Getting Started Notice**: We noticed {not_started_count} participants haven't started their first "
            f"skill badge yet. Need help getting started? Check out our beginner guide link here!"
        ),
        "Private Profile Warning": (
            f"⚠️ **Action Required**: {manual_count} profile URLs could not be verified because they are set to private "
            f"or invalid. Please update your profile privacy settings to Public so your badges count!"
        )
    }

def process_results_dataframe(results: List[Dict[str, Any]]) -> pd.DataFrame:
    rows = []

    for r in results:
        url = r["url"]
        status = r["status"]
        count = r["badge_count"]
        
        category, action = classify_participant(count, status)
        priority = calculate_outreach_priority(count, status)
        remaining = max(0, TARGET_BADGES - count) if status == "Verified" else 0

        rows.append({
            "Google Skills Profile URL": url,
            "Verification Status": status,
            "Badges Earned": count,
            "Badges Remaining": remaining,
            "Campaign Status": category,
            "Outreach Priority": priority,
            "Recommended Action": action,
            "Error Details": r.get("error_msg", "")
        })

    return pd.DataFrame(rows)