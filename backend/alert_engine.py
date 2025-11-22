"""
Alert Engine for Adaptive Research Agent

This module provides the AlertEngine class that evaluates research results
for urgency and importance, sends notifications via configured channels,
and prevents alert fatigue through deduplication.

Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
"""
import os
import json
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import structlog
import httpx

from models import ResearchSynthesis

logger = structlog.get_logger()


@dataclass
class Alert:
    """
    Alert notification data structure.
    
    Requirements: 5.2, 5.3 - Alert with severity and content
    """
    severity: str  # low, medium, high, critical
    title: str
    message: str
    key_points: List[str]
    sources: List[str]
    timestamp: datetime
    query: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary for serialization"""
        return {
            "severity": self.severity,
            "title": self.title,
            "message": self.message,
            "key_points": self.key_points,
            "sources": self.sources,
            "timestamp": self.timestamp.isoformat(),
            "query": self.query
        }


class AlertEngine:
    """
    Engine for detecting critical information and sending notifications.
    
    Evaluates research results for urgency, manages alert channels,
    and prevents duplicate alerts to avoid notification fatigue.
    
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
    """
    
    def __init__(self, mcp_client):
        """
        Initialize alert engine with MCP client and configuration.
        
        Args:
            mcp_client: MCPClient instance for Claude interactions
        """
        self.mcp_client = mcp_client
        self.alert_channels = self._parse_channels(os.getenv("ALERT_CHANNELS", "console"))
        self.alert_history: List[Alert] = []
        self.deduplication_window = timedelta(hours=1)  # 1 hour window for deduplication
        
        logger.info(
            "alert_engine_initialized",
            channels=self.alert_channels,
            deduplication_window_hours=1
        )
    
    def _parse_channels(self, channels_config: str) -> List[str]:
        """
        Parse ALERT_CHANNELS environment variable.
        
        Requirements: 5.2 - Parse ALERT_CHANNELS from environment
        
        Supported formats:
        - "console" - Print to console
        - "file:/path/to/alerts.log" - Write to file
        - "webhook:https://example.com/webhook" - POST to webhook
        - Multiple channels: "console,file:/tmp/alerts.log,webhook:https://..."
        
        Args:
            channels_config: Comma-separated channel configuration
            
        Returns:
            List[str]: Parsed channel configurations
        """
        if not channels_config:
            return ["console"]
        
        channels = [ch.strip() for ch in channels_config.split(",") if ch.strip()]
        
        if not channels:
            channels = ["console"]
        
        logger.info("alert_channels_parsed", channels=channels)
        return channels

    async def evaluate(
        self,
        query: str,
        synthesis: ResearchSynthesis
    ) -> Optional[Alert]:
        """
        Evaluate if research results warrant an alert.
        
        Uses Claude to assess urgency and importance of findings.
        Implements deduplication to prevent alert fatigue.
        
        Requirements: 5.1 - Analyze gathered information for urgency indicators
                      5.2 - Send notifications via configured channels
                      5.3 - Include alert severity based on content analysis
                      5.4 - Deduplicate alerts to prevent notification fatigue
        
        Args:
            query: Original research query
            synthesis: Synthesized research results
            
        Returns:
            Optional[Alert]: Alert object if alert should be triggered, None otherwise
        """
        try:
            logger.info(
                "evaluating_alert",
                query=query,
                confidence_score=synthesis.confidence_score
            )
            
            # Use Claude to assess urgency
            assessment = await self._assess_urgency(query, synthesis)
            
            if not assessment.get("should_alert", False):
                logger.info("alert_not_triggered", query=query, reasoning=assessment.get("reasoning", ""))
                return None
            
            # Check for duplicates
            if self._is_duplicate(query, synthesis):
                logger.info("alert_suppressed_duplicate", query=query)
                return None
            
            # Create alert
            alert = Alert(
                severity=assessment.get("severity", "medium"),
                title=f"Research Alert: {query[:50]}{'...' if len(query) > 50 else ''}",
                message=assessment.get("reasoning", "Critical information detected"),
                key_points=assessment.get("key_points", []),
                sources=synthesis.sources,
                timestamp=datetime.now(),
                query=query
            )
            
            # Send alert via configured channels
            await self._send_alert(alert)
            
            # Store in history for deduplication
            self.alert_history.append(alert)
            
            # Clean up old alerts from history
            self._cleanup_history()
            
            logger.info(
                "alert_triggered",
                query=query,
                severity=alert.severity,
                channels=len(self.alert_channels)
            )
            
            return alert
            
        except Exception as e:
            logger.error("alert_evaluation_failed", query=query, error=str(e))
            # Don't raise - alerting is not critical to core functionality
            return None
    
    async def _assess_urgency(
        self,
        query: str,
        synthesis: ResearchSynthesis
    ) -> Dict[str, Any]:
        """
        Use Claude to assess urgency and importance of research results.
        
        Requirements: 5.1 - Analyze gathered information for urgency indicators
                      5.3 - Include alert severity based on content analysis
        
        Args:
            query: Original research query
            synthesis: Synthesized research results
            
        Returns:
            Dict containing should_alert, severity, reasoning, and key_points
        """
        try:
            # Build sources summary
            sources_summary = ', '.join(synthesis.sources[:5])  # Limit to first 5
            if len(synthesis.sources) > 5:
                sources_summary += f" (and {len(synthesis.sources) - 5} more)"
            
            # Build findings summary
            findings_summary = '\n'.join([f"- {finding}" for finding in synthesis.findings[:10]])
            
            prompt = f"""Analyze this research result for urgency and importance.

