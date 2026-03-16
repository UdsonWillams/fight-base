from datetime import datetime, timezone
from typing import Optional


def parse_date(date_str: str) -> Optional[datetime]:
    if not date_str or date_str.strip() == "" or date_str.strip() == "--":
        return None

    date_str = date_str.strip()
    formats = [
        "%B %d, %Y",  # September 06, 2025
        "%b %d, %Y",  # Mar 09, 1985
        "%Y-%m-%d",  # 1985-03-09
        "%d/%m/%Y",  # 09/03/1985
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue

    return None


def parse_height_to_cm(height_str: str) -> Optional[float]:
    if not height_str or height_str.strip() == "" or height_str.strip() == "--":
        return None
    try:
        height_str = height_str.strip().replace('"', "").replace("'", " ")
        parts = height_str.split()

        if len(parts) == 2:
            feet = float(parts[0])
            inches = float(parts[1])
            return round((feet * 30.48) + (inches * 2.54), 2)
        elif len(parts) == 1:
            val = float(parts[0])
            if val < 10:
                return round(val * 30.48, 2)
            return round(val, 2)
    except (ValueError, IndexError):
        return None
    return None


def parse_reach_to_cm(reach_str: str) -> Optional[float]:
    if not reach_str or reach_str.strip() == "" or reach_str.strip() == "--":
        return None
    try:
        reach_str = reach_str.strip().replace('"', "")
        val = float(reach_str)
        if val < 100:
            return round(val * 2.54, 2)
        return round(val, 2)
    except ValueError:
        return None


def parse_weight_to_lbs(weight_str: str) -> Optional[float]:
    if not weight_str or weight_str.strip() == "" or weight_str.strip() == "--":
        return None
    try:
        weight_str = weight_str.strip().lower().replace("lbs.", "").strip()
        return float(weight_str)
    except ValueError:
        return None


# Test values from CSV
print("--- TESTING DOB ---")
dob_val = "Mar 09, 1985"
print(f"Result: {parse_date(dob_val)}")

print("\n--- TESTING HEIGHT ---")
height_val = "5' 8\""
print(f"Result: {parse_height_to_cm(height_val)} cm")

print("\n--- TESTING WEIGHT ---")
weight_val = "135 lbs."
print(f"Result: {parse_weight_to_lbs(weight_val)} lbs")

print("\n--- TESTING REACH ---")
reach_val = '68"'
print(f"Result: {parse_reach_to_cm(reach_val)} cm")
