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
