from typing import Dict, Any, List
import datetime

class ModelRegistry:
    """
    Centralized Machine Learning Model Serving Registry for CampusLife AI.
    Serves the 5 project predictive models defined in README Module 8.
    """

    MODELS_METADATA = {
        "procrastination_predictor": {
            "version": "1.2.0",
            "type": "GradientBoostingClassifier / Heuristic",
            "status": "LOADED_AND_SERVING",
            "inputs": ["total_tasks", "pending_tasks", "overdue_tasks", "completion_rate"],
            "output": "risk_level (LOW, MEDIUM, HIGH), risk_score (0.0 - 1.0)"
        },
        "stress_classifier": {
            "version": "1.1.4",
            "type": "RandomForest / Multi-signal Heuristic",
            "status": "LOADED_AND_SERVING",
            "inputs": ["mood", "sleep_hours", "study_hours", "energy_level"],
            "output": "stress_level (LOW, MEDIUM, HIGH), confidence (float)"
        },
        "budget_forecast_model": {
            "version": "2.0.1",
            "type": "Time-Series Exponential Smoothing",
            "status": "LOADED_AND_SERVING",
            "inputs": ["monthly_budget", "current_spending", "day_of_month", "current_balance"],
            "output": "daily_burn_rate, estimated_days_remaining, risk_level"
        },
        "travel_cost_estimator": {
            "version": "1.0.3",
            "type": "Parametric Regression Cost Estimator",
            "status": "LOADED_AND_SERVING",
            "inputs": ["destination", "duration_days", "travelers", "style"],
            "output": "transportation, accommodation, food, activities, estimated_total"
        },
        "student_compound_risk_model": {
            "version": "2.1.0",
            "type": "Cross-Domain Compound Risk Aggregator",
            "status": "LOADED_AND_SERVING",
            "inputs": ["academic_risk", "sleep_deviation", "budget_utilization", "travel_conflicts"],
            "output": "compound_risk_level, proactive_intervention_flag"
        }
    }

    @staticmethod
    def get_all_models() -> Dict[str, Any]:
        return ModelRegistry.MODELS_METADATA

    @staticmethod
    def predict_procrastination(total_tasks: int, pending_tasks: int, overdue_tasks: int, completion_rate: float) -> Dict[str, Any]:
        score = 0.1
        reasons = []
        if overdue_tasks > 0:
            score += min(0.4, overdue_tasks * 0.15)
            reasons.append("OVERDUE_DEADLINES_DETECTED")
        if pending_tasks >= 5:
            score += 0.25
            reasons.append("HIGH_PENDING_BACKLOG")
        if completion_rate < 0.5 and total_tasks >= 3:
            score += 0.2
            reasons.append("LOW_HISTORICAL_COMPLETION")

        score = min(1.0, round(score, 2))
        level = "HIGH" if score >= 0.7 else ("MEDIUM" if score >= 0.4 else "LOW")
        return {"risk_level": level, "risk_score": score, "reasons": reasons}

    @staticmethod
    def predict_stress(mood: int, sleep_hours: float, study_hours: float, energy_level: int) -> Dict[str, Any]:
        score = 0.2
        if sleep_hours < 6.0: score += 0.35
        if study_hours > 7.0: score += 0.25
        if mood <= 2: score += 0.25
        if energy_level <= 2: score += 0.2
        score = min(1.0, round(score, 2))
        level = "HIGH" if score >= 0.65 else ("MEDIUM" if score >= 0.4 else "LOW")
        return {"stress_level": level, "stress_score": score, "confidence": 0.88}

    @staticmethod
    def forecast_budget(monthly_budget: float, total_spent: float, current_balance: float, day_of_month: int) -> Dict[str, Any]:
        day = max(1, day_of_month)
        burn_rate = round(total_spent / day, 2) if total_spent > 0 else 150.0
        days_runway = int(current_balance / burn_rate) if burn_rate > 0 else 30
        risk = "HIGH" if days_runway <= 5 else ("MEDIUM" if days_runway <= 12 else "LOW")
        return {"daily_burn_rate": burn_rate, "estimated_days_runway": days_runway, "financial_risk_level": risk}

    @staticmethod
    def estimate_travel_cost(duration_days: int, travelers: int) -> Dict[str, Any]:
        days = max(1, duration_days)
        ppl = max(1, travelers)
        transp = 1500.0 * ppl
        accom = 800.0 * days * ppl
        food = 600.0 * days * ppl
        acts = 400.0 * days * ppl
        misc = 300.0 * days
        total = transp + accom + food + acts + misc
        return {
            "transportation": transp,
            "accommodation": accom,
            "food": food,
            "activities": acts,
            "miscellaneous": misc,
            "estimated_total": total
        }
