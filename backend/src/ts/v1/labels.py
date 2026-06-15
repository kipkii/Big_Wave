def assign_status_label(ts_score: float, growth_score: float, decline_risk: float) -> str:
    if decline_risk >= 70:
        return "Decline Risk"
    if ts_score >= 75 and growth_score >= 60:
        return "Big Wave"
    if ts_score >= 60:
        return "Rising"
    return "Watch"
