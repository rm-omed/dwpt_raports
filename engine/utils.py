from datetime import datetime, timedelta

def get_next_due_date(schedule):
    today = datetime.today()
    s_type = schedule.get("type", "daily")
    s_days = schedule.get("days", [])
    s_months = schedule.get("months", [])

    if s_type == "daily":
        return today + timedelta(days=1)

    elif s_type == "weekly":
        weekday = today.weekday()
        upcoming = sorted([d for d in s_days if d > weekday])
        next_day = upcoming[0] if upcoming else s_days[0]
        days_ahead = (next_day - weekday) % 7
        return today + timedelta(days=days_ahead or 7)

    elif s_type == "monthly":
        day = today.day
        future_days = sorted([d for d in s_days if d > day])
        next_day = future_days[0] if future_days else s_days[0]
        next_month = today.month if future_days else (today.month % 12 + 1)
        year = today.year + (1 if next_month == 1 and today.month == 12 else 0)
        return datetime(year, next_month, min(next_day, 28))

    elif s_type == "yearly":
        for m in sorted(s_months):
            for d in sorted(s_days):
                try:
                    candidate = datetime(today.year, m, d)
                    if candidate > today:
                        return candidate
                except:
                    continue
        return datetime(today.year + 1, s_months[0], s_days[0])

    elif s_type == "semi_annual":
        month = today.month
        next_month = 7 if month < 7 else 1
        next_year = today.year + 1 if month >= 7 else today.year
        return datetime(next_year, next_month, s_days[0])

    return today


def compute_monthly_summary(weeks):
    """
    Aggregates 4 weeks of data into a single dict with keys like "01_1", ..., "23_4", and totals.
    Expects: weeks = list of 4 lists, each with 23 rows of dicts like {"01_1": 3, "01_2": 5, ...}
    Returns: dict suitable for placeholder replacement
    """
    summary = {}
    row_count = 23
    col_count = 4

    # Initialize empty table
    for row in range(1, row_count + 1):
        for col in range(1, col_count + 1):
            key = f"{row:02}_{col}"
            summary[key] = 0

    # Sum weekly data
    for week in weeks:
        for row_idx, row_data in enumerate(week):
            for col_idx in range(col_count):
                key = f"{row_idx + 1:02}_{col_idx + 1}"
                value = row_data.get(key, 0)
                try:
                    summary[key] += float(value)
                except ValueError:
                    pass  # ignore invalid inputs

    # Calculate totals per column
    for col in range(1, col_count + 1):
        total = sum(summary[f"{row:02}_{col}"] for row in range(1, row_count + 1))
        summary[f"total_{col}"] = int(total)

    # Convert all values to strings (for placeholder replacement)
    return {k: str(int(v)) if isinstance(v, float) else str(v) for k, v in summary.items()}