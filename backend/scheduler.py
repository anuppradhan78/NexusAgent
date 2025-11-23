"""
Scheduler for Adaptive Research Agent

This module provides scheduled query execution functionality using APScheduler.
Scheduled queries run in the background and can trigger alerts when results change.

Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6
"""
import asyncio
import json
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from datetime import datetime
import structlog

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.job import Job

from agent_orchestrator import AgentOrchestrator, ResearchResult
from memory_store import MemoryStore

logger = structlog.get_logger()


@dataclass
class ScheduledQuery:
    """
    Scheduled query configuration.
    
    Attributes:
        schedule_id: Unique identifier for this schedule
        query: Query text to execute
        cron_expression: Cron expression for scheduling
        enabled: Whether schedule is active
        alert_on_change: Whether to alert on significant changes
        max_sources: Maximum API sources to use
        created_at: When schedule was created
        last_run: Last execution timestamp
        last_result_hash: Hash of last result for change detection
        execution_count: Number of times executed
    """
    schedule_id: str
    query: str
    cron_expression: str
    enabled: bool = True
    alert_on_change: bool = True
    max_sources: int = 5
    created_at: float = 0.0
    last_run: Optional[float] = None
    last_result_hash: Optional[str] = None
    execution_count: int = 0


class SchedulerError(Exception):
    """Raised when scheduler operations fail"""
    pass


