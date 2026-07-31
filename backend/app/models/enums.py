import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    INSTRUCTOR = "instructor"
    TRAINEE = "trainee"


class ComparisonType(str, enum.Enum):
    """
    Determines how a raw performance value is compared against the
    Excellent / Good / Satisfactory thresholds.

    LOWER_IS_BETTER -> races, sprints (time in seconds/minutes)
    HIGHER_IS_BETTER -> rope climb height, chin-ups, push-ups, shuttle count
    """
    LOWER_IS_BETTER = "lower_is_better"
    HIGHER_IS_BETTER = "higher_is_better"


class GradeLevel(str, enum.Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    SATISFACTORY = "satisfactory"
    FAIL = "fail"  # did not meet even the satisfactory threshold


class TestCategory(str, enum.Enum):
    BPET = "bpet"  # Basic Physical Efficiency Test
    PPT = "ppt"    # Physical Proficiency Test


class ResultStatus(str, enum.Enum):
    PASS = "pass"
    FAIL = "fail"


class IndoorOutdoor(str, enum.Enum):
    INDOOR = "indoor"
    OUTDOOR = "outdoor"
