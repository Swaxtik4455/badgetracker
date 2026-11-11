import os
import re
import time
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Any

# Targeted Google Skill Badge identifiers / filter
REQUIRED_BADGE_TARGET = 10

class ProfileScraper:
    def __init__(self, delay_seconds: float = 0.5):
        self.delay_seconds = delay_seconds
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }

    def fetch_profile(self, url: str) -> Dict[str, Any]:
        """
        Fetches and parses a single Google Skills public profile URL.
        Returns detailed status, earned skill badges, and count.
        """
        url = url.strip()
        result = {
            "url": url,
            "status": "Unknown",
            "is_valid": False,
            "badge_count": 0,
            "badges": [],
            "error_msg": None
        }

        if not url or not url.startswith("http"):
            result["status"] = "Invalid URL"
            result["error_msg"] = "URL format is invalid."
            return result

        time.sleep(self.delay_seconds)  # Rate limiting

        try:
            response = requests.get(url, headers=self.headers, timeout=12)
            
            if response.status_code == 404:
                result["status"] = "Manual Verification Required"
                result["error_msg"] = "Profile not found (404)."
                return result
            elif response.status_code != 200:
                result["status"] = "Manual Verification Required"
                result["error_msg"] = f"HTTP Error {response.status_code}"
                return result

            html = response.text
            soup = BeautifulSoup(html, "html.parser")

            # Check for explicit private account messaging
            if "private" in html.lower() and "profile" in html.lower():
                if not soup.find_all(class_=re.compile("badge|card")):
                    result["status"] = "Private Profile"
                    result["error_msg"] = "User profile is set to private."
                    return result

            # Parse skill badges from HTML DOM
            # Google Skills profile badges live in badge cards/lists
            badge_items = []
            
            # Selector strategies for robustness across profile layout updates
            badge_elements = soup.select(".public-profile-badge, .profile-badge, [class*='badge-card']")
            
            if not badge_elements:
                # Fallback: regex search on structured page data if elements dynamically hydratable
                badge_elements = soup.find_all("div", attrs={"data-badge-title": True})

            for elem in badge_elements:
                title_elem = elem.select_one(".badge-title, .title, h3, header") or elem
                date_elem = elem.select_one(".earned-date, .date, time")
                
                title = title_elem.get_text(strip=True) if title_elem else "Unknown Skill Badge"
                earned_date = date_elem.get_text(strip=True) if date_elem else "N/A"

                # Filter out general non-badge entries if present
                if title and ("badge" in title.lower() or "skill" in title.lower() or len(title) > 3):
                    badge_items.append({"title": title, "date": earned_date})

            # Deduplicate badges by title
            unique_badges = {b["title"]: b for b in badge_items}.values()
            badge_list = list(unique_badges)

            result["badges"] = badge_list
            result["badge_count"] = len(badge_list)
            result["is_valid"] = True
            result["status"] = "Verified"

        except requests.RequestException as e:
            result["status"] = "Manual Verification Required"
            result["error_msg"] = f"Network connectivity issue: {str(e)}"
        except Exception as e:
            result["status"] = "Manual Verification Required"
            result["error_msg"] = f"Parsing failure: {str(e)}"

        return result

    def batch_process(self, urls: List[str], progress_callback=None) -> List[Dict[str, Any]]:
        results = []
        total = len(urls)
        for idx, url in enumerate(urls):
            res = self.fetch_profile(url)
            results.append(res)
            if progress_callback:
                progress_callback((idx + 1) / total)
        return results