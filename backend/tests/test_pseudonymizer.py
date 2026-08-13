"""
Tests for Pseudonymization Service.
"""

import pytest
from app.services.pseudonymizer import Pseudonymizer


@pytest.fixture
def pseudonymizer():
    return Pseudonymizer(seed=42)


