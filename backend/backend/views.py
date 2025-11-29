from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import (
    TaskListInputSerializer, 
    TaskAnalysisSerializer,
    SuggestedTaskSerializer
)
from .priority_algorithm import PriorityAlgorithm
from datetime import date
# POST /api/tasks/analyze/
class AnalyzeTasksView(APIView):
    def post(self, request):
        input_serializer = TaskListInputSerializer(data=request.data)
        if not input_serializer.is_valid():
            return Response(
                {
                    'error': 'Invalid input data',
                    'details': input_serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        tasks = input_serializer.validated_data['tasks']
        strategy = input_serializer.validated_data.get('strategy', 'smart_balance')
        
        try:
            algorithm = PriorityAlgorithm(strategy=strategy)
            analyzed_tasks = algorithm.analyze_tasks(tasks)
            output_serializer = TaskAnalysisSerializer(analyzed_tasks, many=True)
            
            return Response({
                'success': True,
                'strategy': strategy,
                'total_tasks': len(analyzed_tasks),
                'tasks': output_serializer.data
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response(
                {
                    'error': 'Task analysis failed',
                    'details': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {
                    'error': 'Internal server error',
                    'details': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# POST /api/tasks/suggest/
class SuggestTasksView(APIView):
    def post(self, request):
        input_serializer = TaskListInputSerializer(data=request.data)
        if not input_serializer.is_valid():
            return Response(
                {
                    'error': 'Invalid input data',
                    'details': input_serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        tasks = input_serializer.validated_data['tasks']
        strategy = input_serializer.validated_data.get('strategy', 'smart_balance')
        
        try:
            algorithm = PriorityAlgorithm(strategy=strategy)
            suggested_tasks = algorithm.suggest_top_tasks(tasks, count=3)
            output_serializer = SuggestedTaskSerializer(suggested_tasks, many=True)
            
            return Response({
                'success': True,
                'strategy': strategy,
                'date': date.today().isoformat(),
                'message': 'Here are your top 3 recommended tasks for today',
                'suggested_tasks': output_serializer.data
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response(
                {
                    'error': 'Task suggestion failed',
                    'details': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {
                    'error': 'Internal server error',
                    'details': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# GET /api/health/
class HealthCheckView(APIView):    
    def get(self, request):
        return Response({
            'status': 'healthy',
            'service': 'Task Analyzer API',
            'version': '1.0.0'
        }, status=status.HTTP_200_OK)