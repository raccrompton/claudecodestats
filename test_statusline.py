#!/usr/bin/env python3
"""Tests for statusline.py — plain asserts, no framework. Run: python3 test_statusline.py"""
import sys

import statusline


def test_repo():
    assert statusline.repo({"workspace": {"current_dir": "/home/u/my-repo"}}) == "my-repo"
    assert statusline.repo({"workspace": {"current_dir": "/home/u/my-repo/"}}) == "my-repo"
    assert statusline.repo({"cwd": "/home/u/other"}) == "other"
    assert statusline.repo({}) == "-"


def test_branch():
    # Not a git repo -> fallback.
    assert statusline.branch({"cwd": "/"}) == "-"
    # No workdir at all -> fallback.
    assert statusline.branch({}) == "-"
    # This repo's checkout -> a non-empty branch name.
    here = statusline.branch({"cwd": __import__("os").path.dirname(__import__("os").path.abspath(__file__))})
    assert here != "-" and here != ""


def test_model():
    assert statusline.model({"model": {"display_name": "Claude Opus 4.7"}}) == "opus-4.7"
    assert statusline.model({"model": {"display_name": "Claude Sonnet 4.6"}}) == "sonnet-4.6"
    # Unparseable -> raw display name returned verbatim.
    assert statusline.model({"model": {"display_name": "Mystery Model"}}) == "Mystery Model"
    # Missing -> fallback.
    assert statusline.model({}) == "-"
    assert statusline.model({"model": {}}) == "-"


def test_diff():
    assert statusline.diff({"cost": {"total_lines_added": 120, "total_lines_removed": 30}}) == "+120/-30"
    assert statusline.diff({"cost": {}}) == "+0/-0"
    assert statusline.diff({}) == "+0/-0"


def test_duration():
    assert statusline.duration({"cost": {"total_duration_ms": 12 * 60000}}) == "12m"
    assert statusline.duration({"cost": {"total_duration_ms": 64 * 60000}}) == "1h4m"
    # Sub-minute rounds down to 0m.
    assert statusline.duration({"cost": {"total_duration_ms": 5000}}) == "0m"
    assert statusline.duration({"cost": {}}) == "0m"
    assert statusline.duration({}) == "0m"


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS {name}")
            except AssertionError as e:
                failures += 1
                print(f"FAIL {name}: {e}")
    sys.exit(1 if failures else 0)
