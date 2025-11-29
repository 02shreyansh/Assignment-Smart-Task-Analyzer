let tasks = [];
let nextId = 1;
let currentStrategy = 'smart_balance';
const API_BASE_URL = 'http://localhost:8000/api/tasks';

document.addEventListener('DOMContentLoaded', () => {
    setTodayAsDefault();
    setupStrategySelector();
    setupFormSubmit();
});

function setTodayAsDefault() {
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('task-due-date').value = today;
}

function setupStrategySelector() {
    document.querySelectorAll('.strategy-option').forEach(option => {
        option.addEventListener('click', () => {
            document.querySelectorAll('.strategy-option').forEach(o => o.classList.remove('active'));
            option.classList.add('active');
            currentStrategy = option.dataset.strategy;
        });
    });
}

function setupFormSubmit() {
    document.getElementById('task-form').addEventListener('submit', (e) => {
        e.preventDefault();
        addTask();
    });
}

function switchTab(tab) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    
    if (tab === 'manual') {
        document.querySelector('.tab:nth-child(1)').classList.add('active');
        document.getElementById('manual-tab').classList.add('active');
    } else {
        document.querySelector('.tab:nth-child(2)').classList.add('active');
        document.getElementById('bulk-tab').classList.add('active');
    }
}

function addTask() {
    const title = document.getElementById('task-title').value;
    const dueDate = document.getElementById('task-due-date').value;
    const hours = parseFloat(document.getElementById('task-hours').value);
    const importance = parseInt(document.getElementById('task-importance').value);
    const depsInput = document.getElementById('task-dependencies').value;
    if (!title || !dueDate || !hours || !importance) {
        showError('Please fill all required fields');
        return;
    }

    if (importance < 1 || importance > 10) {
        showError('Importance must be between 1 and 10');
        return;
    }

    if (hours < 0.1) {
        showError('Estimated hours must be at least 0.1');
        return;
    }
    const dependencies = depsInput
        ? depsInput.split(',').map(d => parseInt(d.trim())).filter(d => !isNaN(d))
        : [];
    const task = {
        id: nextId++,
        title,
        due_date: dueDate,
        estimated_hours: hours,
        importance,
        dependencies
    };

    tasks.push(task);
    updateTaskList();
    document.getElementById('task-form').reset();
    setTodayAsDefault();
}

function loadBulkTasks() {
    const jsonInput = document.getElementById('bulk-json').value;
    
    try {
        const parsedTasks = JSON.parse(jsonInput);
        
        if (!Array.isArray(parsedTasks)) {
            showError('Input must be an array of tasks');
            return;
        }
        for (const task of parsedTasks) {
            if (!task.title || !task.due_date || !task.estimated_hours || !task.importance) {
                showError('Each task must have: title, due_date, estimated_hours, importance');
                return;
            }
        }

        tasks = parsedTasks.map(task => ({
            ...task,
            id: task.id || nextId++,
            dependencies: task.dependencies || []
        }));

        nextId = Math.max(...tasks.map(t => t.id), 0) + 1;
        
        updateTaskList();
        switchTab('manual');
        showSuccess(`Loaded ${tasks.length} tasks successfully!`);
    } catch (e) {
        showError('Invalid JSON format: ' + e.message);
    }
}

function updateTaskList() {
    const container = document.getElementById('task-list');
    
    if (tasks.length === 0) {
        container.innerHTML = '<p style="color: #999; text-align: center; padding: 20px;">No tasks added yet</p>';
        return;
    }

    container.innerHTML = `
        <div style="background: #f8f9fa; padding: 10px; border-radius: 6px; margin-bottom: 10px;">
            <strong>${tasks.length} task(s) added</strong>
        </div>
        ${tasks.map(task => `
            <div style="background: white; padding: 10px; border-radius: 4px; margin-bottom: 5px; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong>${task.title}</strong><br>
                    <small style="color: #666;">Due: ${task.due_date} | ${task.estimated_hours}h | Importance: ${task.importance}</small>
                </div>
                <button onclick="removeTask(${task.id})" style="background: #dc3545; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer;">✕</button>
            </div>
        `).join('')}
    `;
}

function removeTask(id) {
    tasks = tasks.filter(t => t.id !== id);
    updateTaskList();
}

function clearTaskList() {
    if (confirm('Are you sure you want to clear all tasks?')) {
        tasks = [];
        nextId = 1;
        updateTaskList();
    }
}

