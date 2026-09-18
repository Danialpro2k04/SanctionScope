from fastapi import FastAPI
from pydantic import BaseModel
import time
import json
import uuid
from datetime import datetime

from app.schemas import ScreeningResult, ScreeningMatch, MatchEvidence
from app.audit import init_db, log_screening
from app.matching.exact import match_exact
from app.matching.fuzzy import match_fuzzy
from app.matching.semantic import match_semantic

app = FastAPI(title="SanctionScope")

# Global in-memory data for exact/fuzzy
DATA_CACHE = []

@app.on_event("startup")
def startup_event():
    init_db()
    with open("data/processed_entities.json", "r", encoding="utf-8") as f:
        global DATA_CACHE
        DATA_CACHE = json.load(f)

class ScreenRequest(BaseModel):
    name: str
    country: str | None = None

def build_entity_lookup():
    return {ent["entity_id"]: ent for ent in DATA_CACHE}

@app.post("/screen", response_model=ScreeningResult)
def screen_entity(req: ScreenRequest):
    start_time = time.time()
    
    # Run all three independently
    exact_res = match_exact(req.name, DATA_CACHE)
    fuzzy_res = match_fuzzy(req.name, DATA_CACHE)
    semantic_res = match_semantic(req.name)
    
    lookup = build_entity_lookup()
    candidates = {}
    
    # Combine EXACT
    for eid, score, m_text, m_on, m_alias in exact_res:
        candidates[eid] = {"exact": True, "jw": 1.0, "lev": 1.0, "sem": 0.0, "on": m_on, "alias": m_alias}
        
    # Combine FUZZY
    for eid, score, m_text, m_on, m_alias in fuzzy_res:
        if eid not in candidates:
            candidates[eid] = {"exact": False, "jw": score, "lev": score, "sem": 0.0, "on": m_on, "alias": m_alias}
        else:
            candidates[eid]["jw"] = score
            candidates[eid]["lev"] = score
            
    # Combine SEMANTIC
    for eid, score, m_text, m_on, m_alias in semantic_res:
        if eid not in candidates:
            candidates[eid] = {"exact": False, "jw": 0.0, "lev": 0.0, "sem": score, "on": m_on, "alias": m_alias}
        else:
            candidates[eid]["sem"] = score
            if candidates[eid]["on"] is None:
                candidates[eid]["on"] = m_on
                candidates[eid]["alias"] = m_alias

    matches = []
    for eid, scores in candidates.items():
        combined_score = 1.0 if scores["exact"] else max(scores["jw"], scores["lev"], scores["sem"])
        
        # Threshold logic
        if not scores["exact"] and combined_score < 0.65:
            continue
            
        ent = lookup[eid]
        matches.append(ScreeningMatch(
            entity_id=eid,
            matched_name=ent["canonical_name"],
            entity_type=ent["entity_type"],
            country=ent["country"],
            sanctions_programs=ent["sanctions_programs"],
            source_dataset=ent["source_dataset"],
            evidence=MatchEvidence(
                exact_match=scores["exact"],
                jaro_winkler_score=scores["jw"],
                levenshtein_score=scores["lev"],
                semantic_score=scores["sem"],
                matched_on=scores["on"],
                matched_alias_text=scores["alias"]
            ),
            combined_score=combined_score
        ))

    matches.sort(key=lambda x: x.combined_score, reverse=True)
    
    # Risk Determination
    top_score = matches[0].combined_score if matches else 0.0
    exact = matches[0].evidence.exact_match if matches else False
    
    if exact or top_score >= 0.90:
        risk = "RED"
    elif 0.65 <= top_score < 0.90:
        risk = "YELLOW"
    else:
        risk = "GREEN"

    result = ScreeningResult(
        audit_id=str(uuid.uuid4()),
        query_name=req.name,
        query_country=req.country,
        risk_level=risk,
        matches=matches,
        screened_at=datetime.utcnow(),
        processing_time_ms=(time.time() - start_time) * 1000
    )
    
    log_screening(result)
    return result

@app.get("/screen/compare")
def compare_strategies(name: str):
    return {
        "exact": match_exact(name, DATA_CACHE),
        "fuzzy": match_fuzzy(name, DATA_CACHE),
        "semantic": match_semantic(name)
    }