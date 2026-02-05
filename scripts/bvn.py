#!/usr/bin/env python3
"""
Bump Version Number (bvn) - Version Management Script for mcp-arangodb-async

This script manages version numbers across the project with semantic versioning validation.

Usage:
    bvn.py --version "X.Y.Z"                    # Bump version and set publish_on_pypi=false
    bvn.py --version "X.Y.Z" --pypi true        # Bump version and set publish_on_pypi=true
    bvn.py --version "X.Y.Z" --pypi false       # Bump version and set publish_on_pypi=false
    bvn.py --pypi true                          # Only set publish_on_pypi=true
    bvn.py --pypi false                         # Only set publish_on_pypi=false
    bvn.py --version "X.Y.Z" --dry-run          # Preview changes without applying

Features:
    - Semantic versioning validation (ensures new version > current version)
    - Updates version in pyproject.toml
    - Manages publish_on_pypi flag in pyproject.toml
    - Dry-run mode for previewing changes
    - Comprehensive error handling
    - Clear success/error messages
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Tuple, Optional


class SemanticVersion:
    """Semantic version parser and comparator."""
    
    def __init__(self, version_string: str):
        """Parse semantic version string (X.Y.Z)."""
        self.original = version_string
        match = re.match(r'^(\d+)\.(\d+)\.(\d+)$', version_string)
        if not match:
            raise ValueError(f"Invalid semantic version format: '{version_string}'. Expected: X.Y.Z")
        
        self.major = int(match.group(1))
        self.minor = int(match.group(2))
        self.patch = int(match.group(3))
    
    def __gt__(self, other: 'SemanticVersion') -> bool:
        """Check if this version is greater than another."""
        if self.major != other.major:
            return self.major > other.major
        if self.minor != other.minor:
            return self.minor > other.minor
        return self.patch > other.patch
    
    def __eq__(self, other: 'SemanticVersion') -> bool:
        """Check if versions are equal."""
        return (self.major == other.major and 
                self.minor == other.minor and 
                self.patch == other.patch)
    
    def __str__(self) -> str:
        """Return version string."""
        return f"{self.major}.{self.minor}.{self.patch}"


class VersionManager:
    """Manages version numbers across project files."""
    
    def __init__(self, project_root: Path):
        """Initialize version manager with project root directory."""
        self.project_root = project_root
        self.pyproject_path = project_root / "pyproject.toml"
        
        # Validate project structure
        if not self.pyproject_path.exists():
            raise FileNotFoundError(f"pyproject.toml not found at {self.pyproject_path}")
    
    def get_current_version(self) -> str:
        """Extract current version from pyproject.toml."""
        content = self.pyproject_path.read_text(encoding='utf-8')
        
        # Match: version = "X.Y.Z"
        match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
        if not match:
            raise ValueError("Could not find version field in pyproject.toml")
        
        return match.group(1)
    
    def get_publish_flag(self) -> bool:
        """Extract current publish_on_pypi flag from pyproject.toml."""
        content = self.pyproject_path.read_text(encoding='utf-8')
        
        # Match: publish_on_pypi = true/false
        match = re.search(r'^publish_on_pypi\s*=\s*(true|false)', content, re.MULTILINE)
        if not match:
            # Default to false if not found
            return False
        
        return match.group(1) == 'true'
    
    def update_version(self, new_version: str, dry_run: bool = False) -> Tuple[int, str]:
        """
        Update version in pyproject.toml.
        
        Returns:
            Tuple of (files_modified_count, summary_message)
        """
        current_version = self.get_current_version()
        
        # Validate semantic versioning
        try:
            current_sem = SemanticVersion(current_version)
            new_sem = SemanticVersion(new_version)
        except ValueError as e:
            return (0, f"❌ Error: {e}")
        
        # Check if new version is greater
        if new_sem == current_sem:
            return (0, f"❌ Error: New version ({new_version}) is the same as current version ({current_version})")
        
        if not new_sem > current_sem:
            return (0, f"❌ Error: New version ({new_version}) must be greater than current version ({current_version})")
        
        # Update pyproject.toml
        content = self.pyproject_path.read_text(encoding='utf-8')
        new_content = re.sub(
            r'^(version\s*=\s*)"[^"]+"',
            rf'\1"{new_version}"',
            content,
            count=1,
            flags=re.MULTILINE
        )
        
        if dry_run:
            print(f"\n[DRY RUN] Would update {self.pyproject_path}:")
            print(f"  version = \"{current_version}\" → \"{new_version}\"")
            return (1, f"✓ Dry run complete: 1 file would be modified")
        
        # Write changes
        self.pyproject_path.write_text(new_content, encoding='utf-8')
        
        return (1, f"✓ Version updated: {current_version} → {new_version}\n  Modified: {self.pyproject_path}")
    
    def update_publish_flag(self, publish: bool, dry_run: bool = False) -> Tuple[int, str]:
        """
        Update publish_on_pypi flag in pyproject.toml.
        
        Returns:
            Tuple of (files_modified_count, summary_message)
        """
        current_flag = self.get_publish_flag()
        new_flag_str = 'true' if publish else 'false'
        current_flag_str = 'true' if current_flag else 'false'
        
        if current_flag == publish:
            return (0, f"ℹ Info: publish_on_pypi is already set to {new_flag_str}")
        
        # Update pyproject.toml
        content = self.pyproject_path.read_text(encoding='utf-8')
        
        # Check if publish_on_pypi exists
        if 'publish_on_pypi' in content:
            new_content = re.sub(
                r'^(publish_on_pypi\s*=\s*)(true|false)',
                rf'\1{new_flag_str}',
                content,
                count=1,
                flags=re.MULTILINE
            )
        else:
            # Add publish_on_pypi after version line
            new_content = re.sub(
                r'^(version\s*=\s*"[^"]+")',
                rf'\1\npublish_on_pypi = {new_flag_str}  # Set to false to skip publish, Set to true when you want to publish with an increased version number',
                content,
                count=1,
                flags=re.MULTILINE
            )
        
        if dry_run:
            print(f"\n[DRY RUN] Would update {self.pyproject_path}:")
            print(f"  publish_on_pypi = {current_flag_str} → {new_flag_str}")
            return (1, f"✓ Dry run complete: 1 file would be modified")
        
        # Write changes
        self.pyproject_path.write_text(new_content, encoding='utf-8')
        
        return (1, f"✓ Publish flag updated: {current_flag_str} → {new_flag_str}\n  Modified: {self.pyproject_path}")


def main():
    """Main entry point for version bump script."""
    parser = argparse.ArgumentParser(
        description="Bump Version Number (bvn) - Manage version numbers for mcp-arangodb-async",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --version "0.3.3"                    # Bump version to 0.3.3 and set publish_on_pypi=false
  %(prog)s --version "0.4.0" --pypi true        # Bump version to 0.4.0 and set publish_on_pypi=true
  %(prog)s --pypi true                          # Only set publish_on_pypi=true
  %(prog)s --pypi false                         # Only set publish_on_pypi=false
  %(prog)s --version "0.3.3" --dry-run          # Preview changes without applying
        """
    )
    
    parser.add_argument(
        '--version',
        type=str,
        help='New version number (semantic versioning: X.Y.Z)'
    )
    
    parser.add_argument(
        '--pypi',
        type=str,
        choices=['true', 'false'],
        help='Set publish_on_pypi flag (true or false)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without applying them'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.version and not args.pypi:
        parser.error("At least one of --version or --pypi must be specified")
    
    # Find project root (parent of scripts directory)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    try:
        manager = VersionManager(project_root)
        
        print("=" * 80)
        print("BUMP VERSION NUMBER (bvn) - Version Management Script")
        print("=" * 80)
        print(f"\nProject root: {project_root}")
        print(f"Current version: {manager.get_current_version()}")
        print(f"Current publish_on_pypi: {manager.get_publish_flag()}")
        
        total_files_modified = 0
        messages = []
        
        # Update version if specified
        if args.version:
            print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Updating version to {args.version}...")
            count, message = manager.update_version(args.version, dry_run=args.dry_run)
            total_files_modified += count
            messages.append(message)
            
            # If version bump succeeds and no --pypi flag specified, set publish_on_pypi=false
            if count > 0 and not args.pypi and not args.dry_run:
                print(f"\nSetting publish_on_pypi=false (default after version bump)...")
                count2, message2 = manager.update_publish_flag(False, dry_run=False)
                if count2 > 0:
                    messages.append(message2)
        
        # Update publish flag if specified
        if args.pypi:
            publish_value = args.pypi == 'true'
            print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Setting publish_on_pypi={args.pypi}...")
            count, message = manager.update_publish_flag(publish_value, dry_run=args.dry_run)
            total_files_modified += count
            messages.append(message)
        
        # Print summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        for message in messages:
            print(message)
        
        if total_files_modified > 0:
            print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Total files {'would be ' if args.dry_run else ''}modified: {total_files_modified}")
        
        print("=" * 80)
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

