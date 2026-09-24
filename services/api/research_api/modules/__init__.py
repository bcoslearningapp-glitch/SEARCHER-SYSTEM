"""Bounded domain modules (PRD §58).

No module may bypass another module's public service/contract for convenience.
Each module exposes its public surface through its `service` module; other
modules must not import its `models` directly.
"""
