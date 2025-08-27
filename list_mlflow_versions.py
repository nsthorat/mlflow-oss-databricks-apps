#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "click",
#     "packaging",
# ]
# ///
"""
Script to list available MLflow versions from PyPI.
Shows current major version in detail and older versions in compact format.

Usage:
    uv run list_mlflow_versions.py          # Display formatted versions
    uv run list_mlflow_versions.py --json   # Output all versions as JSON
"""

import json
import sys
import urllib.request
from packaging.version import parse
import click


def fetch_mlflow_versions():
    """Fetch MLflow package information from PyPI."""
    url = "https://pypi.org/pypi/mlflow/json"
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read().decode())


def display_versions_formatted(data):
    """Display MLflow versions in an organized format."""
    versions = sorted(data['releases'].keys(), key=parse, reverse=True)
    
    # Get latest version info
    latest = parse(data['info']['version'])
    latest_major = latest.major
    
    # Group by major.minor
    groups = {}
    for v in versions:
        parsed = parse(v)
        key = f'{parsed.major}.{parsed.minor}'
        if key not in groups:
            groups[key] = []
        groups[key].append(v)
    
    # Print header
    print(f'MLflow Versions (latest: {data["info"]["version"]})')
    print('=' * 40)
    
    # Show latest major version in detail
    print(f'\n▼ Version {latest_major}.x (current):')
    for key in sorted(groups.keys(), key=lambda x: parse(x + '.0'), reverse=True):
        if key.startswith(str(latest_major) + '.'):
            all_versions = groups[key]
            stable = [v for v in all_versions if 'rc' not in v and 'dev' not in v]
            rc = [v for v in all_versions if 'rc' in v]
            
            print(f'\n  {key}.x:')
            if stable:
                for v in stable:
                    prefix = '    → ' if v == data['info']['version'] else '    • '
                    print(f'{prefix}{v}')
            if rc:
                rc_str = ', '.join(rc)
                print(f'    • {len(rc)} pre-release: {rc_str}')
    
    # Show older major versions compactly
    older_majors = {}
    for key in groups.keys():
        major = int(key.split('.')[0])
        if major != latest_major:
            if major not in older_majors:
                older_majors[major] = []
            older_majors[major].extend(groups[key])
    
    if older_majors:
        print(f'\n▼ Older versions:')
        for major in sorted(older_majors.keys(), reverse=True):
            all_v = older_majors[major]
            stable = [v for v in all_v if 'rc' not in v and 'dev' not in v]
            latest_in_major = stable[0] if stable else all_v[0]
            oldest_in_major = stable[-1] if stable else all_v[-1]
            print(f'  {major}.x: {latest_in_major} → {oldest_in_major} ({len(all_v)} total)')


def display_versions_json(data):
    """Display all MLflow versions as JSON."""
    versions = sorted(data['releases'].keys(), key=parse, reverse=True)
    output = {
        "latest": data['info']['version'],
        "total_versions": len(versions),
        "versions": versions
    }
    print(json.dumps(output, indent=2))


@click.command()
@click.option('--json', 'output_json', is_flag=True, help='Output all versions as JSON')
def main(output_json):
    """List available MLflow versions from PyPI."""
    if not output_json:
        print("Fetching MLflow versions from PyPI...")
        print()
    
    try:
        data = fetch_mlflow_versions()
    except Exception as e:
        if output_json:
            error_output = {"error": str(e)}
            print(json.dumps(error_output, indent=2))
        else:
            print(f"Error fetching versions: {e}", file=sys.stderr)
        sys.exit(1)
    
    if output_json:
        display_versions_json(data)
    else:
        display_versions_formatted(data)


if __name__ == "__main__":
    main()