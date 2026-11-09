"""Fetch approved public buyer criteria from Google Apps Script and regenerate buyers.js."""
import json
from pathlib import Path
from urllib.request import Request, urlopen

ENDPOINT = "https://script.google.com/macros/s/AKfycbzIkgcXt5dddq1bBz6UthyhwZZ9Ibpw42MymS6AKpvqSRjZyXqYT3BPI4Xw3fTKoKwE/exec"

with urlopen(Request(ENDPOINT, headers={"User-Agent": "BrownZDMWholesale-Sync/1.0"}), timeout=35) as response:
    payload = json.load(response)
if not isinstance(payload, dict) or not isinstance(payload.get("buyers"), list):
    raise ValueError("Expected JSON with a buyers list; existing website data unchanged")

allowed = {"commercial", "residential", "land"}
records = []
for item in payload["buyers"]:
    if not isinstance(item, dict):
        raise ValueError("Invalid buyer record")
    category = str(item.get("category", "")).strip().lower()
    if category not in allowed:
        raise ValueError("Invalid category; use Commercial, Residential or Land in the sheet")
    buyer_id = str(item.get("id", "")).strip()
    if not buyer_id or len(buyer_id) > 80:
        raise ValueError("Missing or invalid buyer ID")
    def clean(field):
        return str(item.get(field) or "").strip()[:700]
    low, high = clean("minPrice"), clean("maxPrice")
    budget = " – ".join(v for v in (low, high) if v)
    details = "; ".join(v for v in (clean("minimumSize"), clean("strategy"), ("Closing: " + clean("closingTimeline")) if clean("closingTimeline") else "") if v)
    records.append({"id": buyer_id, "category": category,
        "title": clean("title") or buyer_id, "markets": clean("markets"),
        "assetTypes": clean("assetTypes"), "budget": budget,
        "details": details, "updated": clean("updated"), "published": True})

output = "/* Automatically generated from approved PUBLIC buyer criteria. Do not edit manually. */\nwindow.BUYER_CRITERIA = " + json.dumps(records, ensure_ascii=False, indent=2).replace("<", "\\u003c") + ";\n"
Path("buyers.js").write_text(output, encoding="utf-8")
print(f"Synced {len(records)} approved public buyer criteria")
