from rest_framework import serializers
from .models import Task, TaskDependency
from datetime import date

class TaskSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False, allow_null=True)
    title = serializers.CharField(max_length=255)
    due_date = serializers.DateField()
    estimated_hours = serializers.FloatField(min_value=0.1)
    importance = serializers.IntegerField(min_value=1, max_value=10)
    dependencies = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=list
    )
    
    def validate_due_date(self, value):
        if not isinstance(value, date):
            raise serializers.ValidationError("Invalid date format. Use YYYY-MM-DD")
        return value
    
    def validate_estimated_hours(self, value):
        if value <= 0:
            raise serializers.ValidationError("Estimated hours must be positive not negative or zero")
        if value > 1000:
            raise serializers.ValidationError("Estimated hours seems like unrealistic (>1000)")
        return value


class TaskAnalysisSerializer(serializers.Serializer):
    id = serializers.IntegerField(allow_null=True)
    title = serializers.CharField()
    due_date = serializers.DateField()
    estimated_hours = serializers.FloatField()
    importance = serializers.IntegerField()
    dependencies = serializers.ListField(child=serializers.IntegerField())
    priority_score = serializers.FloatField()
    priority_level = serializers.CharField()
    score_breakdown = serializers.DictField()
    

class TaskListInputSerializer(serializers.Serializer):
    tasks = serializers.ListField(
        child=TaskSerializer(),
        min_length=1
    )
    strategy = serializers.ChoiceField(
        choices=['smart_balance', 'fastest_wins', 'high_impact', 'deadline_driven'],
        default='smart_balance',
        required=False
    )
    
    def validate_tasks(self, tasks):
        ids = [t.get('id') for t in tasks if t.get('id') is not None]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError("Duplicate task IDs found")
        return tasks


class SuggestedTaskSerializer(serializers.Serializer):
    id = serializers.IntegerField(allow_null=True)
    title = serializers.CharField()
    due_date = serializers.DateField()
    estimated_hours = serializers.FloatField()
    importance = serializers.IntegerField()
    priority_score = serializers.FloatField()
    priority_level = serializers.CharField()
    reason = serializers.CharField()