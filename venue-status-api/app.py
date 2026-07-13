import os
import requests
import json
import re
from datetime import datetime, timezone
from flask import Flask, jsonify

app = Flask(__name__)

CHANGEDETECTION_URL = os.environ.get("CHANGEDETECTION_URL", "http://changedetection:5000")
API_KEY = os.environ.get("CHANGEDETECTION_API_KEY", "")
DATASTORE_PATH = os.environ.get("DATASTORE_PATH", "/datastore")
SEVEN_DAYS = 7 * 24 * 60 * 60

# Simple in-memory cache for date_created (avoids 250 detail calls on every request)
_date_created_cache = {}


def get_date_created(watch_id):
    if watch_id in _date_created_cache:
        return _date_created_cache[watch_id]
    try:
        r = requests.get(
            f"{CHANGEDETECTION_URL}/api/v1/watch/{watch_id}",
            headers={"x-api-key": API_KEY},
            timeout=5,
        )
        created = r.json().get("date_created", 0)
    except Exception:
        created = 0
    _date_created_cache[watch_id] = created
    return created


def get_llm_change_summary(watch_id, default_venue_name):
    watch_json_path = os.path.join(DATASTORE_PATH, watch_id, "watch.json")
    if not os.path.exists(watch_json_path):
        return None
    
    try:
        with open(watch_json_path, "r", encoding="utf-8") as f:
            watch_data = json.load(f)
            
        summary_text = watch_data.get("_llm_change_summary")
        if not summary_text:
            return None
            
        # Clean markdown code block wraps (e.g. ```json ... ```)
        cleaned_text = summary_text.strip()
        match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", cleaned_text, re.DOTALL | re.IGNORECASE)
        if match:
            cleaned_text = match.group(1).strip()
            
        # Try to parse as JSON first
        try:
            parsed_summary = json.loads(cleaned_text)
            if isinstance(parsed_summary, dict) and "gigs" in parsed_summary:
                # Apply fallback venue name for single-venue watches
                for gig in parsed_summary["gigs"]:
                    if not gig.get("venue"):
                        gig["venue"] = default_venue_name
                return parsed_summary
        except json.JSONDecodeError:
            # Not valid JSON, return raw summary text (markdown/string)
            pass
            
        return summary_text
    except Exception as e:
        app.logger.error(f"Error reading LLM summary for watch {watch_id}: {e}")
        return None


def fmt_date(ts):
    if not ts:
        return None
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")


@app.route("/venue-change-status")
def venue_change_status():
    try:
        watches = requests.get(
            f"{CHANGEDETECTION_URL}/api/v1/watch",
            headers={"x-api-key": API_KEY},
            timeout=10,
        ).json()
    except Exception as e:
        return jsonify({"error": str(e)}), 503

    now_ts = datetime.now(timezone.utc).timestamp()
    seven_days_ago = now_ts - SEVEN_DAYS

    # Deduplicate by LML UUID — keep most recently changed watch per venue
    deduped = {}
    for watch_id, watch in watches.items():
        title = watch.get("title") or watch.get("url", "")
        parts = title.split(" | ")
        name = parts[0].strip()
        lml_uuid = parts[1].strip() if len(parts) > 1 else None
        key = lml_uuid or watch_id

        location, venue_name = ("", name)
        if ": " in name:
            location, venue_name = name.split(": ", 1)

        last_changed = watch.get("last_changed", 0)
        if key not in deduped or last_changed > deduped[key]["last_changed"]:
            deduped[key] = {
                "lml_uuid": lml_uuid,
                "name": venue_name,
                "location": location,
                "url": watch.get("url", ""),
                "last_changed": last_changed,
                "last_checked": watch.get("last_checked", 0),
                "watch_id": watch_id,
            }

    results = []
    for key, d in sorted(deduped.items(), key=lambda x: (x[1]["location"], x[1]["name"])):
        last_changed = d["last_changed"]

        if last_changed and last_changed > seven_days_ago:
            status = "changed"
            since = fmt_date(last_changed)
        else:
            status = "no_change"
            if last_changed:
                since = fmt_date(last_changed)
            else:
                created = get_date_created(d["watch_id"])
                since = fmt_date(created)

        results.append({
            "lml_uuid": d["lml_uuid"],
            "name": d["name"],
            "location": d["location"],
            "status": status,
            "since": since,
            "last_checked": fmt_date(d["last_checked"]),
            "url": d["url"],
            "ai_summary": get_llm_change_summary(d["watch_id"], d["name"]),
        })

    return jsonify(results)


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
