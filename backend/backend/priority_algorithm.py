from datetime import date, timedelta
from typing import List, Dict, Set, Tuple
import math

class PriorityAlgorithm:
    def __init__(self, strategy='smart_balance'):
        self.strategy = strategy
        self.weights = self._get_weights()
    
    def _get_weights(self) -> Dict[str, float]:
        strategies = {
            'smart_balance': {
                'urgency': 0.35,
                'importance': 0.30,
                'effort': 0.15,
                'dependencies': 0.20
            },
            'fastest_wins': {
                'urgency': 0.20,
                'importance': 0.20,
                'effort': 0.50,
                'dependencies': 0.10
            },
            'high_impact': {
                'urgency': 0.15,
                'importance': 0.60,
                'effort': 0.10,
                'dependencies': 0.15
            },
            'deadline_driven': {
                'urgency': 0.60,
                'importance': 0.20,
                'effort': 0.05,
                'dependencies': 0.15
            }
        }
        return strategies.get(self.strategy, strategies['smart_balance'])
    
    def calculate_urgency_score(self, due_date: date) -> float:
        today = date.today()
        days_until_due = (due_date - today).days
        if days_until_due < 0:
            overdue_penalty = min(abs(days_until_due) * 2, 50)
            return min(100, 100 + overdue_penalty)
        if days_until_due == 0:
            return 95
        if days_until_due <= 7:
            return 90 - (days_until_due * 4)
        if days_until_due <= 14:
            return 60 - ((days_until_due - 7) * 2)
        if days_until_due <= 30:
            return 40 - ((days_until_due - 14) * 1)

        return max(10, 40 - (days_until_due - 30) * 0.5)
    
    def calculate_importance_score(self, importance: int) -> float:
        return importance * 10
    
    def calculate_effort_score(self, estimated_hours: float) -> float:
        if estimated_hours < 1:
            return 90 + (1 - estimated_hours) * 10
        score = 100 - (math.log10(estimated_hours + 1) * 35)
        return max(10, min(100, score))
    
    def calculate_dependency_score(self, task_id: int, all_tasks: List[Dict], 
                                    dependency_map: Dict[int, List[int]]) -> float:
        blocked_count = sum(
            1 for deps in dependency_map.values() 
            if task_id in deps
        )
        has_dependencies = task_id in dependency_map and len(dependency_map[task_id]) > 0

        score = 50
        score += min(blocked_count * 10, 50)
        if has_dependencies:
            score -= 20
        
        return max(0, min(100, score))
    
    def detect_circular_dependencies(self, dependency_map: Dict[int, List[int]]) -> List[List[int]]:
        def dfs(node: int, visited: Set[int], path: List[int]) -> List[List[int]]:
            if node in path:
                cycle_start = path.index(node)
                return [path[cycle_start:]]
            
            if node in visited:
                return []
            
            visited.add(node)
            path.append(node)
            
            cycles = []
            for dependency in dependency_map.get(node, []):
                cycles.extend(dfs(dependency, visited, path[:]))
            
            return cycles
        
        visited = set()
        all_cycles = []
        
        for task_id in dependency_map.keys():
            if task_id not in visited:
                cycles = dfs(task_id, visited, [])
                all_cycles.extend(cycles)
        
        return all_cycles
    
    def calculate_priority_score(self, task: Dict, all_tasks: List[Dict], 
                                 dependency_map: Dict[int, List[int]]) -> Tuple[float, Dict]:
        urgency = self.calculate_urgency_score(task['due_date'])
        importance = self.calculate_importance_score(task['importance'])
        effort = self.calculate_effort_score(task['estimated_hours'])
        dependencies = self.calculate_dependency_score(
            task.get('id'), all_tasks, dependency_map
        )
        weights = self.weights
        priority_score = (
            urgency * weights['urgency'] +
            importance * weights['importance'] +
            effort * weights['effort'] +
            dependencies * weights['dependencies']
        )
        breakdown = {
            'urgency': round(urgency, 2),
            'importance': round(importance, 2),
            'effort': round(effort, 2),
            'dependencies': round(dependencies, 2),
            'weights': weights
        }
        
        return round(priority_score, 2), breakdown
    
    def get_priority_level(self, score: float) -> str:
        if score >= 80:
            return 'Critical'
        elif score >= 65:
            return 'High'
        elif score >= 45:
            return 'Medium'
        else:
            return 'Low'
    
    def analyze_tasks(self, tasks: List[Dict]) -> List[Dict]:
        dependency_map = {}
        for task in tasks:
            task_id = task.get('id')
            deps = task.get('dependencies', [])
            if task_id and deps:
                dependency_map[task_id] = deps

        cycles = self.detect_circular_dependencies(dependency_map)
        if cycles:
            raise ValueError(f"Circular dependencies detected: {cycles}")

        analyzed_tasks = []
        for task in tasks:
            score, breakdown = self.calculate_priority_score(
                task, tasks, dependency_map
            )
            
            analyzed_task = {
                **task,
                'priority_score': score,
                'priority_level': self.get_priority_level(score),
                'score_breakdown': breakdown
            }
            analyzed_tasks.append(analyzed_task)
        analyzed_tasks.sort(key=lambda x: x['priority_score'], reverse=True)
        
        return analyzed_tasks
    
    def suggest_top_tasks(self, tasks: List[Dict], count: int = 3) -> List[Dict]:
        analyzed_tasks = self.analyze_tasks(tasks)
        top_tasks = analyzed_tasks[:count]

        for task in top_tasks:
            reason = self._generate_reason(task)
            task['reason'] = reason
        
        return top_tasks
    
    def _generate_reason(self, task: Dict) -> str:
        breakdown = task['score_breakdown']
        reasons = []
        days_until = (task['due_date'] - date.today()).days
        if days_until < 0:
            reasons.append(f"overdue by {abs(days_until)} day(s)")
        elif days_until == 0:
            reasons.append("due today")
        elif days_until <= 3:
            reasons.append(f"due in {days_until} day(s)")
        if task['importance'] >= 8:
            reasons.append("high importance")
        if task['estimated_hours'] <= 2:
            reasons.append("quick win")
        if breakdown['dependencies'] > 70:
            reasons.append("blocks other tasks")
        if self.strategy == 'fastest_wins' and task['estimated_hours'] <= 1:
            reasons.append("fast to complete")
        elif self.strategy == 'high_impact' and task['importance'] >= 8:
            reasons.append("maximum impact")
        elif self.strategy == 'deadline_driven' and days_until <= 2:
            reasons.append("urgent deadline")
        
        if not reasons:
            reasons.append("balanced priority across all factors")
        
        return "Recommended because: " + ", ".join(reasons)