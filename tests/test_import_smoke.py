from __future__ import annotations


def test_package_imports() -> None:
    import poker_training_bot

    assert poker_training_bot.__version__ == "0.0.0"
