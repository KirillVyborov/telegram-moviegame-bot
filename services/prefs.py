from dataclasses import dataclass

DIFFICULTY = {
    "easy": ((1, 20), 1),
    "medium": ((21, 60), 2),
    "hard": ((61, 150), 3)
}
DIFFICULTY_LABELS = {"easy": "Легкая", "medium": "Средняя", "hard": "Тяжелая"}

EPOCHS = {
    "any": None,
    "1940": (1940, 1959),
    "1960": (1960, 1979),
    "1980": (1980, 1999),
    "2000": (2000, 2019),
    "2020": (2020, 2039)
}

EPOCHS_LABELS = {
    "any": "Любая эпоха",
    "1940": "1940-1959",
    "1960": "1960-1979",
    "1980": "1980-1999",
    "2000": "2000-2019",
    "2020": "2020-наст.вр."
}

@dataclass
class Prefs:
    animation: bool = False
    difficulty: str = "easy"
    epoch: str = "any"

_prefs: dict[int, Prefs] = {}

def get_prefs(user_id: int) -> Prefs:
    return _prefs.setdefault(user_id, Prefs())

def reset_prefs(user_id: int) -> None:
    _prefs.pop(user_id, None)