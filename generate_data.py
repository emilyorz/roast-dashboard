#!/usr/bin/env python3
import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parent
ROASTS_DIR = ROOT / "roasts"
OUTPUT_PATH = ROOT / "data.js"

CTRL_TYPE_MAP = {
    0: "P",
    1: "F",
    2: "D",
}


def parse_datetime(raw_value):
    if raw_value is None:
        return None
    if isinstance(raw_value, (int, float)):
        ts = raw_value / 1000 if raw_value > 1e12 else raw_value
        return datetime.fromtimestamp(ts)
    if isinstance(raw_value, str):
        v = raw_value.strip()
        if not v:
            return None
        try:
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def to_float(raw_value):
    if isinstance(raw_value, (int, float)):
        return float(raw_value)
    if isinstance(raw_value, str):
        v = raw_value.strip()
        if not v:
            return None
        try:
            return float(v)
        except ValueError:
            return None
    return None


def format_duration(seconds):
    if not seconds or seconds <= 0:
        return "N/A"
    total = int(round(seconds))
    m, s = divmod(total, 60)
    return f"{m}m {s:02d}s"


def make_histogram(values, bin_size, start=None, end=None, unit=""):
    if not values:
        return {"labels": [], "counts": [], "binSize": bin_size, "unit": unit}

    lo = min(values) if start is None else start
    hi = max(values) if end is None else end

    lo_bin = int(lo // bin_size) * bin_size
    hi_bin = int((hi + bin_size - 1) // bin_size) * bin_size

    if hi_bin == lo_bin:
        hi_bin += bin_size

    labels = []
    counts = []

    cur = lo_bin
    while cur < hi_bin:
        nxt = cur + bin_size
        labels.append(f"{cur:g}-{nxt:g}{unit}")
        counts.append(0)
        cur = nxt

    for value in values:
        idx = int((value - lo_bin) // bin_size)
        idx = max(0, min(idx, len(counts) - 1))
        counts[idx] += 1

    return {
        "labels": labels,
        "counts": counts,
        "binSize": bin_size,
        "unit": unit,
    }


def load_roasts():
    roasts = []
    for path in sorted(ROASTS_DIR.iterdir()):
        if not path.is_file():
            continue
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(record, dict):
            roasts.append(record)
    return roasts


ROAST_LEVELS = ["Light", "Medium", "MediumDark", "Dark", "Unknown"]


def classify_roast_level(drop_temp):
    if drop_temp is None:
        return "Unknown"
    if drop_temp < 185:
        return "Light"
    if drop_temp < 200:
        return "Medium"
    if drop_temp < 210:
        return "MediumDark"
    return "Dark"


def build_data(roasts):
    now = datetime.now()
    week_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = week_start - timedelta(days=week_start.weekday())

    parsed_dates = []
    roast_times = []
    charge_temps = []
    drop_temps = []
    weights = []
    monthly_counts = Counter()
    roast_level_counts = Counter()
    roast_level_by_month = defaultdict(lambda: Counter())

    action_counts = Counter({"F": 0, "P": 0, "D": 0})
    action_percentages = defaultdict(list)
    sequence_steps = defaultdict(list)

    for record in roasts:
        dt = parse_datetime(record.get("dateTime"))
        if dt:
            parsed_dates.append(dt)
            monthly_counts[dt.strftime("%Y-%m")] += 1

        total_time = to_float(record.get("totalRoastTime"))
        if total_time and total_time > 0:
            roast_times.append(total_time)

        charge = to_float(record.get("beanChargeTemperature"))
        if charge is not None and charge > 100:  # filter out 0/invalid charge temps
            charge_temps.append(charge)

        drop = to_float(record.get("beanDropTemperature"))
        if drop is not None:
            drop_temps.append(drop)

        level = classify_roast_level(drop)
        roast_level_counts[level] += 1
        if dt:
            roast_level_by_month[dt.strftime("%Y-%m")][level] += 1

        weight = to_float(record.get("weightGreen"))
        if weight and weight > 0:
            weights.append(weight)

        events = []
        action_time_list = (record.get("actions") or {}).get("actionTimeList") or []
        for action in action_time_list:
            if not isinstance(action, dict):
                continue
            name = CTRL_TYPE_MAP.get(action.get("ctrlType"))
            if not name:
                continue

            idx = action.get("index")
            value = action.get("value")
            idx = to_float(idx)
            value = to_float(value)
            if idx is None:
                continue

            total = total_time if total_time and total_time > 0 else None
            if total:
                pct = max(0.0, min(100.0, (float(idx) / float(total)) * 100.0))
                action_percentages[name].append(pct)

            action_counts[name] += 1
            events.append({
                "name": name,
                "index": float(idx),
                "value": value,
                "percent": pct if total else None,
            })

        events.sort(key=lambda x: x["index"])
        for pos, event in enumerate(events[:8]):
            sequence_steps[pos].append(event)

    parsed_dates.sort()
    start_date = parsed_dates[0].strftime("%Y-%m-%d") if parsed_dates else None
    end_date = parsed_dates[-1].strftime("%Y-%m-%d") if parsed_dates else None

    this_month_count = sum(1 for d in parsed_dates if d.year == now.year and d.month == now.month)
    this_week_count = sum(1 for d in parsed_dates if d >= week_start)

    avg_time = mean(roast_times) if roast_times else 0

    monthly_labels = sorted(monthly_counts.keys())
    monthly_values = [monthly_counts[label] for label in monthly_labels]

    time_hist = make_histogram(roast_times, bin_size=30, unit="s")

    temp_all = charge_temps + drop_temps
    if temp_all:
        temp_start = int(min(temp_all) // 5) * 5
        temp_end = int((max(temp_all) + 4) // 5) * 5
        charge_hist = make_histogram(charge_temps, bin_size=5, start=temp_start, end=temp_end, unit="C")
        drop_hist = make_histogram(drop_temps, bin_size=5, start=temp_start, end=temp_end, unit="C")
    else:
        charge_hist = make_histogram([], 5, unit="C")
        drop_hist = make_histogram([], 5, unit="C")

    weight_hist = make_histogram(weights, bin_size=50, unit="g")

    avg_percent_by_type = {
        key: round(mean(vals), 2) if vals else None
        for key, vals in action_percentages.items()
    }
    for key in ["F", "P", "D"]:
        avg_percent_by_type.setdefault(key, None)

    average_sequence = []
    for step in sorted(sequence_steps.keys()):
        entries = sequence_steps[step]
        names = [e["name"] for e in entries]
        mode_name = Counter(names).most_common(1)[0][0] if names else None

        percents = [e["percent"] for e in entries if isinstance(e.get("percent"), (int, float))]
        values = [e["value"] for e in entries if isinstance(e.get("value"), (int, float))]

        average_sequence.append({
            "step": step + 1,
            "name": mode_name,
            "avgPercent": round(mean(percents), 2) if percents else None,
            "avgValue": round(mean(values), 2) if values else None,
            "sampleSize": len(entries),
        })

    return {
        "meta": {
            "generatedAt": datetime.now().isoformat(timespec="seconds"),
            "totalRoasts": len(roasts),
            "startDate": start_date,
            "endDate": end_date,
        },
        "kpis": {
            "totalRoasts": len(roasts),
            "thisMonth": this_month_count,
            "thisWeek": this_week_count,
            "avgRoastTimeSec": round(avg_time, 2),
            "avgRoastTimeLabel": format_duration(avg_time),
            "dateRange": f"{start_date} ~ {end_date}" if start_date and end_date else "N/A",
        },
        "monthlyTrend": {
            "labels": monthly_labels,
            "counts": monthly_values,
        },
        "roastTimeHistogram": time_hist,
        "temperatureHistogram": {
            "labels": charge_hist["labels"],
            "chargeCounts": charge_hist["counts"],
            "dropCounts": drop_hist["counts"],
            "binSize": 5,
            "unit": "C",
        },
        "weightHistogram": {
            "labels": weight_hist["labels"],
            "counts": weight_hist["counts"],
            "recordedCount": len(weights),
            "missingCount": len(roasts) - len(weights),
            "binSize": 50,
            "unit": "g",
        },
        "roastLevel": {
            "counts": {level: roast_level_counts.get(level, 0) for level in ROAST_LEVELS},
            "roastLevelByMonth": {
                "labels": monthly_labels,
                **{
                    level: [roast_level_by_month[m].get(level, 0) for m in monthly_labels]
                    for level in ROAST_LEVELS
                },
            },
        },
        "actionBehavior": {
            "countByType": {
                "F": action_counts["F"],
                "P": action_counts["P"],
                "D": action_counts["D"],
            },
            "avgPercentByType": avg_percent_by_type,
            "averageSequence": average_sequence,
        },
    }


def write_data_js(data):
    payload = json.dumps(data, ensure_ascii=False, indent=2)
    OUTPUT_PATH.write_text(f"const ROAST_DATA = {payload};\n", encoding="utf-8")


def main():
    roasts = load_roasts()
    data = build_data(roasts)
    write_data_js(data)
    print(f"Loaded {len(roasts)} roast files from {ROASTS_DIR}")
    print(f"Wrote dashboard data to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
