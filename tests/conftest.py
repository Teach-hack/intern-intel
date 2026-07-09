"""Pytest conftest configuration."""

from __future__ import annotations

import os

# Set a secure test secret key for settings loading during the entire test suite run
os.environ["JWT_SECRET_KEY"] = "securetestsecretkeycontainingatleast32chars"
