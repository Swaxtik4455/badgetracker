import time
import requests
from urllib.parse import urlparse
from typing import Dict, Any, List

ALLOWED_DOMAINS = {"skills.google", "www.skills.google", "cloudskillsboost.google", "www.cloudskillsboost.google"}

class ProfileScraper:
    def __init__(self, delay_seconds: float = 0.3, timeout_seconds: int = 10):
        self.delay_seconds = delay_seconds
        self.timeout_seconds = timeout_seconds
        self.headers = {
            "User-Agent": "SkillTrack-GDG-Verifier/1.0 (+https://github.com/your-username/skilltrack)"
        }

    def is_safe_url(self, url: str) -> bool:
        """Validates URL scheme and restricts requests strictly to official Google domains."""
        try:
            parsed = urlparse(url.strip())
            return (
                parsed.scheme == "https" and 
                parsed.netloc.lower() in ALLOWED_DOMAINS and
                bool(parsed.path)
            )
        except Exception:
            return False

    def fetch_profile(self, url: str) -> Dict[str, Any]:
        url_clean = str(url).strip()

        # Input Sanitization Check
        if not self.is_safe_url(url_clean):
            return {
                "url": url_clean,
                "status": "Invalid / Unsafe URL",
                "badge_count": 0,
                "error_msg": "URL rejected: Scheme must be HTTPS and domain must be skills.google"
            }

        time.sleep(self.delay_seconds)

        try:
            response = requests.get(
                url_clean, 
                headers=self.headers, 
                timeout=self.timeout_seconds,
                allow_redirects=True
            )
            
            if response.status_code == 404:
                return {"url": url_clean, "status": "Manual Verification Required", "badge_count": 0, "error_msg": "Profile non-existent (404)."}
            elif response.status_code != 200:
                return {"url": url_clean, "status": "Manual Verification Required", "badge_count": 0, "error_msg": f"HTTP {response.status_code}"}
                
            if "private" in response.text.lower():
                return {"url": url_clean, "status": "Private Profile", "badge_count": 0, "error_msg": "User profile set to private."}

            # Badge parsing logic...
            count = response.text.count("badge-item") # Example matching existing scraper logic
            return {"url": url_clean, "status": "Verified", "badge_count": count, "error_msg": None}

        except requests.Timeout:
            return {"url": url_clean, "status": "Manual Verification Required", "badge_count": 0, "error_msg": "Connection timed out."}
        except requests.RequestException as e:
            return {"url": url_clean, "status": "Manual Verification Required", "badge_count": 0, "error_msg": f"Network error: {str(e)}"}