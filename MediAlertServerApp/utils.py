from django.db.models import Count
from django.contrib.auth.models import User

def assign_reviewer_to_report():
    professionals = User.objects.filter(profile__user_type='PROFESSIONAL')

    professional_workload = professionals.annotate(report_count=Count('assigned_reviews')).order_by('report_count')

    if professional_workload.exists():
        min_reports = professional_workload.first().report_count
        candidates = professional_workload.filter(report_count=min_reports)

        if candidates.count() > 1:
            return None

        return candidates.first()
    
    return None

