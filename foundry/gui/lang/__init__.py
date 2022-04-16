import json
import os

STRINGS = {}


def get_options() -> list:
    """Scans the /foundry/data/lang folder for any *.json file.  It takes the
    'language' key from that file and inserts it and the file path into an
    available language options list."""

    options = []
    directory = os.scandir("./foundry/data/lang/")

    for entry in directory:
        if entry.is_file() and entry.name.endswith(".json"):
            file = open(entry.path)
            file_data = json.load(file)
            options.append(tuple((file_data["language"], entry.path)))
            file.close()
    return options


def load_language(path):
    """This will load a new langauge.  English is always loaded first and then
    the new langauge is superimposed onto the English dictionary.  This way if
    there is a missing string in any language translation, it will default to
    the English string.

    NOTE: This requires that there is always an English string available for a
    solution."""

    english_file = open("./foundry/data/lang/english.json")
    new_lang_file = open(path, "r", encoding="utf-8")

    english_data = json.load(english_file)
    new_lang_data = json.load(new_lang_file)

    STRINGS.clear()
    STRINGS.update(english_data)
    STRINGS.update(new_lang_data)

    english_file.close()
    new_lang_file.close()


load_language("./foundry/data/lang/english.json")
