# Smart Task Analyzer

A sophisticated task management system that intelligently scores and prioritizes tasks based on urgency, importance, effort, and dependencies. Built with Django REST Framework backend and vanilla JavaScript frontend.

## 🚀 Setup Instructions

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Backend Setup

1. **Create a virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**
```bash
pip install django djangorestframework
```

3. **Create Django project structure**
```bash
django-admin startproject core backend/
cd backend
django-admin startapp backend
```

4. **Copy backend files**
Copy the following files into the `backend/` directory:
- `models.py`
- `serializers.py`
- `priority_algorithm.py`
- `views.py`
- `urls.py`
- `tests.py`

5. **Configure Django settings**

Add to `backend/settings.py`:
```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'backend',
    'corsheaders',
    'rest_framework',
]

# Add CORS headers for local development
CORS_ALLOW_ALL_ORIGINS = True  # Only for development!
```

Install CORS headers:
```bash
pip install django-cors-headers
```

Add to `INSTALLED_APPS`:
```python
'corsheaders',
```

Add to `MIDDLEWARE`:
```python
'corsheaders.middleware.CorsMiddleware',
```

6. **Update main URLs**

Edit `backend/urls.py`:
```python
from django.contrib import admin
from django.urls import path,include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
    path('api/tasks/', include('backend.urls')),
]
```

7. **Run migrations and start server**
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

Backend will be available at `http://localhost:8000`

### Frontend Setup

1. **Update API configuration**

Open `script.js` and update line 4:
```javascript
const API_BASE_URL = 'http://localhost:8000/api/tasks';
```

2. **Open in browser**
Simply open `index.html` in your web browser, or use a local server:
```bash
python -m http.server 8080
# Visit http://localhost:8080
```

### Running Tests

```bash
python manage.py test tasks
```

---

## 🧮 Algorithm Explanation

### Overview
The priority scoring algorithm calculates a weighted score (0-100+) for each task by analyzing four key factors: urgency, importance, effort, and dependencies. The final priority score determines task ranking and helps users focus on what matters most.

### Core Components

**1. Urgency Scoring (0-100+)**

The urgency component uses an exponential decay model that heavily weights imminent deadlines:

- **Overdue tasks** receive scores above 100, with penalties increasing by 2 points per day overdue (capped at +50)
- **Due today** scores 95, creating immediate priority
- **Due within 1 week** follows exponential decay: `90 - (days * 4)`, dropping from 90 to 62
- **Due within 2 weeks** uses linear decay at 2 points per day
- **Future tasks** (30+ days) receive minimal urgency (10-40 points)

This non-linear approach reflects human psychology: the difference between "due today" and "due in 2 days" feels more significant than "due in 20 days" versus "due in 22 days."

**2. Importance Scoring (0-100)**

User-provided importance ratings (1-10) are linearly scaled to 0-100. This straightforward conversion preserves user intent without algorithmic bias.

**3. Effort Scoring (0-100)**

The effort component uses logarithmic scaling to identify "quick wins":

- Tasks under 1 hour score 90-100
- The formula `100 - (log₁₀(hours + 1) * 35)` creates diminishing returns for longer tasks
- A 1-hour task scores 90, while a 20-hour task scores ~53

Logarithmic scaling prevents massive tasks from dominating the algorithm while still rewarding efficiency.

**4. Dependency Scoring (0-100)**

This component analyzes the task dependency graph:

- Base score: 50
- **Blocking factor**: +10 points per task this one blocks (capped at +50)
- **Dependency penalty**: -20 points if this task depends on incomplete tasks

Tasks on the critical path (blocking multiple others) receive priority, while blocked tasks are deprioritized until dependencies clear.

### Weighted Combination

The algorithm supports four strategies with different weight distributions:

- **Smart Balance**: 35% urgency, 30% importance, 15% effort, 20% dependencies
- **Fastest Wins**: 20% urgency, 20% importance, 50% effort, 10% dependencies
- **High Impact**: 15% urgency, 60% importance, 10% effort, 15% dependencies
- **Deadline Driven**: 60% urgency, 20% importance, 5% effort, 15% dependencies

