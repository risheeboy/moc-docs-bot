#!/usr/bin/env python3
"""
FastAPI OpenAPI Specification Export Script

This script exports the FastAPI auto-generated OpenAPI 3.0 specification
from the API Gateway to a standalone YAML file. Run this after building
the API Gateway service.

Usage:
    python openapi_export.py --output openapi.yaml
    python openapi_export.py --output openapi.json --format json

Requires:
    - FastAPI application running (or importable)
    - pyyaml, json installed
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

try:
    import yaml
except ImportError:
    print("Error: pyyaml not installed. Install with: pip install pyyaml")
    sys.exit(1)


def load_openapi_from_app(app_module: str = "api_gateway.main:app") -> Dict[str, Any]:
    """
    Load OpenAPI spec from FastAPI application.

    Args:
        app_module: Module path to FastAPI app (e.g., "api_gateway.main:app")

    Returns:
        Dictionary containing OpenAPI specification
    """
    try:
        module_path, app_name = app_module.rsplit(":", 1)
        module = __import__(module_path, fromlist=[app_name])
        app = getattr(module, app_name)

        if not hasattr(app, "openapi"):
            raise AttributeError(f"{app_module} does not have openapi() method")

        return app.openapi()
    except Exception as e:
        print(f"Error loading app from {app_module}: {e}")
        raise


def export_to_yaml(spec: Dict[str, Any], output_path: Path) -> None:
    """Export OpenAPI spec to YAML file."""
    with open(output_path, "w") as f:
        yaml.dump(spec, f, default_flow_style=False, sort_keys=False)
    print(f"Exported OpenAPI spec to {output_path}")


def export_to_json(spec: Dict[str, Any], output_path: Path) -> None:
    """Export OpenAPI spec to JSON file."""
    with open(output_path, "w") as f:
        json.dump(spec, f, indent=2)
    print(f"Exported OpenAPI spec to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Export FastAPI OpenAPI specification to YAML or JSON"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("openapi.yaml"),
        help="Output file path (default: openapi.yaml)"
    )
    parser.add_argument(
        "--format",
        choices=["yaml", "json"],
        default="yaml",
        help="Output format (default: yaml)"
    )
    parser.add_argument(
        "--app",
        default="api_gateway.main:app",
        help="FastAPI app module path (default: api_gateway.main:app)"
    )

    args = parser.parse_args()

    try:
        spec = load_openapi_from_app(args.app)

        if args.format == "yaml":
            export_to_yaml(spec, args.output)
        else:
            export_to_json(spec, args.output)

        print(f"✓ OpenAPI {spec.get('info', {}).get('version', 'unknown')} exported successfully")

    except Exception as e:
        print(f"✗ Export failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
