import argparse
import sys
import pandas as pd
from scrapper import ProfileScraper
from storage import save_run
from analytics import (
    process_results_dataframe, 
    calculate_campaign_health, 
    generate_outreach_templates
)

def print_summary(df: pd.DataFrame):
    health = calculate_campaign_health(df)
    templates = generate_outreach_templates(df)

    print("\n" + "="*85)
    print(" ⚡ SKILLTRACK CLI — CAMPAIGN SUMMARY OVERVIEW")
    print("="*85)
    print(f" Total Profiles Processed : {health['total']}")
    print(f" Campaign Health Index    : {health['health_score']}% ({health['health_status']})")
    print(f" Campaign Completed (10/10): {health['completed']}")
    print(f" Almost Completed (8-9)   : {health['almost']}")
    print(f" Completion Percentage    : {health['completion_rate']}%")
    print("-" * 85)
    print(" 📢 QUICK ACTION TEMPLATE (Copy & Paste for Discord/WhatsApp):")
    print(f" \"{templates['Quick Win Reminder']}\"")
    print("="*85 + "\n")

def print_table(df: pd.DataFrame, priority_filter: str = None):
    header = f"{'PROFILE URL':<40} | {'STATUS':<10} | {'BADGES':<6} | {'PRIORITY':<24} | {'CATEGORY':<18}"
    print(header)
    print("-" * len(header))
    
    for _, row in df.iterrows():
        prio_str = str(row["Outreach Priority"])
        if priority_filter and priority_filter.lower() not in prio_str.lower():
            continue
            
        url_str = str(row["Google Skills Profile URL"])
        short_url = url_str[:37] + "..." if len(url_str) > 40 else url_str
        curr_str = str(row["Badges Earned"])
        status_str = str(row["Verification Status"])
        category_str = str(row["Campaign Status"])
        
        print(f"{short_url:<40} | {status_str:<10} | {curr_str:<6} | {prio_str:<24} | {category_str:<18}")
    print("-" * len(header))

def main():
    parser = argparse.ArgumentParser(description="SkillTrack CLI — GDG Google Skills Campaign Tracker")
    parser.add_argument("csv_path", help="Path to input CSV file containing 'Google Skills Profile URL'")
    parser.add_argument("--export", help="Path to export output CSV report (e.g. output.csv)")
    parser.add_argument("--priority", help="Filter display by priority (e.g. 'HIGH', 'MEDIUM', 'LOW')")
    
    args = parser.parse_args()

    try:
        df_raw = pd.read_csv(args.csv_path)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        sys.exit(1)

    url_col = "Google Skills Profile URL"
    if url_col not in df_raw.columns:
        print(f"Error: Required column '{url_col}' not found in CSV.")
        sys.exit(1)

    urls = df_raw[url_col].dropna().unique().tolist()
    print(f"Loaded {len(urls)} unique URLs. Starting profile verification...")

    scraper = ProfileScraper(delay_seconds=0.3)
    raw_results = []
    
    for idx, url in enumerate(urls, start=1):
        print(f"[{idx}/{len(urls)}] Verifying: {url}")
        res = scraper.fetch_profile(url)
        raw_results.append(res)

    save_run(raw_results)
    analysis_df = process_results_dataframe(raw_results)
    
    print_summary(analysis_df)
    print_table(analysis_df, priority_filter=args.priority)

    if args.export:
        analysis_df.to_csv(args.export, index=False)
        print(f"\n[✓] Detailed report exported successfully to: {args.export}")

if __name__ == "__main__":
    main()