Final score: `(urgency × w₁) + (importance × w₂) + (effort × w₃) + (dependencies × w₄)`

### Circular Dependency Detection

Before scoring, the algorithm performs depth-first search (DFS) on the dependency graph to detect cycles. If circular dependencies exist, the analysis fails with an error message identifying the cycle.

---

## 🎯 Design Decisions

### 1. **Why POST for both endpoints?**
**Decision**: Used POST for both `/analyze/` and `/suggest/` endpoints

**Reasoning**: While `/suggest/` conceptually "gets" data, it requires complex task data in the request body. REST conventions suggest POST for operations with substantial payloads. GET requests with bodies are not semantically clean and face browser/proxy limitations.

**Trade-off**: Less RESTful purity, but better practicality and API usability.

### 2. **Stateless API Design**
**Decision**: No database persistence; API processes tasks in-memory

**Reasoning**: The assignment focuses on algorithm design, not CRUD operations. Stateless design simplifies testing and allows frontend flexibility. Users can manage task storage client-side or via external systems.

**Trade-off**: No task history or user accounts, but faster development and easier testing.

### 3. **Non-linear Urgency Scoring**
**Decision**: Exponential decay for near-term urgency rather than linear

**Reasoning**: Psychological research shows humans perceive time non-linearly. The urgency difference between "today" and "tomorrow" feels greater than "day 20" versus "day 21." Exponential decay models this accurately.

**Trade-off**: More complex calculation, but significantly more intuitive results.

### 4. **Logarithmic Effort Scaling**
**Decision**: `log₁₀` instead of linear or inverse scoring

**Reasoning**: Linear inverse (`100 / hours`) creates extreme differences between small tasks. A 0.5-hour task would score 200 while a 2-hour task scores 50—too dramatic. Logarithmic scaling compresses the range while still rewarding quick wins.

**Trade-off**: Requires `math` library and is less intuitive to explain, but produces balanced scores.

### 5. **Four Strategy Presets vs. Custom Weights**
**Decision**: Predefined strategies instead of sliders for each weight

**Reasoning**: Four named strategies (Smart Balance, Fastest Wins, etc.) are easier for users to understand than abstract weight sliders. Presets prevent invalid configurations (weights not summing to 1.0) and provide opinionated guidance.

**Trade-off**: Less flexibility, but better UX and fewer edge cases.

### 6. **Decimal Hours Support**
**Decision**: Float field allowing 0.1+ hours instead of integer-only

**Reasoning**: Real tasks often take 30 minutes (0.5h) or 90 minutes (1.5h). The assignment emphasizes "quick wins," which requires sub-hour granularity. Industry tools (Jira, Asana) use decimals.

**Trade-off**: Slightly more complex input, but significantly more realistic.

### 7. **Frontend: Vanilla JavaScript**
**Decision**: No React/Vue/Angular framework

**Reasoning**: The assignment evaluates backend algorithm design primarily. Vanilla JS keeps the frontend simple, reduces setup complexity, and demonstrates fundamental JavaScript skills without framework magic.

**Trade-off**: More verbose code and manual DOM manipulation, but zero build tooling required.

### 8. **Score Transparency**
**Decision**: Return full breakdown of urgency/importance/effort/dependency scores

**Reasoning**: Users need to understand *why* a task scored highly. Transparency builds trust and allows users to adjust their strategy if results feel wrong. This is critical for an "intelligent" system.

**Trade-off**: Larger API response payload, but essential for usability.

---

## ⏱️ Time Breakdown

