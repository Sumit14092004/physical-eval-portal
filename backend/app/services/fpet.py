"""
FPET activity templates and age-band resolution.

Per-activity marks are entered directly by the instructor (matching the
paper form), not derived from a raw performance value the way BPET/PPT
grading works. The Excellent/Very Good/Good/Fail bands below are a
PLACEHOLDER based on plausible percentage cutoffs, not an official
scale -- swap in the real criteria once that data is provided (the
paper forms suggest failing any individual event also forces an
overall Fail, which is implemented below, but the total-percentage
bands are provisional).
"""
from datetime import date


# (activity name, max marks) -- order matters, this is the exact
# sequence the form displays in, matching the paper layout.
FPET_TEMPLATES: dict[str, list[tuple[str, float]]] = {
    "below_35": [
        ("3.2 KMS Run", 10),
        ("M/Rope", 10),
        ("9 Feet Ditch", 10),
        ("6 Feet Wall", 10),
        ("F/Lift", 10),
    ],
    "35_40": [
        ("Run 3.2 KMS", 10),
        ("M/Rope", 10),
        ("6 Feet Wall", 10),
        ("9 Feet Ditch", 10),
    ],
    "40_45": [
        ("Run 3.2 KMS", 10),
        ("M/Rope", 10),
        ("5 Feet Wall", 10),
        ("8 Feet Ditch", 10),
    ],
    "female": [
        ("2 KM Run (with Arms & Eqpt)", 15),
        ("100 Yards Sprint (with Arms & Eqpt)", 10),
        ("7.5 Feet Ditch (with Arms & Eqpt)", 5),
        ("Vertical Rope 12 Feet (Eqpt Only)", 10),
        ("Push Ups (without Arms & Eqpt)", 10),
    ],
}


def compute_age(date_of_birth: date, as_of: date | None = None) -> int:
    as_of = as_of or date.today()
    years = as_of.year - date_of_birth.year
    if (as_of.month, as_of.day) < (date_of_birth.month, date_of_birth.day):
        years -= 1
    return years


def resolve_age_band(gender: str, date_of_birth: date, as_of: date | None = None) -> str:
    """
    Female trainees use a single fixed template regardless of age (per
    spec -- only one FEMALE activity list was given, no age split).
    Male trainees split at 35 and 40; ages 45+ fall back to the 40_45
    band since no band above that was specified.
    """
    if gender.strip().lower() == "female":
        return "female"

    age = compute_age(date_of_birth, as_of)
    if age < 35:
        return "below_35"
    if age < 40:
        return "35_40"
    return "40_45"


def get_template(age_band: str) -> list[tuple[str, float]]:
    return FPET_TEMPLATES[age_band]


def grade_from_marks(marks: dict[str, float], template: list[tuple[str, float]]) -> tuple[float, float, float, str]:
    """
    Returns (total_marks, max_total, percentage, grade).

    Failing any single event (entered as 0) forces an overall Fail,
    matching the pattern visible on the paper forms (an "F" in any
    column overrides an otherwise-passing total). The percentage bands
    below are placeholders -- see module docstring.
    """
    max_total = sum(max_marks for _, max_marks in template)
    total = sum(marks.get(name, 0) for name, _ in template)
    percentage = round((total / max_total) * 100, 2) if max_total else 0.0

    any_zero = any(marks.get(name, 0) == 0 for name, _ in template)
    if any_zero:
        grade = "Fail"
    elif percentage >= 90:
        grade = "Excellent"
    elif percentage >= 75:
        grade = "Very Good"
    elif percentage >= 50:
        grade = "Good"
    else:
        grade = "Fail"

    return round(total, 2), round(max_total, 2), percentage, grade
