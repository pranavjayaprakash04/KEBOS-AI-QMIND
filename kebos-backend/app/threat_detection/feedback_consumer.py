from aiokafka import AIOKafkaConsumer
import asyncio, json, logging
from uuid import uuid4
from datetime import datetime
from app.config import settings

logger = logging.getLogger(__name__)

# Global references to be set from main.py
_db_pool = None


def set_feedback_dependencies(db_pool):
    """Set global dependencies for feedback consumer."""
    global _db_pool
    _db_pool = db_pool


async def consume_analyst_feedback():
    """
    Consumes analyst.feedback Kafka topic.
    Stores corrections as labelled training data.
    CatBoost retraining is triggered when >= 100 new corrections accumulate.
    """
    consumer = AIOKafkaConsumer(
        "analyst.feedback",
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id="kebos-feedback-consumer",
        value_deserializer=lambda m: json.loads(m.decode()),
        auto_offset_reset="earliest",
    )
    await consumer.start()
    logger.info("analyst.feedback consumer started — retraining loop is active")
    try:
        async for msg in consumer:
            feedback = msg.value
            await _store_correction(feedback)
            correction_count = await _get_pending_correction_count()
            if correction_count >= 100:
                logger.info(
                    f"100 analyst corrections accumulated — "
                    f"triggering CatBoost retraining"
                )
                task = asyncio.create_task(
                    _retrain_catboost(), name="catboost_retrain"
                )
                task.add_done_callback(handle_task_error)
    finally:
        await consumer.stop()


async def _store_correction(feedback: dict):
    """Store analyst correction as labelled training data."""
    if not _db_pool:
        logger.error("DB pool not set for feedback consumer")
        return
    
    async with _db_pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO analyst_feedback
               (id, tenant_id, indicator_value, predicted_category,
                corrected_category, analyst_id, created_at)
               VALUES ($1, $2, $3, $4, $5, $6, NOW())""",
            str(uuid4()), feedback.get("tenant_id"),
            feedback.get("indicator_value"),
            feedback.get("predicted_category"),
            feedback.get("corrected_category"),
            feedback.get("analyst_id")
        )


async def _get_pending_correction_count() -> int:
    if not _db_pool:
        logger.error("DB pool not set for feedback consumer")
        return 0
    
    async with _db_pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT COUNT(*) FROM analyst_feedback WHERE used_for_training=false"
        )
        return row[0] if row else 0


async def _retrain_catboost():
    """
    Stub for CatBoost retraining job.
    Full implementation requires: fetch corrections, prepare feature matrix,
    fine-tune existing model, evaluate on validation set, swap if improved.
    """
    logger.info("CatBoost retraining triggered — loading analyst corrections")
    # TODO: implement full retraining pipeline with Celery task
    # For now: log and mark corrections as used
    if not _db_pool:
        logger.error("DB pool not set for feedback consumer")
        return
    
    async with _db_pool.acquire() as conn:
        await conn.execute(
            "UPDATE analyst_feedback SET used_for_training=true "
            "WHERE used_for_training=false"
        )
    logger.info("CatBoost retraining: corrections marked as used (full pipeline TODO)")


def handle_task_error(task: asyncio.Task):
    """Global error handler for background tasks with auto-restart."""
    if task.cancelled():
        return
    exc = task.exception()
    if exc:
        logger.error(
            f"Background task '{task.get_name()}' crashed: {exc}",
            exc_info=exc
        )