class QueryScheduler:
    """
    Manages scheduled recurring queries.
    
    Requirements:
    - 13.1: Accept scheduled queries with cron-like expressions
    - 13.2: Execute scheduled queries in background
    - 13.3: Compare new results with previous executions
    - 13.4: Trigger alerts on significant changes
    - 13.5: Generate reports for scheduled queries
    - 13.6: Allow enable/disable/modify scheduled queries
    """
    
    def __init__(
        self,
        agent_orchestrator: AgentOrchestrator,
        memory_store: MemoryStore
    ):
        """
        Initialize query scheduler.
        
        Args:
            agent_orchestrator: Agent orchestrator for query execution
            memory_store: Memory store for persisting schedules
        """
        self.agent_orchestrator = agent_orchestrator
        self.memory_store = memory_store
        self.scheduler = AsyncIOScheduler()
        self.schedules: Dict[str, ScheduledQuery] = {}
        
        logger.info("query_scheduler_initialized")
    
    async def start(self):
        """
        Start the scheduler and load persisted schedules.
        
        Requirements: 13.2 - Execute scheduled queries in background
        """
        try:
            # Load persisted schedules from Redis
            await self._load_schedules()
            
            # Start APScheduler
            self.scheduler.start()
            
            logger.info(
                "scheduler_started",
                loaded_schedules=len(self.schedules)
            )
            
        except Exception as e:
            logger.error("scheduler_start_failed", error=str(e))
            raise SchedulerError(f"Failed to start scheduler: {e}")
    
    async def stop(self):
        """Stop the scheduler gracefully."""
        try:
            self.scheduler.shutdown(wait=True)
            logger.info("scheduler_stopped")
        except Exception as e:
            logger.error("scheduler_stop_failed", error=str(e))
    
    async def create_schedule(
        self,
        query: str,
        cron_expression: str,
        enabled: bool = True,
        alert_on_change: bool = True,
        max_sources: int = 5
    ) -> ScheduledQuery:
        """
        Create a new scheduled query.
        
        Requirements:
        - 13.1: Accept scheduled queries with cron-like expressions
        - 13.6: Allow users to enable/disable/modify scheduled queries
        
        Args:
            query: Query text to execute
            cron_expression: Cron expression (e.g., "0 * * * *" for hourly)
            enabled: Whether schedule is active
            alert_on_change: Whether to alert on significant changes
            max_sources: Maximum API sources to use
            
        Returns:
            ScheduledQuery: Created schedule configuration
            
        Raises:
            SchedulerError: If schedule creation fails
        """
        try:
            # Generate unique schedule ID
            schedule_id = f"schedule_{int(time.time())}_{hash(query) % 10000}"
            
            # Validate cron expression
            try:
                trigger = CronTrigger.from_crontab(cron_expression)
            except Exception as e:
                raise SchedulerError(f"Invalid cron expression: {e}")
            
            # Create schedule object
            schedule = ScheduledQuery(
                schedule_id=schedule_id,
                query=query,
                cron_expression=cron_expression,
                enabled=enabled,
                alert_on_change=alert_on_change,
                max_sources=max_sources,
                created_at=time.time()
            )
            
            # Store in memory
            self.schedules[schedule_id] = schedule
            
            # Persist to Redis
            await self._persist_schedule(schedule)
            
            # Add job to scheduler if enabled
            if enabled:
                self._add_job(schedule)
            
            logger.info(
                "schedule_created",
                schedule_id=schedule_id,
                query=query[:100],
                cron_expression=cron_expression,
                enabled=enabled
            )
            
            return schedule
            
        except SchedulerError:
            raise
        except Exception as e:
            logger.error("schedule_creation_failed", error=str(e))
            raise SchedulerError(f"Failed to create schedule: {e}")
    
    async def get_schedule(self, schedule_id: str) -> Optional[ScheduledQuery]:
        """
        Get a scheduled query by ID.
        
        Args:
            schedule_id: Schedule identifier
            
        Returns:
            ScheduledQuery if found, None otherwise
        """
        return self.schedules.get(schedule_id)
    
    async def list_schedules(self) -> List[ScheduledQuery]:
        """
        List all scheduled queries.
        
        Returns:
            List of all scheduled queries
        """
        return list(self.schedules.values())
    
    async def update_schedule(
        self,
        schedule_id: str,
        enabled: Optional[bool] = None,
        cron_expression: Optional[str] = None,
        alert_on_change: Optional[bool] = None,
        max_sources: Optional[int] = None
    ) -> ScheduledQuery:
        """
        Update an existing scheduled query.
        
        Requirements: 13.6 - Allow users to enable/disable/modify scheduled queries
        
        Args:
            schedule_id: Schedule identifier
            enabled: New enabled status
            cron_expression: New cron expression
            alert_on_change: New alert setting
            max_sources: New max sources
            
        Returns:
            Updated ScheduledQuery
            
        Raises:
            SchedulerError: If schedule not found or update fails
        """
        try:
            schedule = self.schedules.get(schedule_id)
            if not schedule:
                raise SchedulerError(f"Schedule not found: {schedule_id}")
            
            # Update fields
            if enabled is not None:
                schedule.enabled = enabled
            if cron_expression is not None:
                # Validate new cron expression
                try:
                    CronTrigger.from_crontab(cron_expression)
                    schedule.cron_expression = cron_expression
                except Exception as e:
                    raise SchedulerError(f"Invalid cron expression: {e}")
            if alert_on_change is not None:
                schedule.alert_on_change = alert_on_change
            if max_sources is not None:
                schedule.max_sources = max_sources
            
            # Persist changes
            await self._persist_schedule(schedule)
            
            # Update job in scheduler
            self._remove_job(schedule_id)
            if schedule.enabled:
                self._add_job(schedule)
            
            logger.info(
                "schedule_updated",
                schedule_id=schedule_id,
                enabled=schedule.enabled,
                cron_expression=schedule.cron_expression
            )
            
            return schedule
            
        except SchedulerError:
            raise
        except Exception as e:
            logger.error("schedule_update_failed", error=str(e))
            raise SchedulerError(f"Failed to update schedule: {e}")
    
    async def delete_schedule(self, schedule_id: str) -> bool:
        """
        Delete a scheduled query.
        
        Requirements: 13.6 - Allow users to enable/disable/modify scheduled queries
        
        Args:
            schedule_id: Schedule identifier
            
        Returns:
            True if deleted, False if not found
        """
        try:
            if schedule_id not in self.schedules:
                return False
            
            # Remove from scheduler
            self._remove_job(schedule_id)
            
            # Remove from memory
            del self.schedules[schedule_id]
            
            # Remove from Redis
            await self._delete_persisted_schedule(schedule_id)
            
            logger.info("schedule_deleted", schedule_id=schedule_id)
            
            return True
            
        except Exception as e:
            logger.error("schedule_deletion_failed", error=str(e))
            raise SchedulerError(f"Failed to delete schedule: {e}")
    
    def _add_job(self, schedule: ScheduledQuery):
        """
        Add a job to APScheduler.
        
        Args:
            schedule: Schedule configuration
        """
        try:
            trigger = CronTrigger.from_crontab(schedule.cron_expression)
            
            self.scheduler.add_job(
                func=self._execute_scheduled_query,
                trigger=trigger,
                args=[schedule.schedule_id],
                id=schedule.schedule_id,
                name=f"Scheduled Query: {schedule.query[:50]}",
                replace_existing=True
            )
            
            logger.info(
                "job_added_to_scheduler",
                schedule_id=schedule.schedule_id,
                cron_expression=schedule.cron_expression
            )
            
        except Exception as e:
            logger.error(
                "job_addition_failed",
                schedule_id=schedule.schedule_id,
                error=str(e)
            )
    
    def _remove_job(self, schedule_id: str):
        """
        Remove a job from APScheduler.
        
        Args:
            schedule_id: Schedule identifier
        """
        try:
            self.scheduler.remove_job(schedule_id)
            logger.info("job_removed_from_scheduler", schedule_id=schedule_id)
        except Exception as e:
            # Job might not exist, which is fine
            logger.debug("job_removal_skipped", schedule_id=schedule_id, error=str(e))
    
    async def _execute_scheduled_query(self, schedule_id: str):
        """
        Execute a scheduled query.
        
        Requirements:
        - 13.2: Execute scheduled queries in background
        - 13.3: Compare new results with previous executions
        - 13.4: Trigger alerts on significant changes
        - 13.5: Generate reports for scheduled queries
        
        Args:
            schedule_id: Schedule identifier
        """
        schedule = self.schedules.get(schedule_id)
        if not schedule:
            logger.warning("scheduled_query_not_found", schedule_id=schedule_id)
            return
        
        logger.info(
            "executing_scheduled_query",
            schedule_id=schedule_id,
            query=schedule.query[:100],
            execution_count=schedule.execution_count
        )
        
        try:
            # Execute query through agent orchestrator
            # Requirements: 13.5 - Generate reports for scheduled queries
            result = await self.agent_orchestrator.process_query(
                query=schedule.query,
                session_id=f"scheduled_{schedule_id}",
                max_sources=schedule.max_sources,
                timeout=60,  # Longer timeout for scheduled queries
                include_report=True,  # Always generate reports
                alert_enabled=schedule.alert_on_change
            )
            
            # Calculate result hash for change detection
            # Requirements: 13.3 - Compare new results with previous executions
            result_hash = self._calculate_result_hash(result)
            
            # Check for significant changes
            # Requirements: 13.4 - Trigger alerts on significant changes
            if schedule.last_result_hash and schedule.alert_on_change:
                if result_hash != schedule.last_result_hash:
                    logger.info(
                        "scheduled_query_results_changed",
                        schedule_id=schedule_id,
                        old_hash=schedule.last_result_hash[:16],
                        new_hash=result_hash[:16]
                    )
                    
                    # Alert is already triggered by agent orchestrator if enabled
                    # We just log the change detection here
                else:
                    logger.info(
                        "scheduled_query_results_unchanged",
                        schedule_id=schedule_id,
                        result_hash=result_hash[:16]
                    )
            
            # Update schedule metadata
            schedule.last_run = time.time()
            schedule.last_result_hash = result_hash
            schedule.execution_count += 1
            
            # Persist updated schedule
            await self._persist_schedule(schedule)
            
            logger.info(
                "scheduled_query_executed_successfully",
                schedule_id=schedule_id,
                query_id=result.query_id,
                processing_time_ms=result.processing_time_ms,
                confidence_score=result.synthesis.confidence_score,
                execution_count=schedule.execution_count,
                report_generated=result.report_path is not None,
                alert_triggered=result.alert is not None
            )
            
        except Exception as e:
            logger.error(
                "scheduled_query_execution_failed",
                schedule_id=schedule_id,
                query=schedule.query[:100],
                error=str(e),
                error_type=type(e).__name__
            )
    
    def _calculate_result_hash(self, result: ResearchResult) -> str:
        """
        Calculate hash of result for change detection.
        
        Uses key findings and confidence score to detect significant changes.
        
        Args:
            result: Research result
            
        Returns:
            Hash string for comparison
        """
        import hashlib
        
        # Create a string representation of key result components
        result_str = json.dumps({
            "summary": result.synthesis.summary,
            "findings": sorted(result.synthesis.findings),
            "confidence": round(result.synthesis.confidence_score, 2),
            "sources": sorted(result.synthesis.sources)
        }, sort_keys=True)
        
        # Calculate SHA256 hash
        return hashlib.sha256(result_str.encode()).hexdigest()
    
    async def _persist_schedule(self, schedule: ScheduledQuery):
        """
        Persist schedule to Redis.
        
        Args:
            schedule: Schedule to persist
        """
        try:
            key = f"schedule:{schedule.schedule_id}"
            value = json.dumps(asdict(schedule))
            
            # Store in Redis with no expiration (schedules persist until deleted)
            self.memory_store.client.set(key, value)
            
            logger.debug("schedule_persisted", schedule_id=schedule.schedule_id)
            
        except Exception as e:
            logger.error(
                "schedule_persistence_failed",
                schedule_id=schedule.schedule_id,
                error=str(e)
            )
    
    async def _load_schedules(self):
        """
        Load persisted schedules from Redis.
        """
        try:
            # Scan for all schedule keys
            for key in self.memory_store.client.scan_iter("schedule:*"):
                try:
                    value = self.memory_store.client.get(key)
                    if value:
                        schedule_data = json.loads(value)
                        schedule = ScheduledQuery(**schedule_data)
                        
                        self.schedules[schedule.schedule_id] = schedule
                        
                        # Add job to scheduler if enabled
                        if schedule.enabled:
                            self._add_job(schedule)
                        
                        logger.debug(
                            "schedule_loaded",
                            schedule_id=schedule.schedule_id,
                            enabled=schedule.enabled
                        )
                        
                except Exception as e:
                    logger.warning(
                        "schedule_load_failed",
                        key=key,
                        error=str(e)
                    )
                    continue
            
            logger.info(
                "schedules_loaded",
                count=len(self.schedules)
            )
            
        except Exception as e:
            logger.error("schedules_load_failed", error=str(e))
    
    async def _delete_persisted_schedule(self, schedule_id: str):
        """
        Delete persisted schedule from Redis.
        
        Args:
            schedule_id: Schedule identifier
        """
        try:
            key = f"schedule:{schedule_id}"
            self.memory_store.client.delete(key)
            
            logger.debug("persisted_schedule_deleted", schedule_id=schedule_id)
            
        except Exception as e:
            logger.error(
                "persisted_schedule_deletion_failed",
                schedule_id=schedule_id,
                error=str(e)
            )
    
    def get_next_run_time(self, schedule_id: str) -> Optional[datetime]:
        """
        Get next scheduled run time for a schedule.
        
        Args:
            schedule_id: Schedule identifier
            
        Returns:
            Next run datetime if schedule exists and is enabled, None otherwise
        """
        try:
            job = self.scheduler.get_job(schedule_id)
            if job:
                return job.next_run_time
            return None
        except Exception:
            return None