Query: {query}

Summary:
{synthesis.summary}

Key Findings:
{findings_summary}

Sources: {sources_summary}

Confidence Score: {synthesis.confidence_score:.2f}

Assess:
1. Is this time-sensitive or breaking information?
2. Does this contain critical updates, anomalies, or urgent matters?
3. What is the severity level (low/medium/high/critical)?
4. Should an alert be triggered?

Consider:
- Breaking news or time-sensitive information = high/critical
- Significant changes or important updates = medium/high
- Routine information or expected results = low or no alert
- Be conservative with alerts to avoid fatigue

Respond in JSON format:
{{
    "should_alert": true/false,
    "severity": "low|medium|high|critical",
    "reasoning": "brief explanation of why alert is/isn't needed",
    "key_points": ["point1", "point2", "point3"]
}}"""
            
            system_prompt = "You are an information triage specialist. Be conservative with alerts to avoid notification fatigue. Only trigger alerts for truly urgent, time-sensitive, or critical information."
            
            response = await self.mcp_client.call_claude(
                prompt=prompt,
                system=system_prompt,
                temperature=0.3  # Lower temperature for more consistent decisions
            )
            
            # Parse JSON response
            assessment = self._parse_json_response(response)
            
            logger.info(
                "urgency_assessed",
                query=query,
                should_alert=assessment.get("should_alert", False),
                severity=assessment.get("severity", "unknown")
            )
            
            return assessment
            
        except Exception as e:
            logger.error("urgency_assessment_failed", query=query, error=str(e))
            # Default to no alert on error
            return {
                "should_alert": False,
                "severity": "low",
                "reasoning": f"Assessment failed: {str(e)}",
                "key_points": []
            }
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        Parse JSON from Claude's response, handling markdown code blocks.
        
        Args:
            response: Claude's response text
            
        Returns:
            Dict containing parsed JSON
        """
        try:
            # Try direct JSON parse first
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code block
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                json_str = response[start:end].strip()
                return json.loads(json_str)
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                json_str = response[start:end].strip()
                return json.loads(json_str)
            else:
                # Fallback: return default
                logger.warning("failed_to_parse_json_response", response=response[:200])
                return {
                    "should_alert": False,
                    "severity": "low",
                    "reasoning": "Failed to parse assessment",
                    "key_points": []
                }
    
    def _is_duplicate(self, query: str, synthesis: ResearchSynthesis) -> bool:
        """
        Check if similar alert was recently sent to prevent alert fatigue.
        
        Requirements: 5.4 - Deduplicate alerts to prevent notification fatigue
        
        Args:
            query: Current query
            synthesis: Current synthesis results
            
        Returns:
            bool: True if this is a duplicate alert, False otherwise
        """
        # Get recent alerts within deduplication window
        cutoff_time = datetime.now() - self.deduplication_window
        recent_alerts = [
            alert for alert in self.alert_history
            if alert.timestamp >= cutoff_time
        ]
        
        if not recent_alerts:
            return False
        
        # Check for similar queries or content
        query_lower = query.lower()
        summary_lower = synthesis.summary.lower()
        
        for past_alert in recent_alerts:
            # Check query similarity (simple word overlap)
            if self._text_similarity(past_alert.query.lower(), query_lower) > 0.8:
                logger.info(
                    "duplicate_alert_detected",
                    current_query=query,
                    past_query=past_alert.query,
                    time_diff_minutes=(datetime.now() - past_alert.timestamp).seconds / 60
                )
                return True
            
            # Check if key points overlap significantly
            if self._key_points_overlap(past_alert.key_points, synthesis.findings) > 0.7:
                logger.info(
                    "duplicate_alert_detected_by_content",
                    current_query=query,
                    past_query=past_alert.query
                )
                return True
        
        return False
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate simple text similarity based on word overlap.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            float: Similarity score between 0.0 and 1.0
        """
        # Simple word-based similarity (Jaccard similarity)
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _key_points_overlap(self, points1: List[str], points2: List[str]) -> float:
        """
        Calculate overlap between two lists of key points.
        
        Args:
            points1: First list of key points
            points2: Second list of key points
            
        Returns:
            float: Overlap score between 0.0 and 1.0
        """
        if not points1 or not points2:
            return 0.0
        
        # Calculate average similarity between all pairs
        similarities = []
        for p1 in points1:
            for p2 in points2:
                sim = self._text_similarity(p1.lower(), p2.lower())
                similarities.append(sim)
        
        return max(similarities) if similarities else 0.0

    async def _send_alert(self, alert: Alert) -> None:
        """
        Send alert via all configured channels.
        
        Requirements: 5.2 - Send notifications via configured Alert_Channel
        
        Args:
            alert: Alert to send
        """
        logger.info(
            "sending_alert",
            severity=alert.severity,
            channels=len(self.alert_channels)
        )
        
        # Send to all channels concurrently
        tasks = []
        for channel in self.alert_channels:
            if channel == "console":
                tasks.append(self._send_console(alert))
            elif channel.startswith("file:"):
                file_path = channel[5:]  # Remove "file:" prefix
                tasks.append(self._send_file(alert, file_path))
            elif channel.startswith("webhook:"):
                webhook_url = channel[8:]  # Remove "webhook:" prefix
                tasks.append(self._send_webhook(alert, webhook_url))
            else:
                logger.warning("unknown_alert_channel", channel=channel)
        
        # Execute all sends concurrently
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Log any errors
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(
                        "alert_send_failed",
                        channel=self.alert_channels[i],
                        error=str(result)
                    )
    
    async def _send_console(self, alert: Alert) -> None:
        """
        Print alert to console.
        
        Requirements: 5.2 - Console alert channel
        
        Args:
            alert: Alert to print
        """
        try:
            # Format alert for console display
            separator = "=" * 70
            
            # Color codes for severity (ANSI escape codes)
            severity_colors = {
                "low": "\033[94m",      # Blue
                "medium": "\033[93m",   # Yellow
                "high": "\033[91m",     # Red
                "critical": "\033[95m"  # Magenta
            }
            reset_color = "\033[0m"
            
            color = severity_colors.get(alert.severity, "")
            
            output = f"""
{separator}
{color}🚨 ALERT [{alert.severity.upper()}] 🚨{reset_color}
{separator}
Title: {alert.title}
Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