| Section | Estimated Time | Notes |
|---------|---------------|-------|
| **Backend - Models & Serializers** | 20 min | Basic Django setup, validation logic |
| **Backend - Core Algorithm** | 90 min | Mathematical functions, dependency detection, strategy patterns |
| **Backend - API Views** | 25 min | Endpoint logic, error handling |
| **Backend - Testing** | 35 min | 15+ unit tests covering edge cases |
| **Frontend - UI Structure** | 30 min | HTML layout, CSS styling |
| **Frontend - Form Logic** | 25 min | Manual entry, bulk JSON, validation |
| **Frontend - API Integration** | 20 min | Fetch calls, response handling |
| **Frontend - Results Display** | 20 min | Task cards, score visualization |
| **Documentation** | 25 min | README, code comments |
| **Testing & Refinement** | 20 min | End-to-end testing, bug fixes |
| **Total** | **~5 hours** | Includes breaks and debugging |

*Note: Assignment estimated 3.5 hours total (2h backend + 1.5h frontend). Actual time reflects comprehensive testing, documentation, and polish.*

---

## 🚀 Future Improvements

### High Priority (< 2 hours each)

1. **Date Intelligence**
   - Skip weekends when calculating urgency
   - Support custom business hours (e.g., 9-5 workdays)
   - Integrate holiday calendars
   - **Impact**: More realistic deadlines for business contexts

2. **Eisenhower Matrix Visualization**
   - 2D scatter plot: Urgency (Y-axis) vs. Importance (X-axis)
   - Quadrant labels: "Do First," "Schedule," "Delegate," "Eliminate"
   - Interactive task repositioning
   - **Impact**: Visual alternative to linear ranking

3. **Dependency Graph Visualization**
   - Use D3.js or Cytoscape.js for network graph
   - Highlight critical path in color
   - Show circular dependencies visually
   - **Impact**: Better understanding of task relationships

4. **Advanced Validation**
   - Warn if dependency IDs don't exist in task list
   - Suggest breaking tasks >40 hours into subtasks
   - Flag if all tasks are importance 10 (poor prioritization)
   - **Impact**: Better data quality and user guidance

### Medium Priority (2-5 hours each)

5. **Machine Learning Adaptation**
   - Track which suggested tasks users actually complete
   - Adjust weight preferences based on completion patterns
   - Use scikit-learn for simple supervised learning
   - **Impact**: Personalized algorithm over time

6. **Database Persistence**
   - Full Django ORM integration
   - User authentication (JWT tokens)
   - Task history and analytics
   - **Impact**: Production-ready application

7. **Collaboration Features**
   - Multi-user task assignment
   - Shared team workspaces
   - Real-time updates via WebSockets
   - **Impact**: Team productivity tool

8. **Export & Reporting**
   - Export to CSV, JSON, or PDF
   - Weekly productivity reports
   - Gantt chart view of scheduled tasks
   - **Impact**: Integration with existing workflows

### Advanced Features (5+ hours each)

9. **Smart Scheduling**
   - Auto-schedule tasks into calendar slots
   - Consider available work hours and task effort
   - Suggest optimal task ordering for the day/week
   - **Impact**: Move from prioritization to execution planning

10. **Natural Language Input**
    - Parse task descriptions: "Review PR tomorrow, should take an hour, high priority"
    - Extract due dates, effort, and importance automatically
    - Use NLP libraries (spaCy) or LLM APIs
    - **Impact**: Faster task entry

11. **Mobile App**
    - React Native or Flutter mobile app
    - Push notifications for urgent tasks
    - Offline-first architecture
    - **Impact**: Accessibility and real-time reminders

12. **Integration Ecosystem**
    - Sync with Google Calendar, Outlook
    - Import from Jira, Asana, Trello
    - Zapier/webhook support
    - **Impact**: Fits into existing tool stack

### Technical Debt & Polish

- Add rate limiting and caching
- Implement comprehensive API documentation (Swagger/OpenAPI)
- Add type hints throughout Python codebase
- Migrate frontend to TypeScript + React
- Set up CI/CD pipeline with GitHub Actions
- Add performance monitoring (Sentry, DataDog)
- Implement comprehensive accessibility (WCAG 2.1 AA)

---