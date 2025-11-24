"""
Report Generator - Generate markdown reports
Note: This is a simple wrapper since the actual report generation
is handled by the Research Tools MCP Server
"""
from pathlib import Path
from typing import List, Dict, Any
import structlog

logger = structlog.get_logger()


class ReportGenerator:
    """Simple report generator wrapper"""
    
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Report generator initialized", output_dir=str(self.output_dir))
    
    def list_reports(self, limit: int = 20) -> List[Dict[str, Any]]:
        """List generated reports"""
        try:
            reports = []
            for report_file in sorted(self.output_dir.glob("*.md"), reverse=True)[:limit]:
                reports.append({
                    "report_id": report_file.stem,
                    "filename": report_file.name,
                    "path": str(report_file),
                    "size": report_file.stat().st_size,
                    "created": report_file.stat().st_mtime
                })
            
            logger.info(f"Listed {len(reports)} reports")
            return reports
            
        except Exception as e:
            logger.error("Failed to list reports", error=str(e))
            return []
    
    def get_report(self, report_id: str) -> str:
        """Get report content by ID"""
        try:
            # Try with .md extension
            report_file = self.output_dir / f"{report_id}.md"
            if not report_file.exists():
                # Try exact filename
                report_file = self.output_dir / report_id
            
            if not report_file.exists():
                raise FileNotFoundError(f"Report not found: {report_id}")
            
            content = report_file.read_text(encoding="utf-8")
            logger.info(f"Retrieved report", report_id=report_id)
            return content
            
        except Exception as e:
            logger.error("Failed to get report", report_id=report_id, error=str(e))
            raise
