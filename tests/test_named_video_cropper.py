import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from app.service.named_video_cropper import sanitize_filename

def test_sanitize_filename():
    test_cases = [
        ("Nguyen", "nguyen"),
        ("Nguyen Van A", "nguyen_van_a"),
        ("Player #1", "player_1"),
        ("Trần", "tran"),
        ("!!!", "player_unknown"),
        ("  Space Test  ", "space_test"),
        ("Mixed-Case_Symbols!", "mixed_case_symbols"),
        ("123abc", "123abc"),
    ]
    
    for input_name, expected in test_cases:
        result = sanitize_filename(input_name)
        print(f"Input: '{input_name}' -> Output: '{result}' | Expected: '{expected}'")
        assert result == expected, f"Failed for {input_name}: got {result}, expected {expected}"

if __name__ == "__main__":
    try:
        test_sanitize_filename()
        print("\nAll sanitize_filename tests passed!")
    except AssertionError as e:
        print(f"\nTest failed: {e}")
        sys.exit(1)
