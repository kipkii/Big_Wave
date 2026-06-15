def generate_rule_report(keyword: str, ts_result: dict, data_mode: str) -> dict:
    mode_note = "sample data 기반" if data_mode == "sample" else "real collector 기반"
    label = ts_result["status_label"]
    return {
        "summary": f"{keyword}의 현재 상태는 {label}입니다. 이 결과는 {mode_note} 분석입니다.",
        "evidence": (
            f"TS {ts_result['ts_score']}, growth {ts_result['growth_score']}, "
            f"reaction {ts_result['reaction_score']}, decline risk {ts_result['decline_risk']}를 종합했습니다."
        ),
        "risk": "real mode에서는 API 응답 품질과 수집 기간에 따라 결과가 크게 달라질 수 있습니다.",
        "recommendation": "키워드 세트와 기간을 바꿔 반복 분석하고, raw preview로 수집 품질을 먼저 확인하세요.",
    }
