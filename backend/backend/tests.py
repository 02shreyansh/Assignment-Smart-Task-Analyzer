from django.test import TestCase
from datetime import date, timedelta
from .priority_algorithm import PriorityAlgorithm


class PriorityAlgorithmTests(TestCase):
    def setUp(self):
        self.algorithm = PriorityAlgorithm(strategy='smart_balance')
        self.today = date.today()
    
    def test_urgency_score_past_due(self):
        past_date = self.today - timedelta(days=5)
        score = self.algorithm.calculate_urgency_score(past_date)
        self.assertGreaterEqual(score, 100)
    
    def test_urgency_score_due_today(self):
        score = self.algorithm.calculate_urgency_score(self.today)
        self.assertEqual(score, 95)
    
    def test_urgency_score_future(self):
        future_date = self.today + timedelta(days=30)
        score = self.algorithm.calculate_urgency_score(future_date)
        self.assertLess(score, 50)
    
    def test_importance_score_conversion(self):
        self.assertEqual(self.algorithm.calculate_importance_score(1), 10)
        self.assertEqual(self.algorithm.calculate_importance_score(5), 50)
        self.assertEqual(self.algorithm.calculate_importance_score(10), 100)
    
    def test_effort_score_quick_tasks(self):
        quick_score = self.algorithm.calculate_effort_score(0.5)
        long_score = self.algorithm.calculate_effort_score(10)
        self.assertGreater(quick_score, long_score)
    
    def test_circular_dependency_detection(self):
        dependency_map = {
            1: [2],
            2: [1]
        }
        cycles = self.algorithm.detect_circular_dependencies(dependency_map)
        self.assertGreater(len(cycles), 0)
    
    def test_no_circular_dependency(self):
        dependency_map = {
            1: [2],
            2: [3]
        }
        cycles = self.algorithm.detect_circular_dependencies(dependency_map)
        self.assertEqual(len(cycles), 0)
    
    def test_analyze_tasks_sorting(self):
        tasks = [
            {
                'id': 1,
                'title': 'Low priority task',
                'due_date': self.today + timedelta(days=30),
                'estimated_hours': 10,
                'importance': 3,
                'dependencies': []
            },
            {
                'id': 2,
                'title': 'High priority task',
                'due_date': self.today,
                'estimated_hours': 1,
                'importance': 10,
                'dependencies': []
            }
        ]
        
        analyzed = self.algorithm.analyze_tasks(tasks)
        self.assertEqual(analyzed[0]['id'], 2)
        self.assertGreater(
            analyzed[0]['priority_score'],
            analyzed[1]['priority_score']
        )
    
    def test_dependency_score_blocking_tasks(self):
        tasks = [
            {'id': 1, 'dependencies': []},
            {'id': 2, 'dependencies': [1]},
            {'id': 3, 'dependencies': [1]}
        ]
        
        dependency_map = {
            2: [1],
            3: [1]
        }
        score = self.algorithm.calculate_dependency_score(1, tasks, dependency_map)
        self.assertGreater(score, 60)
    
    def test_missing_data_handling(self):
        tasks = [
            {
                'id': 1,
                'title': 'Task without dependencies',
                'due_date': self.today + timedelta(days=5),
                'estimated_hours': 2,
                'importance': 7
            }
        ]
        analyzed = self.algorithm.analyze_tasks(tasks)
        self.assertEqual(len(analyzed), 1)
        self.assertIn('priority_score', analyzed[0])
    
    def test_strategy_weights(self):
        smart_balance = PriorityAlgorithm('smart_balance')
        fastest_wins = PriorityAlgorithm('fastest_wins')
        
        self.assertNotEqual(
            smart_balance.weights['effort'],
            fastest_wins.weights['effort']
        )
        self.assertGreater(
            fastest_wins.weights['effort'],
            smart_balance.weights['effort']
        )
    
    def test_suggest_top_tasks(self):
        tasks = [
            {
                'id': 1,
                'title': 'Task 1',
                'due_date': self.today,
                'estimated_hours': 1,
                'importance': 8,
                'dependencies': []
            },
            {
                'id': 2,
                'title': 'Task 2',
                'due_date': self.today + timedelta(days=10),
                'estimated_hours': 5,
                'importance': 5,
                'dependencies': []
            }
        ]
        
        suggestions = self.algorithm.suggest_top_tasks(tasks, count=2)
        self.assertEqual(len(suggestions), 2)
        self.assertIn('reason', suggestions[0])
        self.assertTrue(suggestions[0]['reason'].startswith('Recommended because:'))


class APIEndpointTests(TestCase):
    def test_analyze_endpoint_valid_input(self):
        payload = {
            'tasks': [
                {
                    'id': 1,
                    'title': 'Test task',
                    'due_date': date.today().isoformat(),
                    'estimated_hours': 2,
                    'importance': 7,
                    'dependencies': []
                }
            ],
            'strategy': 'smart_balance'
        }
        
        response = self.client.post(
            '/api/tasks/analyze/',
            data=payload,
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertIn('tasks', response.json())
    
    def test_analyze_endpoint_invalid_input(self):
        payload = {
            'tasks': [
                {
                    'title': 'Invalid task',
                    'due_date': 'not-a-date',
                    'estimated_hours': -5,
                    'importance': 15
                }
            ]
        }
        
        response = self.client.post(
            '/api/tasks/analyze/',
            data=payload,
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_suggest_endpoint(self):
        payload = {
            'tasks': [
                {
                    'id': 1,
                    'title': 'Task 1',
                    'due_date': date.today().isoformat(),
                    'estimated_hours': 1,
                    'importance': 9,
                    'dependencies': []
                }
            ]
        }
        
        response = self.client.post(
            '/api/tasks/suggest/',
            data=payload,
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('suggested_tasks', response.json())
    
    def test_health_check_endpoint(self):
        response = self.client.get('/api/health/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'healthy')