#!/usr/bin/env python3
"""
DLT Generator Tool
Generates service structure, pipeline scaffolding, and documentation templates
based on the provided JSON configuration.
"""

import os
import sys
import json
import argparse
from pathlib import Path


def generate_service(config_path: str):
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    project_name = config.get("project_name", "hubspot-deals-etl")
    service_name = config.get("service_name", "hubspot_deals")
    ports = config.get("ports", {"dev": 5200, "stage": 5201, "prod": 5202})

    print(f"==================================================")
    print(f"  DLT Service Generator")
    print(f"  Project Name: {project_name}")
    print(f"  Service Name: {service_name}")
    print(f"  Configured Ports: Dev={ports.get('dev')}, Stage={ports.get('stage')}, Prod={ports.get('prod')}")
    print(f"==================================================")

    # 1. Scaffolding Directories
    directories = [
        Path("docs"),
        Path("services"),
        Path("test-results"),
        Path("logs"),
        Path("api/services"),
        Path("api/tests"),
    ]
    for d in directories:
        d.mkdir(parents=True, exist_ok=True)
        print(f"[OK] Directory verified: {d}/")

    # 2. Template Documentation Scaffolding
    doc_templates = {
        Path("docs/api-integration.md"): "# HubSpot CRM API Integration Documentation\n\n## Overview\n",
        Path("docs/database-schema.md"): "# Database Schema Design: HubSpot Deals Data Extraction Service\n\n## Overview\n",
        Path("docs/api-documentation.md"): "# Service API Specification Documentation\n\n## Overview\n",
    }
    for doc_path, default_content in doc_templates.items():
        if not doc_path.exists():
            doc_path.write_text(default_content, encoding="utf-8")
            print(f"[OK] Generated template: {doc_path}")
        else:
            print(f"[OK] Existing template preserved: {doc_path}")

    # 3. Environment Scaffolding
    env_file = Path(".env.example")
    if not env_file.exists():
        env_file.write_text(
            f"# {project_name} Environment Configuration\n"
            f"PIPELINE_NAME={service_name}_pipeline\n"
            f"DATABASE_SCHEMA={service_name}\n"
            f"PORT={ports.get('dev', 5200)}\n",
            encoding="utf-8"
        )
        print(f"[OK] Generated environment template: {env_file}")
    else:
        print(f"[OK] Environment template verified: {env_file}")

    print("==================================================")
    print(f"[SUCCESS] Scaffolding for '{project_name}' generated successfully.")
    print(f"[NEXT STEP] Review and customize documents in docs/ directory.")
    print("==================================================")


def main():
    parser = argparse.ArgumentParser(description="DLT Generator Tool")
    parser.add_argument("-c", "--config", required=True, help="Path to configuration JSON file")
    args = parser.parse_args()

    if not os.path.exists(args.config):
        print(f"Error: Config file '{args.config}' not found.")
        sys.exit(1)

    generate_service(args.config)


if __name__ == "__main__":
    main()
