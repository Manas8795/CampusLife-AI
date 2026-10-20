from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel

class BaselineMetric(BaseModel):
    metric: str
    personal_baseline: float
    current_value: float
    deviation: float
    status: str # NORMAL, ELEVATED, DECREASED, AT_RISK

class CrossDomainRiskOut(BaseModel):
    id: Optional[int] = None
    risk_type: str
    severity: str # LOW, MEDIUM, HIGH, CRITICAL
    score: float
    confidence: float
    supporting_signals: List[str]
    created_at: Optional[datetime] = None

class IntelligenceInsightOut(BaseModel):
    id: Optional[int] = None
    insight_type: str
    severity: str
    title: str
    evidence_signals: List[str]
    recommendation: str
    created_at: Optional[datetime] = None

class UnifiedStudentStateOut(BaseModel):
    user_id: int
    updated_at: datetime
    compound_risk_level: str
    compound_risk_score: float
    academic_state: Dict
    wellness_state: Dict
    financial_state: Dict
    travel_state: Dict
    baselines: List[BaselineMetric]
    detected_risks: List[CrossDomainRiskOut]
    priority_insights: List[IntelligenceInsightOut]
    proactive_intervention_recommended: bool
    proactive_intervention_reason: Optional[str] = None
