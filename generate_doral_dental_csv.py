"""
Generate Doral FL Dental Offices - Low Online Presence CSV from researched data.
Outputs doral_dental_low_presence.csv (HIGH + MEDIUM opportunity only).
"""

import csv
from doral_dental_data import PRACTICES

OUTPUT_FILE = "doral_dental_low_presence.csv"

FIELDNAMES = [
    "practice_name",
    "doctor_name",
    "specialty",
    "address",
    "city",
    "state",
    "zip",
    "phone",
    "email",
    "website",
    "has_facebook",
    "has_instagram",
    "has_twitter",
    "has_linkedin",
    "has_youtube",
    "has_tiktok",
    "social_platforms_count",
    "presence_score",
    "opportunity_tier",
    "website_quality_notes",
    "key_opportunity",
]


def main():
    leads = [p for p in PRACTICES if p["opportunity_tier"] in ("HIGH", "MEDIUM")]
    leads.sort(key=lambda p: (p["opportunity_tier"] != "HIGH", p["presence_score"]))

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(leads)

    high = sum(1 for p in leads if p["opportunity_tier"] == "HIGH")
    med  = sum(1 for p in leads if p["opportunity_tier"] == "MEDIUM")
    print(f"Saved {len(leads)} leads to {OUTPUT_FILE}")
    print(f"  HIGH opportunity: {high}")
    print(f"  MEDIUM opportunity: {med}")


if __name__ == "__main__":
    main()
