import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.health.models import HealthRecord, WellnessRecommendation
from backend.app.health.schemas import HealthLogCreate, StressPredictionOut, WellnessSummaryOut

DEFAULT_SLEEP_BASELINE = 7.5

class HealthService:
    @staticmethod
    def _compute_stress(mood: int, sleep_hours: float, study_hours: float, energy_level: int):
        score = 0.2
        signals = []

        if sleep_hours < 6.0:
            score += 0.3
            signals.append("LOW_SLEEP_HOURS")
        elif sleep_hours < 7.0:
            score += 0.15
            signals.append("SUBOPTIMAL_SLEEP")

        if study_hours > 7.0:
            score += 0.25
            signals.append("HEAVY_STUDY_HOURS")
        elif study_hours > 5.0:
            score += 0.1
            signals.append("ELEVATED_STUDY_HOURS")

        if mood <= 2:
            score += 0.25
            signals.append("LOW_MOOD_REPORTED")

        if energy_level <= 2:
            score += 0.2
            signals.append("LOW_ENERGY_REPORTED")

        score = min(1.0, round(score, 2))
        if score >= 0.65:
            level = "HIGH"
        elif score >= 0.4:
            level = "MEDIUM"
        else:
            level = "LOW"
            if not signals:
                signals.append("NORMAL_HEALTH_METRICS")

        return level, score, signals

    @staticmethod
    def log_wellness(db: Session, user_id: int, data: HealthLogCreate) -> HealthRecord:
        record_date = data.record_date or datetime.date.today()
        stress_lvl, stress_score, _ = HealthService._compute_stress(
            data.mood, data.sleep_hours, data.study_hours, data.energy_level
        )

        existing = db.query(HealthRecord).filter(
            HealthRecord.user_id == user_id,
            HealthRecord.record_date == record_date
        ).first()

        if existing:
            existing.mood = data.mood
            existing.sleep_hours = data.sleep_hours
            existing.study_hours = data.study_hours
            existing.energy_level = data.energy_level
            existing.stress_level = stress_lvl
            existing.stress_score = stress_score
            existing.notes = data.notes or ""
            db.commit()
            db.refresh(existing)
            return existing

        record = HealthRecord(
            user_id=user_id,
            record_date=record_date,
            mood=data.mood,
            sleep_hours=data.sleep_hours,
            study_hours=data.study_hours,
            energy_level=data.energy_level,
            stress_level=stress_lvl,
            stress_score=stress_score,
            notes=data.notes or ""
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def get_logs(db: Session, user_id: int, limit: int = 14) -> list[HealthRecord]:
        return db.query(HealthRecord).filter(
            HealthRecord.user_id == user_id
        ).order_by(HealthRecord.record_date.desc()).limit(limit).all()

    @staticmethod
    def get_wellness_summary(db: Session, user_id: int) -> WellnessSummaryOut:
        recent_logs = db.query(HealthRecord).filter(
            HealthRecord.user_id == user_id
        ).order_by(HealthRecord.record_date.desc()).limit(7).all()

        if not recent_logs:
            return WellnessSummaryOut(
                average_sleep_7d=7.0,
                average_study_7d=3.0,
                average_mood_7d=3.5,
                average_energy_7d=3.5,
                current_stress_level="LOW",
                sleep_baseline=DEFAULT_SLEEP_BASELINE,
                sleep_status="STABLE",
                logs_count=0
            )

        avg_sleep = round(sum(l.sleep_hours for l in recent_logs) / len(recent_logs), 2)
        avg_study = round(sum(l.study_hours for l in recent_logs) / len(recent_logs), 2)
        avg_mood = round(sum(l.mood for l in recent_logs) / len(recent_logs), 2)
        avg_energy = round(sum(l.energy_level for l in recent_logs) / len(recent_logs), 2)
        latest_stress = recent_logs[0].stress_level

        sleep_status = "BELOW_BASELINE" if avg_sleep < (DEFAULT_SLEEP_BASELINE - 1.0) else "HEALTHY"

        return WellnessSummaryOut(
            average_sleep_7d=avg_sleep,
            average_study_7d=avg_study,
            average_mood_7d=avg_mood,
            average_energy_7d=avg_energy,
            current_stress_level=latest_stress,
            sleep_baseline=DEFAULT_SLEEP_BASELINE,
            sleep_status=sleep_status,
            logs_count=len(recent_logs)
        )

    @staticmethod
    def predict_stress(db: Session, user_id: int) -> StressPredictionOut:
        latest = db.query(HealthRecord).filter(
            HealthRecord.user_id == user_id
        ).order_by(HealthRecord.record_date.desc()).first()

        if not latest:
            return StressPredictionOut(
                stress_level="LOW",
                confidence=0.75,
                signals=["NO_RECENT_HEALTH_LOGS"],
                sleep_hours=DEFAULT_SLEEP_BASELINE,
                sleep_baseline_deviation=0.0,
                recommendation="Start logging your daily mood, sleep, and study hours for personalized stress prediction."
            )

        level, score, signals = HealthService._compute_stress(
            latest.mood, latest.sleep_hours, latest.study_hours, latest.energy_level
        )
        deviation = round(latest.sleep_hours - DEFAULT_SLEEP_BASELINE, 2)

        if level == "HIGH":
            rec = "High stress pattern detected. Consider taking a 15-minute break, staying hydrated, and aiming for at least 7 hours of sleep tonight."
        elif level == "MEDIUM":
            rec = "Moderate workload stress noted. Maintain regular study intervals with short breathing exercises."
        else:
            rec = "Your wellness parameters are balanced. Keep up the consistent routine!"

        return StressPredictionOut(
            stress_level=level,
            confidence=0.85,
            signals=signals,
            sleep_hours=latest.sleep_hours,
            sleep_baseline_deviation=deviation,
            recommendation=rec
        )

    @staticmethod
    def generate_recommendation(db: Session, user_id: int, rec_type: str = "GENERAL") -> WellnessRecommendation:
        summary = HealthService.get_wellness_summary(db, user_id)
        rec_type = rec_type.upper()

        if rec_type == "DIET":
            title = "Cognitive Nutrition & Energy Fuel"
            content = "For prolonged focus during study periods, pair complex carbs (oats, whole wheat) with protein and antioxidants (berries, nuts). Avoid high-sugar snacks that trigger energy crashes."
        elif rec_type == "MINDFULNESS":
            title = "4-7-8 Breathing & Decompression"
            content = "Inhale calmly through your nose for 4 seconds, hold your breath gently for 7 seconds, and exhale slowly through your mouth for 8 seconds. Repeat 4 times to reduce study anxiety."
        else:
            if summary.sleep_status == "BELOW_BASELINE":
                title = "Sleep Recovery Advisory"
                content = f"Your 7-day average sleep ({summary.average_sleep_7d}h) is below your {summary.sleep_baseline}h baseline. Dim screens 30 minutes before bed to allow melatonin production."
            else:
                title = "Balanced Daily Study-Rest Routine"
                content = "Great job maintaining adequate rest. Schedule your most demanding academic tasks during your peak energy hours in the morning or early afternoon."

        rec = WellnessRecommendation(
            user_id=user_id,
            rec_type=rec_type,
            title=title,
            content=content
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)
        return rec

    @staticmethod
    def get_dashboard(db: Session, user_id: int) -> dict:
        summary = HealthService.get_wellness_summary(db, user_id)
        stress = HealthService.predict_stress(db, user_id)
        latest = db.query(HealthRecord).filter(
            HealthRecord.user_id == user_id
        ).order_by(HealthRecord.record_date.desc()).first()
        stress_score = latest.stress_score if latest else 0.2

        suggestions = [
            {"category": "Mindfulness", "action": "4-7-8 Breathing & Decompression", "reason": "Reduces exam stress and regulates heart rate"},
            {"category": "Rest", "action": "Dim screens 30 min before bed", "reason": "Aids natural melatonin cycle"},
            {"category": "Hydration", "action": "Drink 500ml water between study blocks", "reason": "Boosts sustained cognitive performance"}
        ]
        return {
            "stress_prediction": {
                "stress_score": stress_score,
                "category": stress.stress_level,
                "recommendation": stress.recommendation,
                "confidence": stress.confidence
            },
            "baseline_7d": {
                "avg_sleep_hours": summary.average_sleep_7d,
                "avg_energy": summary.average_energy_7d,
                "avg_mood": summary.average_mood_7d,
                "avg_study_hours": summary.average_study_7d
            },
            "suggestions": suggestions
        }
