from pydantic import BaseModel
from typing import Literal
from datetime import datetime

class MatchEvidence(BaseModel):
    exact_match: bool
    jaro_winkler_score: float
    levenshtein_score: float
    semantic_score: float
    matched_on: str
    matched_alias_text: str | None = None

class ScreeningMatch(BaseModel):
    entity_id: str
    matched_name: str
    entity_type: str
    country: str | None = None
    sanctions_programs: list[str] = []
    source_dataset: str
    evidence: MatchEvidence
    combined_score: float

class ScreeningResult(BaseModel):
    audit_id: str
    query_name: str
    query_country: str | None = None
    risk_level: Literal["RED", "YELLOW", "GREEN"]
    matches: list[ScreeningMatch]
    screened_at: datetime
    processing_time_ms: float