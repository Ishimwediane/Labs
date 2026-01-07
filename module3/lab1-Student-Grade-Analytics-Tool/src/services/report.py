from typing import List
from src.models.entities import Student
from src.models.schemas import GradeAnalyticsReport
from src.services.distribution import DistributionService
from src.services.ranking import RankingService
from src.services.trend import TrendService

class ReportService:
    def __init__(self, students: List[Student]):
        self.students = students

    def generate_full_report(self) -> GradeAnalyticsReport:
        """Assembles all data using GradeAnalyticsReport TypedDict."""
        ranking_service = RankingService(self.students)
        
        # Use the TypedDict constructor for clear type safety and Mypy compliance
        return GradeAnalyticsReport(
            total_students=len(self.students),
            grade_distribution=DistributionService.calculate_grade_distribution(self.students),
            major_grouping=DistributionService.group_by_major(self.students),
            top_performers=[tp._asdict() for tp in ranking_service.get_top_performers()],
            overall_average=RankingService.calculate_overall_average(self.students),
            rolling_averages=TrendService.calculate_rolling_averages(self.students)
        )
