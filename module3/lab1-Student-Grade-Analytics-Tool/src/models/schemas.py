from typing import Dict, List, TypedDict, Union


class GradeAnalyticsReport(TypedDict):
    total_students: int
    grade_distribution: Dict[str, int]
    major_grouping: Dict[str, List[str]]
    top_performers: List[Dict[str, Union[str, float]]]
    overall_average: float
    rolling_averages: Dict[str, List[float]]
