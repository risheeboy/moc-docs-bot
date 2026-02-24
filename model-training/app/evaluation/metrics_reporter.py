"""Generate evaluation reports and metrics."""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.utils.logging_config import setup_json_logging


logger = setup_json_logging("metrics_reporter")


class MetricsReporter:
    """Generate and report evaluation metrics."""

    def __init__(self):
        """Initialize metrics reporter."""
        pass

    def generate_json_report(
        self,
        metrics: Dict[str, Any],
        model_version: str,
        output_file: Optional[str] = None,
    ) -> str:
        """Generate JSON report of metrics.

        Args:
            metrics: Dictionary of metrics
            model_version: Model version identifier
            output_file: Optional file to save report

        Returns:
            JSON string of report
        """
        report = {
            "model_version": model_version,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "metrics": metrics,
        }

        json_report = json.dumps(report, indent=2, ensure_ascii=False)

        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(json_report)

            logger.info(
                "JSON report saved",
                extra={"file": output_file, "model_version": model_version},
            )

        return json_report

    def generate_html_report(
        self,
        metrics: Dict[str, Any],
        model_version: str,
        output_file: Optional[str] = None,
    ) -> str:
        """Generate HTML report with visualizations.

        Args:
            metrics: Dictionary of metrics
            model_version: Model version
            output_file: Optional file to save report

        Returns:
            HTML string
        """
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Model Evaluation Report - {model_version}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background-color: #2c3e50;
            color: white;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .metrics-section {{
            background-color: white;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .metric-item {{
            display: flex;
            justify-content: space-between;
            padding: 10px;
            border-bottom: 1px solid #eee;
        }}
        .metric-name {{
            font-weight: bold;
            color: #2c3e50;
        }}
        .metric-value {{
            color: #27ae60;
            font-weight: bold;
        }}
        .progress-bar {{
            background-color: #ecf0f1;
            border-radius: 10px;
            overflow: hidden;
            height: 25px;
            margin-top: 5px;
        }}
        .progress-fill {{
            height: 100%;
            background-color: #27ae60;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
        }}
        .timestamp {{
            color: #7f8c8d;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Model Evaluation Report</h1>
        <p>Model Version: {model_version}</p>
        <p class="timestamp">Generated: {datetime.utcnow().isoformat()}Z</p>
    </div>

    <div class="metrics-section">
        <h2>QA Metrics</h2>
"""

        if "qa_metrics" in metrics:
            qa_m = metrics["qa_metrics"]
            html += f"""        <div class="metric-item">
            <span class="metric-name">Exact Match</span>
            <span class="metric-value">{qa_m.get('exact_match', 0):.2%}</span>
        </div>
        <div class="metric-item">
            <span class="metric-name">F1 Score</span>
            <span class="metric-value">{qa_m.get('f1', 0):.4f}</span>
        </div>
        <div class="metric-item">
            <span class="metric-name">BLEU Score</span>
            <span class="metric-value">{qa_m.get('bleu', 0):.4f}</span>
        </div>
"""

        html += """    </div>

    <div class="metrics-section">
        <h2>Quality Metrics</h2>
"""

        if "quality_metrics" in metrics:
            qual_m = metrics["quality_metrics"]
            for metric_name in ["relevance", "correctness", "completeness", "clarity", "overall"]:
                value = qual_m.get(metric_name, 0)
                percentage = (value / 5.0) * 100
                html += f"""        <div class="metric-item">
            <span class="metric-name">{metric_name.title()}</span>
            <span class="metric-value">{value:.2f} / 5.0</span>
        </div>
        <div class="progress-bar">
            <div class="progress-fill" style="width: {percentage}%;">{percentage:.1f}%</div>
        </div>
"""

        html += """    </div>

    <div class="metrics-section">
        <h2>Hallucination Metrics</h2>
"""

        if "hallucination_metrics" in metrics:
            hal_m = metrics["hallucination_metrics"]
            html += f"""        <div class="metric-item">
            <span class="metric-name">Average Hallucination Rate</span>
            <span class="metric-value">{hal_m.get('average_hallucination_rate', 0):.2%}</span>
        </div>
        <div class="metric-item">
            <span class="metric-name">Max Hallucination Rate</span>
            <span class="metric-value">{hal_m.get('max_hallucination_rate', 0):.2%}</span>
        </div>
"""

        html += """    </div>
</body>
</html>"""

        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(html)

            logger.info(
                "HTML report saved",
                extra={"file": output_file, "model_version": model_version},
            )

        return html

    def generate_markdown_report(
        self,
        metrics: Dict[str, Any],
        model_version: str,
        output_file: Optional[str] = None,
    ) -> str:
        """Generate Markdown report.

        Args:
            metrics: Dictionary of metrics
            model_version: Model version
            output_file: Optional file to save report

        Returns:
            Markdown string
        """
        lines = []

        lines.append(f"# Model Evaluation Report: {model_version}")
        lines.append("")
        lines.append(f"**Generated:** {datetime.utcnow().isoformat()}Z")
        lines.append("")

        # QA Metrics
        if "qa_metrics" in metrics:
            lines.append("## QA Evaluation Metrics")
            lines.append("")
            qa_m = metrics["qa_metrics"]
            lines.append(f"- **Exact Match:** {qa_m.get('exact_match', 0):.2%}")
            lines.append(f"- **F1 Score:** {qa_m.get('f1', 0):.4f}")
            lines.append(f"- **BLEU Score:** {qa_m.get('bleu', 0):.4f}")
            lines.append(f"- **Sample Count:** {qa_m.get('sample_count', 0)}")
            lines.append("")

        # Hindi Metrics
        if "hindi_metrics" in metrics:
            lines.append("## Hindi-Specific Metrics")
            lines.append("")
            hindi_m = metrics["hindi_metrics"]
            lines.append(f"- **Hindi Exact Match:** {hindi_m.get('exact_match_hindi', 0):.2%}")
            lines.append(f"- **Hindi F1:** {hindi_m.get('f1_hindi', 0):.4f}")
            lines.append(f"- **Hindi BLEU:** {hindi_m.get('bleu_hindi', 0):.4f}")
            lines.append(f"- **Devanagari Consistency:** {hindi_m.get('devanagari_consistency', 0):.2%}")
            lines.append("")

        # Quality Metrics
        if "quality_metrics" in metrics:
            lines.append("## Response Quality Metrics (1-5 scale)")
            lines.append("")
            qual_m = metrics["quality_metrics"]
            lines.append(f"- **Relevance:** {qual_m.get('relevance', 0):.2f} / 5.0")
            lines.append(f"- **Correctness:** {qual_m.get('correctness', 0):.2f} / 5.0")
            lines.append(f"- **Completeness:** {qual_m.get('completeness', 0):.2f} / 5.0")
            lines.append(f"- **Clarity:** {qual_m.get('clarity', 0):.2f} / 5.0")
            lines.append(f"- **Overall:** {qual_m.get('overall', 0):.2f} / 5.0")
            lines.append("")

        # Hallucination Metrics
        if "hallucination_metrics" in metrics:
            lines.append("## Hallucination Detection")
            lines.append("")
            hal_m = metrics["hallucination_metrics"]
            lines.append(f"- **Average Hallucination Rate:** {hal_m.get('average_hallucination_rate', 0):.2%}")
            lines.append(f"- **Max Hallucination Rate:** {hal_m.get('max_hallucination_rate', 0):.2%}")
            lines.append(f"- **Min Hallucination Rate:** {hal_m.get('min_hallucination_rate', 0):.2%}")
            lines.append(f"- **Sample Count:** {hal_m.get('sample_count', 0)}")
            lines.append("")

        markdown = "\n".join(lines)

        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(markdown)

            logger.info(
                "Markdown report saved",
                extra={"file": output_file, "model_version": model_version},
            )

        return markdown

    def compare_models(
        self,
        model_metrics: List[Dict[str, Any]],
        model_names: List[str],
        output_file: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Compare metrics across multiple models.

        Args:
            model_metrics: List of metric dictionaries
            model_names: List of model names
            output_file: Optional file to save comparison

        Returns:
            Comparison dictionary
        """
        if len(model_metrics) != len(model_names):
            raise ValueError("Number of models and names must match")

        comparison = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "models": model_names,
            "metric_comparison": {},
        }

        # Extract and compare key metrics
        for metric_key in ["exact_match", "f1", "bleu", "overall_quality"]:
            comparison["metric_comparison"][metric_key] = {}

            for model_name, metrics in zip(model_names, model_metrics):
                # Find metric value in nested structure
                value = self._extract_metric_value(metrics, metric_key)
                comparison["metric_comparison"][metric_key][model_name] = value

        # Determine best model for each metric
        comparison["best_model"] = {}
        for metric_key, values in comparison["metric_comparison"].items():
            if values:
                best_model = max(values, key=values.get)
                comparison["best_model"][metric_key] = best_model

        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(comparison, f, indent=2, ensure_ascii=False)

            logger.info(
                "Model comparison saved",
                extra={"file": output_file, "model_count": len(model_names)},
            )

        return comparison

    def _extract_metric_value(self, metrics: Dict[str, Any], key: str) -> float:
        """Extract metric value from nested metrics dict.

        Args:
            metrics: Metrics dictionary
            key: Metric key to extract

        Returns:
            Metric value or 0.0 if not found
        """
        # Try direct access
        if key in metrics:
            return float(metrics[key])

        # Try nested access
        for section in ["qa_metrics", "quality_metrics", "hallucination_metrics", "hindi_metrics"]:
            if section in metrics and key in metrics[section]:
                return float(metrics[section][key])

        return 0.0
