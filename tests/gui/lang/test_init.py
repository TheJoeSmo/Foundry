from foundry.gui.lang import STRINGS, get_options, load_language


def test_english_is_available():
    assert ("English", "./foundry/data/lang/english.json") in get_options()


def test_english_is_english():
    load_language("./foundry/data/lang/english.json")
    assert STRINGS["language"] == "English"


def test_load_spanish_is_spanish():
    load_language("./foundry/data/lang/spanish.json")
    assert STRINGS["language"] == "Español (Spanish)"


def test_missing_field_is_english():
    """In this test the 'lives_title' needs to be missing from the test
    file."""
    load_language("./tests/gui/lang/spanish.json")
    assert STRINGS["language"] == "Español (Spanish)"
    assert STRINGS["lives_title"] == "Player Lives"
