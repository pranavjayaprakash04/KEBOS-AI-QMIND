"""
Robustness Logger Utility
Logs adversarial attack results to the DB.
"""
from common.db import SessionLocal
from common.models import AttackResultORM
from datetime import datetime
from typing import Optional

def log_attack_result(user_id: str, model_id: str, attack_type: str, metrics: dict, result_path: Optional[str] = None):
    db = SessionLocal()
    try:
        entry = AttackResultORM(
            user_id=user_id,
            model_id=model_id,
            attack_type=attack_type,
            metrics=metrics,
            result_path=result_path,
            timestamp=datetime.utcnow()
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry.id
    finally:
        db.close()
