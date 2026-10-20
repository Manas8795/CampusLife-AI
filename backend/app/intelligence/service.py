import json
import datetime
from sqlalchemy.orm import Session
from backend.app.intelligence.models import StudentState, IntelligenceRisk, IntelligenceInsight
from backend.app.intelligence.schemas import (
    UnifiedStudentStateOut, BaselineMetric, CrossDomainRiskOut, IntelligenceInsightOut
)
from backend.app.study.service import StudyService
from backend.app.health.service import HealthService
from backend.app.expenses.service import ExpenseService
from backend.app.travel.service import TravelService

class IntelligenceService:
    @staticmethod
    def evaluate_student_state(db: Session, user_id: int) -> UnifiedStudentStateOut:
        now = datetime.datetime.now()

        # 1. Fetch domain signals
        productivity = StudyService.calculate_productivity_risk(db, user_id)
        wellness = HealthService.get_wellness_summary(db, user_id)
        stress = HealthService.predict_stress(db, user_id)
        financial_forecast = ExpenseService.forecast_out_of_cash(db, user_id)
        current_month = datetime.date.today().strftime("%Y-%m")
        budget_status = ExpenseService.get_budget_status(db, user_id, current_month)
        trips = TravelService.get_trips(db, user_id)

        # 2. Check travel conflicts for upcoming trips
        upcoming_trips = [t for t in trips if t.status in ["PLANNING", "CONFIRMED", "UPCOMING"]]
        travel_conflicts = []
        for t in upcoming_trips:
            c = TravelService.check_academic_conflicts(db, user_id, t.id)
            if c.has_conflict:
                travel_conflicts.extend(c.conflicts)

        # 3. Personal Baselines
        baselines = [
            BaselineMetric(
                metric="Sleep Hours",
                personal_baseline=wellness.sleep_baseline,
                current_value=wellness.average_sleep_7d,
                deviation=round(wellness.average_sleep_7d - wellness.sleep_baseline, 2),
                status="AT_RISK" if wellness.average_sleep_7d < 6.0 else ("DECREASED" if wellness.average_sleep_7d < wellness.sleep_baseline else "NORMAL")
            ),
            BaselineMetric(
                metric="Daily Study Hours",
                personal_baseline=3.5,
                current_value=wellness.average_study_7d,
                deviation=round(wellness.average_study_7d - 3.5, 2),
                status="ELEVATED" if wellness.average_study_7d > 5.5 else "NORMAL"
            ),
            BaselineMetric(
                metric="Task Completion Rate",
                personal_baseline=0.75,
                current_value=productivity.completion_rate,
                deviation=round(productivity.completion_rate - 0.75, 2),
                status="AT_RISK" if productivity.completion_rate < 0.5 else "NORMAL"
            )
        ]

        # 4. Cross-Domain Correlation & Risk Detection
        detected_risks: list[CrossDomainRiskOut] = []
        insights: list[IntelligenceInsightOut] = []
        compound_score = 0.1

        # Check Academic + Wellness Overload
        academic_wellness_signals = []
        if productivity.risk_level in ["MEDIUM", "HIGH"]:
            academic_wellness_signals.append(f"Task productivity risk is {productivity.risk_level}")
        if wellness.average_sleep_7d < 6.5:
            academic_wellness_signals.append(f"Recent sleep ({wellness.average_sleep_7d}h) is below healthy baseline")
        if stress.stress_level == "HIGH":
            academic_wellness_signals.append("High wellness stress level reported")

        if len(academic_wellness_signals) >= 2:
            score = 0.75 if stress.stress_level == "HIGH" else 0.55
            detected_risks.append(CrossDomainRiskOut(
                risk_type="ACADEMIC_WELLNESS_OVERLOAD",
                severity="HIGH" if score >= 0.7 else "MEDIUM",
                score=score,
                confidence=0.88,
                supporting_signals=academic_wellness_signals
            ))
            insights.append(IntelligenceInsightOut(
                insight_type="ACADEMIC_WELLNESS",
                severity="HIGH",
                title="Academic Workload & Sleep Deprivation Alert",
                evidence_signals=academic_wellness_signals,
                recommendation="Your academic load is elevated while sleep has dropped. Protect a 7-hour sleep window tonight to prevent burnout before deadlines."
            ))
            compound_score += 0.35

        # Check Travel + Academic Conflicts
        if travel_conflicts:
            conflict_signals = [f"{c.type}: {c.title} on {c.date}" for c in travel_conflicts]
            detected_risks.append(CrossDomainRiskOut(
                risk_type="TRAVEL_SCHEDULE_CONFLICT",
                severity="HIGH",
                score=0.8,
                confidence=0.92,
                supporting_signals=conflict_signals
            ))
            insights.append(IntelligenceInsightOut(
                insight_type="TRAVEL_ACADEMIC",
                severity="HIGH",
                title="Upcoming Travel Clashes With Academic Deadlines",
                evidence_signals=conflict_signals,
                recommendation="Reschedule or submit assignments early to avoid academic penalties during your travel."
            ))
            compound_score += 0.25

        # Check Financial Budget Burn Risk
        if financial_forecast.financial_risk_level in ["MEDIUM", "HIGH"] or budget_status.utilization_percentage >= 80.0:
            fin_signals = [
                f"Budget utilization is {budget_status.utilization_percentage}%",
                f"Runway estimated at ~{financial_forecast.estimated_days_remaining} days (INR {financial_forecast.daily_burn_rate}/day)"
            ]
            detected_risks.append(CrossDomainRiskOut(
                risk_type="FINANCIAL_RUNWAY_RISK",
                severity=financial_forecast.financial_risk_level,
                score=0.7 if financial_forecast.financial_risk_level == "HIGH" else 0.45,
                confidence=0.82,
                supporting_signals=fin_signals
            ))
            insights.append(IntelligenceInsightOut(
                insight_type="FINANCIAL",
                severity=financial_forecast.financial_risk_level,
                title="Elevated Spending Rate Against Monthly Budget",
                evidence_signals=fin_signals,
                recommendation="Consider limiting non-essential discretionary expenses over the next week to restore budget cushion."
            ))
            compound_score += 0.2

        # Check Academic-Financial Link: External Fatigue Indicator (Energy drinks / Coffee)
        from backend.app.expenses.models import Expense
        from backend.app.study.models import Task
        from backend.app.core.models import User

        all_user_expenses = db.query(Expense).filter(Expense.user_id == user_id).all()
        caffeine_kws = ["red bull", "espresso", "coffee", "cappuccino", "energy drink", "sting", "monster", "cafe", "latte"]
        caffeine_expenses = [e for e in all_user_expenses if any(k in (e.description or "").lower() for k in caffeine_kws)]
        caffeine_total = sum(e.amount for e in caffeine_expenses)

        # Check pending tasks due in 48 hours
        in_48h = now + datetime.timedelta(hours=48)
        pending_tasks = db.query(Task).filter(Task.user_id == user_id, Task.status != "COMPLETED").all()
        due_48h = [t for t in pending_tasks if t.due_date and t.due_date <= in_48h]

        if caffeine_expenses and (len(due_48h) >= 1 or wellness.average_sleep_7d < 6.5):
            fatigue_signals = [
                f"Logged INR {caffeine_total:.0f} across {len(caffeine_expenses)} café / energy drink purchases during exam crunch",
                f"Recent sleep baseline is {wellness.average_sleep_7d:.1f}h with {len(due_48h)} urgent submissions pending"
            ]
            detected_risks.append(CrossDomainRiskOut(
                risk_type="EXTERNAL_FATIGUE_INDICATOR",
                severity="HIGH" if caffeine_total >= 800 else "MEDIUM",
                score=0.72,
                confidence=0.88,
                supporting_signals=fatigue_signals
            ))
            insights.append(IntelligenceInsightOut(
                insight_type="WELLNESS_FINANCIAL_FATIGUE",
                severity="MEDIUM",
                title="Academic-Financial Fatigue Indicator: Elevated Stimulant Spending",
                evidence_signals=fatigue_signals,
                recommendation=f"High café/stimulant spending (INR {caffeine_total:.0f}) suggests fatigue compensation. Taper off caffeine past 4 PM to restore restorative slow-wave sleep."
            ))
            compound_score += 0.2

        # 5. Compound Risk Level & Proactive Intervention Trigger
        compound_score = min(1.0, round(compound_score, 2))

        # Check Cross-Domain Causality: 3+ tasks due in 48h AND sleep drops < 5.5h
        user_rec = db.query(User).filter(User.id == user_id).first()
        student_first_name = user_rec.full_name.split()[0] if (user_rec and user_rec.full_name) else "Alex"

        is_causal_compound_overload = (
            (len(due_48h) >= 3 or (len(due_48h) >= 1 and productivity.risk_level in ["MEDIUM", "HIGH"]))
            and wellness.average_sleep_7d < 5.5
        )

        if is_causal_compound_overload:
            burnout_risk_pct = min(95, int(65 + max(0, 5.5 - wellness.average_sleep_7d) * 15 + min(3, len(due_48h)) * 5))
            high_task = next((t.title for t in due_48h if t.priority == "HIGH"), (due_48h[0].title if due_48h else "Operating Systems"))
            low_task = next((t.title for t in due_48h if t.priority in ["LOW", "MEDIUM"] and t.title != high_task), "non-critical reading")

            compound_message = (
                f"{student_first_name}, you have {len(due_48h)} major submissions tomorrow and you only slept {wellness.average_sleep_7d:.1f} hours. "
                f"Your risk of burnout today is {burnout_risk_pct}%. I recommend we postpone your non-critical {low_task} by 24 hours "
                f"so you can focus on {high_task} and sleep by 11 PM tonight."
            )

            compound_risk_level = "HIGH"
            proactive_intervention = True
            proactive_reason = compound_message
            compound_score = max(compound_score, 0.88)
        elif compound_score >= 0.7 or any(r.severity == "HIGH" and r.risk_type == "ACADEMIC_WELLNESS_OVERLOAD" for r in detected_risks):
            compound_risk_level = "HIGH"
            proactive_intervention = True
            proactive_reason = "Compound overload detected: Approaching academic deadlines combined with reduced sleep and elevated stress."
        elif compound_score >= 0.4:
            compound_risk_level = "MEDIUM"
            proactive_intervention = False
            proactive_reason = None
        else:
            compound_risk_level = "LOW"
            proactive_intervention = False
            proactive_reason = None
            if not insights:
                insights.append(IntelligenceInsightOut(
                    insight_type="SUMMARY",
                    severity="LOW",
                    title="Student Co-Pilot Overview: Normal Operation",
                    evidence_signals=["All academic, wellness, financial, and travel signals within normal ranges"],
                    recommendation="Keep up the great momentum across your studies and wellness routines!"
                ))

        # 6. Save or update StudentState in database
        academic_dict = {
            "total_tasks": productivity.total_tasks,
            "pending_tasks": productivity.pending_tasks,
            "overdue_tasks": productivity.overdue_tasks,
            "productivity_risk": productivity.risk_level,
            "completion_rate": productivity.completion_rate
        }
        wellness_dict = {
            "avg_sleep_7d": wellness.average_sleep_7d,
            "avg_study_7d": wellness.average_study_7d,
            "stress_level": stress.stress_level
        }
        financial_dict = {
            "budget_spent": budget_status.current_spending,
            "budget_limit": budget_status.total_budget,
            "utilization_pct": budget_status.utilization_percentage,
            "days_runway": financial_forecast.estimated_days_remaining
        }
        travel_dict = {
            "upcoming_trips_count": len(upcoming_trips),
            "conflicts_count": len(travel_conflicts)
        }

        state_rec = db.query(StudentState).filter(StudentState.user_id == user_id).first()
        if not state_rec:
            state_rec = StudentState(
                user_id=user_id,
                academic_summary=json.dumps(academic_dict),
                wellness_summary=json.dumps(wellness_dict),
                financial_summary=json.dumps(financial_dict),
                travel_summary=json.dumps(travel_dict),
                compound_risk_level=compound_risk_level,
                compound_risk_score=compound_score,
                updated_at=now
            )
            db.add(state_rec)
        else:
            state_rec.academic_summary = json.dumps(academic_dict)
            state_rec.wellness_summary = json.dumps(wellness_dict)
            state_rec.financial_summary = json.dumps(financial_dict)
            state_rec.travel_summary = json.dumps(travel_dict)
            state_rec.compound_risk_level = compound_risk_level
            state_rec.compound_risk_score = compound_score
            state_rec.updated_at = now

        db.commit()

        return UnifiedStudentStateOut(
            user_id=user_id,
            updated_at=now,
            compound_risk_level=compound_risk_level,
            compound_risk_score=compound_score,
            academic_state=academic_dict,
            wellness_state=wellness_dict,
            financial_state=financial_dict,
            travel_state=travel_dict,
            baselines=baselines,
            detected_risks=detected_risks,
            priority_insights=insights,
            proactive_intervention_recommended=proactive_intervention,
            proactive_intervention_reason=proactive_reason
        )
