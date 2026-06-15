"""Pytest tests for FitFindr tools (Milestone 3)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import create_fit_card, search_listings, suggest_outfit
from utils.data_loader import get_empty_wardrobe


def test_search_returns_results():
    results = search_listings("vintage graphic tee", size=None, max_price=50)

    assert isinstance(results, list)
    assert len(results) > 0
    assert all(isinstance(item, dict) for item in results)


def test_search_empty_results():
    results = search_listings("designer ballgown", size="XXS", max_price=5)

    assert results == []


def test_search_price_filter():
    results = search_listings("jacket", size=None, max_price=10)

    assert isinstance(results, list)
    assert all(item["price"] <= 10 for item in results)


def test_suggest_outfit_empty_wardrobe():
    item = search_listings("vintage graphic tee", size=None, max_price=50)[0]
    result = suggest_outfit(item, get_empty_wardrobe())

    assert isinstance(result, str)
    assert len(result.strip()) > 0


def test_create_fit_card_empty_outfit():
    item = search_listings("vintage graphic tee", size=None, max_price=50)[0]
    result = create_fit_card("", item)

    assert isinstance(result, str)
    assert len(result.strip()) > 0
    assert "outfit" in result.lower() or "suggestion" in result.lower()


def test_create_fit_card_normal_input():
    item = search_listings("vintage graphic tee", size=None, max_price=50)[0]
    outfit = "Pair this tee with baggy jeans and chunky sneakers."
    result = create_fit_card(outfit, item)

    assert isinstance(result, str)
    assert len(result.strip()) > 0
