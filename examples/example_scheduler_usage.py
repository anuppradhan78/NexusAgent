"""
Example usage of Query Scheduler

This script demonstrates how to use the scheduled query functionality.

Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6
"""
import asyncio
from dotenv import load_dotenv

from mcp_client import MCPClient
from memory_store import MemoryStore
from agent_orchestrator import AgentOrchestrator
from alert_engine import AlertEngine
from report_generator import ReportGenerator
from scheduler import QueryScheduler

# Load environment variables
load_dotenv()


async def main():
    """Demonstrate scheduler functionality"""
    
    print("=" * 60)
    print("Query Scheduler Example")
    print("=" * 60)
    print()
    
    # Initialize components
    print("Initializing components...")
    mcp_client = MCPClient()
    await mcp_client.initialize()
    
    memory_store = MemoryStore(redis_url="redis://localhost:6379")
    alert_engine = AlertEngine(mcp_client=mcp_client)
    report_generator = ReportGenerator(output_dir="./reports")
    
    agent_orchestrator = AgentOrchestrator(
        mcp_client=mcp_client,
        memory_store=memory_store,
        alert_engine=alert_engine,
        report_generator=report_generator
    )
    
    # Initialize scheduler
    print("Initializing scheduler...")
    scheduler = QueryScheduler(
        agent_orchestrator=agent_orchestrator,
        memory_store=memory_store
    )
    await scheduler.start()
    print("✓ Scheduler started")
    print()
    
    # Example 1: Create a scheduled query (hourly)
    print("Example 1: Creating hourly scheduled query")
    print("-" * 60)
    schedule1 = await scheduler.create_schedule(
        query="What are the latest AI developments?",
        cron_expression="0 * * * *",  # Every hour at minute 0
        enabled=True,
        alert_on_change=True,
        max_sources=5
    )
    
    print(f"✓ Schedule created: {schedule1.schedule_id}")
    print(f"  Query: {schedule1.query}")
    print(f"  Cron: {schedule1.cron_expression}")
    print(f"  Enabled: {schedule1.enabled}")
    print(f"  Alert on change: {schedule1.alert_on_change}")
    
    next_run = scheduler.get_next_run_time(schedule1.schedule_id)
    if next_run:
        print(f"  Next run: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Example 2: Create a daily scheduled query
    print("Example 2: Creating daily scheduled query")
    print("-" * 60)
    schedule2 = await scheduler.create_schedule(
        query="What are the trending topics in machine learning?",
        cron_expression="0 9 * * *",  # Every day at 9:00 AM
        enabled=True,
        alert_on_change=True,
        max_sources=3
    )
    
    print(f"✓ Schedule created: {schedule2.schedule_id}")
    print(f"  Query: {schedule2.query}")
    print(f"  Cron: {schedule2.cron_expression}")
    
    next_run = scheduler.get_next_run_time(schedule2.schedule_id)
    if next_run:
        print(f"  Next run: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Example 3: List all schedules
    print("Example 3: Listing all schedules")
    print("-" * 60)
    all_schedules = await scheduler.list_schedules()
    print(f"Total schedules: {len(all_schedules)}")
    for schedule in all_schedules:
        print(f"  - {schedule.schedule_id}: {schedule.query[:50]}...")
        print(f"    Enabled: {schedule.enabled}, Executions: {schedule.execution_count}")
    print()
    
    # Example 4: Update a schedule (disable it)
    print("Example 4: Updating schedule (disabling)")
    print("-" * 60)
    updated = await scheduler.update_schedule(
        schedule_id=schedule1.schedule_id,
        enabled=False
    )
    print(f"✓ Schedule updated: {updated.schedule_id}")
    print(f"  Enabled: {updated.enabled}")
    print()
    
    # Example 5: Get a specific schedule
    print("Example 5: Getting specific schedule")
    print("-" * 60)
    retrieved = await scheduler.get_schedule(schedule2.schedule_id)
    if retrieved:
        print(f"✓ Schedule retrieved: {retrieved.schedule_id}")
        print(f"  Query: {retrieved.query}")
        print(f"  Cron: {retrieved.cron_expression}")
        print(f"  Enabled: {retrieved.enabled}")
        print(f"  Execution count: {retrieved.execution_count}")
    print()
    
    # Example 6: Manually execute a scheduled query
    print("Example 6: Manually executing scheduled query")
    print("-" * 60)
    print(f"Executing query: {schedule2.query[:50]}...")
    print("(This would normally run automatically based on cron schedule)")
    
    # Note: In production, this runs automatically via APScheduler
    # For demo purposes, we can trigger it manually:
    # await scheduler._execute_scheduled_query(schedule2.schedule_id)
    
    print("✓ Query would be executed in background")
    print("  - Results would be synthesized")
    print("  - Report would be generated")
    print("  - Alert would be triggered if results changed significantly")
    print()
    
    # Example 7: Delete a schedule
    print("Example 7: Deleting schedule")
    print("-" * 60)
    success = await scheduler.delete_schedule(schedule1.schedule_id)
    if success:
        print(f"✓ Schedule deleted: {schedule1.schedule_id}")
    print()
    
    # Final schedule count
    print("Final schedule count")
    print("-" * 60)
    remaining_schedules = await scheduler.list_schedules()
    print(f"Remaining schedules: {len(remaining_schedules)}")
    print()
    
    # Cleanup
    print("Cleaning up...")
    await scheduler.stop()
    await mcp_client.close()
    memory_store.close()
    print("✓ Cleanup complete")
    print()
    
    print("=" * 60)
    print("Scheduler Example Complete!")
    print("=" * 60)
    print()
    print("Key Features Demonstrated:")
    print("  ✓ Create scheduled queries with cron expressions")
    print("  ✓ List all scheduled queries")
    print("  ✓ Get specific schedule details")
    print("  ✓ Update schedule settings (enable/disable)")
    print("  ✓ Delete schedules")
    print("  ✓ Automatic background execution")
    print("  ✓ Change detection and alerting")
    print("  ✓ Report generation for scheduled queries")
    print()


if __name__ == "__main__":
    asyncio.run(main())
