from app.services.rounds import normalize, check_answer, calculate_points


def test_normalize():
    assert normalize("The Beatles!") == "beatles"
    assert normalize("  Queen  ") == "queen"


def test_check_answer_exact():
    ok, score = check_answer("Bohemian Rhapsody", "Bohemian Rhapsody")
    assert ok is True
    assert score == 100


def test_check_answer_typo():
    # опечатка должна засчитываться
    ok, score = check_answer("Bohemian Rapsody", "Bohemian Rhapsody")
    assert ok is True


def test_check_answer_wrong():
    ok, score = check_answer("Random Song", "Bohemian Rhapsody")
    assert ok is False


def test_points_fast_more_than_slow():
    fast = calculate_points(100, 2.0)
    slow = calculate_points(100, 25.0)
    assert fast > slow
