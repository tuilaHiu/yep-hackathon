import pytest
from app.service.player_selector_terminal import parse_player_input

def test_parse_player_input():
    # Standard comma separated
    assert parse_player_input("1,2,3", 5) == [1, 2, 3]
    # Space separated
    assert parse_player_input("1 2 3", 5) == [1, 2, 3]
    # Mixed and spaces
    assert parse_player_input("1, 2 3", 5) == [1, 2, 3]
    # Single ID
    assert parse_player_input("1", 5) == [1]
    # Out of range (should warn and skip, return valid ones)
    assert parse_player_input("1, 6, 2", 5) == [1, 2]
    # Completely out of range
    assert parse_player_input("6, 7, 8", 5) == []
    # Non-numeric input
    assert parse_player_input("abc", 5) == []
    # Duplicate input
    assert parse_player_input("1, 1, 2", 5) == [1, 2]

def test_parse_player_input_empty():
    assert parse_player_input("", 5) == []
