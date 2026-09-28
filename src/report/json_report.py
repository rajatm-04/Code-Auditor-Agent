"""
JSON report generator.
Leverages Pydantic's native model_dump_json for reliable serialization.
"""

import os
from src.models import AuditReport


class JsonReportGenerator:
    """Saves AuditReport models to structured JSON files."""

    @classmethod
    def save(cls, report: AuditReport, output_path: str) -> str:
        """Serializes and saves report as pretty-printed JSON."""
        target_file = output_path if output_path.endswith(".json") else f"{output_path}.json"
        os.makedirs(os.path.dirname(os.path.abspath(target_file)), exist_ok=True)
        
        json_data = report.model_dump_json(indent=2)
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(json_data)
        return target_file