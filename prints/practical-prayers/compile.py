#!/usr/bin/env python3
"""Practical Prayers — data-driven build via bookkit. See prints/BOOKS.md."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "bookkit"))
from engine import build
build(pathlib.Path(__file__).parent)