async function analyzeTasks() {
    if (tasks.length === 0) {
        showError('Please add at least one task');
        return;
    }

    const resultsContainer = document.getElementById('results-container');
    resultsContainer.innerHTML = '<div class="loading"><div class="loading-spinner"></div><p>Analyzing tasks...</p></div>';
    
    document.getElementById('analyze-btn').disabled = true;

    try {
        const response = await fetch(`${API_BASE_URL}/tasks/analyze/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                tasks: tasks,
                strategy: currentStrategy
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.details || data.error || 'Analysis failed');
        }

        displayResults(data);
    } catch (error) {
        resultsContainer.innerHTML = `<div class="error-message">${error.message}</div>`;
    } finally {
        document.getElementById('analyze-btn').disabled = false;
    }
}

async function getSuggestions() {
    if (tasks.length === 0) {
        showError('Please add at least one task');
        return;
    }

    const resultsContainer = document.getElementById('results-container');
    resultsContainer.innerHTML = '<div class="loading"><div class="loading-spinner"></div><p>Getting suggestions...</p></div>';
    
    document.getElementById('suggest-btn').disabled = true;

    try {
        const response = await fetch(`${API_BASE_URL}/tasks/suggest/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                tasks: tasks,
                strategy: currentStrategy
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.details || data.error || 'Suggestion failed');
        }

        displaySuggestions(data);
    } catch (error) {
        resultsContainer.innerHTML = `<div class="error-message">${error.message}</div>`;
    } finally {
        document.getElementById('suggest-btn').disabled = false;
    }
}

function displayResults(data) {
    const container = document.getElementById('results-container');
    const tasks = data.tasks;

    container.innerHTML = `
        <div class="success-message">
            Analyzed ${data.total_tasks} tasks using <strong>${formatStrategy(data.strategy)}</strong> strategy
        </div>
        ${tasks.map((task, index) => `
            <div class="task-card ${task.priority_level.toLowerCase()}">
                <div class="task-header">
                    <div>
                        <div class="task-title">${index + 1}. ${task.title}</div>
                        <span class="priority-badge ${task.priority_level.toLowerCase()}">${task.priority_level}</span>
                    </div>
                    <div class="task-score">${task.priority_score}</div>
                </div>
                
                <div class="task-details">
                    <div class="task-detail"><strong>Due:</strong> ${task.due_date}</div>
                    <div class="task-detail"><strong>Hours:</strong> ${task.estimated_hours}</div>
                    <div class="task-detail"><strong>Importance:</strong> ${task.importance}/10</div>
                    <div class="task-detail"><strong>Dependencies:</strong> ${task.dependencies.length > 0 ? task.dependencies.join(', ') : 'None'}</div>
                </div>

                <div class="task-breakdown">
                    <div class="breakdown-item">
                        <div class="breakdown-label">Urgency</div>
                        <div class="breakdown-value">${task.score_breakdown.urgency}</div>
                    </div>
                    <div class="breakdown-item">
                        <div class="breakdown-label">Importance</div>
                        <div class="breakdown-value">${task.score_breakdown.importance}</div>
                    </div>
                    <div class="breakdown-item">
                        <div class="breakdown-label">Effort</div>
                        <div class="breakdown-value">${task.score_breakdown.effort}</div>
                    </div>
                    <div class="breakdown-item">
                        <div class="breakdown-label">Dependencies</div>
                        <div class="breakdown-value">${task.score_breakdown.dependencies}</div>
                    </div>
                </div>
            </div>
        `).join('')}
    `;

    document.getElementById('suggestions-panel').style.display = 'none';
}

function displaySuggestions(data) {
    const container = document.getElementById('results-container');
    const suggestionsPanel = document.getElementById('suggestions-panel');

    container.innerHTML = `
        <div class="success-message">
            Top 3 recommended tasks for today
        </div>
    `;

    suggestionsPanel.innerHTML = `
        <div class="suggestion-panel">
            <h3>${data.message}</h3>
            ${data.suggested_tasks.map((task, index) => `
                <div class="suggestion-card">
                    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 10px;">
                        <div>
                            <div style="font-size: 1.2rem; font-weight: 600; margin-bottom: 5px;">
                                ${index + 1}. ${task.title}
                            </div>
                            <div style="font-size: 0.9rem; opacity: 0.9;">
                                Due: ${task.due_date} | ${task.estimated_hours}h | Importance: ${task.importance}/10
                            </div>
                        </div>
                        <div style="font-size: 1.5rem; font-weight: 700; background: rgba(255,255,255,0.2); padding: 8px 15px; border-radius: 6px;">
                            ${task.priority_score}
                        </div>
                    </div>
                    <div class="suggestion-reason">${task.reason}</div>
                </div>
            `).join('')}
        </div>
    `;

    suggestionsPanel.style.display = 'block';
}

function formatStrategy(strategy) {
    const map = {
        'smart_balance': 'Smart Balance',
        'fastest_wins': 'Fastest Wins',
        'high_impact': 'High Impact',
        'deadline_driven': 'Deadline Driven'
    };
    return map[strategy] || strategy;
}

function showError(message) {
    const container = document.getElementById('results-container');
    container.innerHTML = `<div class="error-message">${message}</div>`;
}

function showSuccess(message) {
    const container = document.getElementById('results-container');
    container.innerHTML = `<div class="success-message">${message}</div>`;
}