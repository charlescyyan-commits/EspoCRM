"""Workspace import bridge for the chitu-connector distribution directory."""

from pathlib import Path


__path__ = [str(Path(__file__).resolve().parent.parent / "chitu-connector" / "chitu_connector")]