Message: {alert.message}

Key Points:
"""
            for i, point in enumerate(alert.key_points, 1):
                output += f"  {i}. {point}\n"
            
            output += f"\nSources: {', '.join(alert.sources[:5])}"
            if len(alert.sources) > 5:
                output += f" (and {len(alert.sources) - 5} more)"
            
            output += f"\n{separator}\n"
            
            print(output)
            
            logger.info("alert_sent_to_console", severity=alert.severity)
            
        except Exception as e:
            logger.error("console_alert_failed", error=str(e))
            raise
    
    async def _send_file(self, alert: Alert, file_path: str) -> None:
        """
        Write alert to file.
        
        Requirements: 5.2 - File alert channel
        
        Args:
            alert: Alert to write
            file_path: Path to alert log file
        """
        try:
            # Format alert as JSON for file storage
            alert_json = json.dumps(alert.to_dict(), indent=2)
            
            # Append to file (create if doesn't exist)
            with open(file_path, 'a') as f:
                f.write(alert_json + "\n")
                f.write("-" * 70 + "\n")
            
            logger.info("alert_sent_to_file", file_path=file_path, severity=alert.severity)
            
        except Exception as e:
            logger.error("file_alert_failed", file_path=file_path, error=str(e))
            raise
    
    async def _send_webhook(self, alert: Alert, webhook_url: str) -> None:
        """
        Send alert to webhook endpoint via HTTP POST.
        
        Requirements: 5.2 - Webhook alert channel
        
        Args:
            alert: Alert to send
            webhook_url: Webhook URL to POST to
        """
        try:
            # Prepare webhook payload
            payload = alert.to_dict()
            
            # Send POST request
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                response.raise_for_status()
            
            logger.info(
                "alert_sent_to_webhook",
                webhook_url=webhook_url,
                severity=alert.severity,
                status_code=response.status_code
            )
            
        except httpx.HTTPError as e:
            logger.error(
                "webhook_alert_failed",
                webhook_url=webhook_url,
                error=str(e)
            )
            raise
        except Exception as e:
            logger.error(
                "webhook_alert_unexpected_error",
                webhook_url=webhook_url,
                error=str(e)
            )
            raise
    
    def _cleanup_history(self) -> None:
        """
        Remove old alerts from history to prevent unbounded growth.
        
        Keeps only alerts within the deduplication window.
        """
        cutoff_time = datetime.now() - self.deduplication_window
        
        original_count = len(self.alert_history)
        self.alert_history = [
            alert for alert in self.alert_history
            if alert.timestamp >= cutoff_time
        ]
        
        removed_count = original_count - len(self.alert_history)
        if removed_count > 0:
            logger.info(
                "alert_history_cleaned",
                removed=removed_count,
                remaining=len(self.alert_history)
            )
    
    def get_recent_alerts(self, hours: int = 24) -> List[Alert]:
        """
        Get recent alerts within specified time window.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List[Alert]: Recent alerts
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [
            alert for alert in self.alert_history
            if alert.timestamp >= cutoff_time
        ]
    
    def get_alert_stats(self) -> Dict[str, Any]:
        """
        Get statistics about alerts.
        
        Returns:
            Dict containing alert statistics
        """
        recent_24h = self.get_recent_alerts(hours=24)
        
        severity_counts = {
            "low": 0,
            "medium": 0,
            "high": 0,
            "critical": 0
        }
        
        for alert in recent_24h:
            severity_counts[alert.severity] = severity_counts.get(alert.severity, 0) + 1
        
        return {
            "total_alerts_24h": len(recent_24h),
            "severity_breakdown": severity_counts,
            "channels_configured": len(self.alert_channels),
            "deduplication_window_hours": self.deduplication_window.total_seconds() / 3600
        }
