from django.urls import path
from .views import AnalyzeTasksView, SuggestTasksView, HealthCheckView

urlpatterns = [
    path('tasks/analyze/', AnalyzeTasksView.as_view(), name='analyze-tasks'),
    path('tasks/suggest/', SuggestTasksView.as_view(), name='suggest-tasks'),
    path('health/', HealthCheckView.as_view(), name='health-check'),
]