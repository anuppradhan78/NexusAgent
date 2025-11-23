"""
Example usage of AlertEngine

This demonstrates how to integrate the AlertEngine into the agent orchestrator.
"""
import asyncio
import os
from alert_engine import AlertEngine
from models import ResearchSynthesis, APISource
from mcp_client import MCPClient


async def example_usage():
    """Example of using the AlertEngine"""
    
    # Set up environment
    os.environ["ALERT_CHANNELS"] = "console,file:./alerts.log"
    
    # Initialize MCP client and alert engine
    mcp_client = MCPClient()
    await mcp_client.initialize()
    
    alert_engine = AlertEngine(mcp_client)
    
    # Example research synthesis
    synthesis = ResearchSynthesis(
        summary="Breaking: Major security vulnerability discovered in popular framework",
        detailed_analysis="A critical security flaw has been identified that affects millions of users...",
        findings=[
            "CVE-2024-XXXXX assigned with CVSS score 9.8",
            "Affects versions 1.0 through 3.5",
            "Patch available in version 3.6",
            "Active exploitation detected in the wild"
        ],
        sources=["security_api", "cve_database", "vendor_advisory"],
        source_details=[
            APISource(
                api_id="security_api",
                api_name="Security API",
                endpoint="/api/vulnerabilities",
                verified=True,
                priority_score=0.95
            )
        ],
        confidence_score=0.95,
        confidence_breakdown={"security_api": 0.95}
    )
    
    # Evaluate for alert
    query = "Latest security vulnerabilities in web frameworks"
    alert = await alert_engine.evaluate(query, synthesis)
    
    if alert:
        print(f"\n✅ Alert triggered with severity: {alert.severity}")
        print(f"   Title: {alert.title}")
        print(f"   Key points: {len(alert.key_points)}")
    else:
        print("\n❌ No alert triggered")
    
    # Get alert statistics
    stats = alert_engine.get_alert_stats()
    print(f"\n📊 Alert Statistics:")
    print(f"   Total alerts (24h): {stats['total_alerts_24h']}")
    print(f"   Channels configured: {stats['channels_configured']}")
    print(f"   Severity breakdown: {stats['severity_breakdown']}")
    
    # Clean up
    await mcp_client.close()


if __name__ == "__main__":
    asyncio.run(example_usage())
