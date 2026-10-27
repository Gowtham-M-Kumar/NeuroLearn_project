# Django Template Integration Examples

## Overview
This document shows how to display learning progress data in Django templates for teacher and child dashboards.

---

## Child Dashboard Integration

### 1. Update View

**File**: `apps/learning/views.py`

```python
from .models import LearningProgress

@login_required
def learning_dashboard(request):
    """
    Child dashboard showing their own progress.
    """
    # Get progress for current child
    alphabet_progress = LearningProgress.objects.filter(
        user=request.user,
        module='alphabet'
    ).order_by('item')
    
    # Calculate stats
    total_letters = 26
    completed_count = alphabet_progress.filter(completed=True).count()
    completion_percentage = round((completed_count / total_letters) * 100)
    
    # Get list of completed letter items
    completed_letters = list(
        alphabet_progress.filter(completed=True).values_list('item', flat=True)
    )
    
    context = {
        'alphabet_progress': alphabet_progress,
        'completed_count': completed_count,
        'total_letters': total_letters,
        'completion_percentage': completion_percentage,
        'completed_letters': completed_letters,
    }
    
    return render(request, 'learning/dashboard.html', context)
```

### 2. Update Template

**File**: `templates/learning/dashboard.html`

```html
{% extends 'base.html' %}

{% block content %}
<div class="learning-dashboard">
    <h1>My Learning Progress</h1>
    
    <!-- Progress Overview -->
    <div class="progress-overview">
        <h2>Alphabet Progress</h2>
        <div class="progress-bar-container">
            <div class="progress-bar" style="width: {{ completion_percentage }}%;">
                {{ completion_percentage }}%
            </div>
        </div>
        <p>{{ completed_count }} of {{ total_letters }} letters completed!</p>
    </div>
    
    <!-- Letter Grid -->
    <div class="letter-grid">
        {% for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' %}
            <div class="letter-card {% if letter in completed_letters %}completed{% endif %}">
                <span class="letter">{{ letter }}</span>
                {% if letter in completed_letters %}
                    <span class="checkmark">✓</span>
                {% else %}
                    <span class="lock">🔒</span>
                {% endif %}
            </div>
        {% endfor %}
    </div>
    
    <!-- Recent Activity -->
    <div class="recent-activity">
        <h3>Recently Completed</h3>
        <ul>
            {% for progress in alphabet_progress|slice:":5" %}
                <li>
                    Letter <strong>{{ progress.item }}</strong> 
                    - {{ progress.completed_at|date:"M d, Y" }}
                </li>
            {% empty %}
                <li>No progress yet. Start learning!</li>
            {% endfor %}
        </ul>
    </div>
    
    <!-- React App Embed (if applicable) -->
    <div id="react-alphabet-app"></div>
    <script src="{% static 'js/alphabet-learning-app.js' %}"></script>
</div>
{% endblock %}
```

### 3. Add CSS Styling

```css
.progress-bar-container {
    width: 100%;
    height: 30px;
    background: #e0e0e0;
    border-radius: 15px;
    overflow: hidden;
}

.progress-bar {
    height: 100%;
    background: linear-gradient(90deg, #4CAF50, #8BC34A);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: bold;
    transition: width 0.3s ease;
}

.letter-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(60px, 1fr));
    gap: 10px;
    margin: 20px 0;
}

.letter-card {
    aspect-ratio: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    border: 2px solid #ddd;
    border-radius: 8px;
    background: white;
    cursor: pointer;
    transition: all 0.2s;
}

.letter-card.completed {
    background: #4CAF50;
    color: white;
    border-color: #4CAF50;
}

.letter-card .checkmark {
    font-size: 20px;
}
```

---

## Teacher Dashboard Integration

### 1. Create Teacher View

**File**: `apps/learning/views.py`

```python
from django.contrib.auth import get_user_model
from django.db.models import Count, Q

User = get_user_model()

@login_required
def teacher_dashboard(request):
    """
    Teacher dashboard showing progress for all students.
    """
    # Ensure user is a teacher (adjust based on your user model)
    # if not request.user.is_teacher:
    #     return redirect('learning:learning_dashboard')
    
    # Get all children/students
    children = User.objects.filter(
        # Add your filter for child users
        # e.g., role='child' or is_child=True
    )
    
    # Get progress stats for each child
    child_progress_data = []
    for child in children:
        alphabet_progress = LearningProgress.objects.filter(
            user=child,
            module='alphabet',
            completed=True
        )
        
        child_progress_data.append({
            'child': child,
            'completed_count': alphabet_progress.count(),
            'completion_percentage': round((alphabet_progress.count() / 26) * 100),
            'recent_items': alphabet_progress.order_by('-completed_at')[:3],
        })
    
    # Overall stats
    total_completions = LearningProgress.objects.filter(
        module='alphabet',
        completed=True
    ).count()
    
    context = {
        'child_progress_data': child_progress_data,
        'total_completions': total_completions,
        'total_children': children.count(),
    }
    
    return render(request, 'learning/teacher_dashboard.html', context)
```

### 2. Create Teacher Template

**File**: `templates/learning/teacher_dashboard.html`

```html
{% extends 'base.html' %}

{% block content %}
<div class="teacher-dashboard">
    <h1>Teacher Dashboard - Learning Progress</h1>
    
    <!-- Overview Stats -->
    <div class="stats-cards">
        <div class="stat-card">
            <h3>Total Students</h3>
            <p class="stat-number">{{ total_children }}</p>
        </div>
        <div class="stat-card">
            <h3>Total Completions</h3>
            <p class="stat-number">{{ total_completions }}</p>
        </div>
        <div class="stat-card">
            <h3>Average Progress</h3>
            <p class="stat-number">
                {% widthratio total_completions total_children|default:1 26 %}%
            </p>
        </div>
    </div>
    
    <!-- Student Progress Table -->
    <div class="student-progress-table">
        <h2>Student Progress</h2>
        <table>
            <thead>
                <tr>
                    <th>Student Name</th>
                    <th>Progress</th>
                    <th>Completed</th>
                    <th>Recent Activity</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                {% for data in child_progress_data %}
                <tr>
                    <td>{{ data.child.get_full_name|default:data.child.username }}</td>
                    <td>
                        <div class="progress-bar-small">
                            <div class="progress-fill" 
                                 style="width: {{ data.completion_percentage }}%;">
                            </div>
                        </div>
                        {{ data.completion_percentage }}%
                    </td>
                    <td>{{ data.completed_count }} / 26</td>
                    <td>
                        {% for item in data.recent_items %}
                            <span class="badge">{{ item.item }}</span>
                        {% empty %}
                            <em>No activity</em>
                        {% endfor %}
                    </td>
                    <td>
                        <a href="{% url 'learning:child_detail' data.child.id %}" 
                           class="btn btn-sm">View Details</a>
                    </td>
                </tr>
                {% empty %}
                <tr>
                    <td colspan="5">No students found.</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    
    <!-- Module Filter -->
    <div class="module-filter">
        <h3>View by Module</h3>
        <div class="filter-buttons">
            <button class="filter-btn active" data-module="alphabet">Alphabet</button>
            <button class="filter-btn" data-module="numbers">Numbers</button>
            <button class="filter-btn" data-module="words">Words</button>
        </div>
    </div>
</div>

<script>
// Optional: Add filtering via AJAX
document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        const module = this.dataset.module;
        // Fetch filtered data via API or reload page with query param
        window.location.href = `?module=${module}`;
    });
});
</script>
{% endblock %}
```

---

## API-Based Dashboard (Dynamic)

If you want to use JavaScript/React for the dashboard instead of Django templates:

### JavaScript Example

```javascript
// Fetch progress data and render dynamically
async function loadDashboard() {
    try {
        const response = await fetch('/learning/api/progress/?module=alphabet', {
            credentials: 'include'
        });
        
        const data = await response.json();
        
        // Calculate stats
        const completedCount = data.count;
        const totalLetters = 26;
        const percentage = Math.round((completedCount / totalLetters) * 100);
        
        // Update UI
        document.getElementById('progress-bar').style.width = `${percentage}%`;
        document.getElementById('completed-count').textContent = 
            `${completedCount} / ${totalLetters}`;
        
        // Render letter grid
        const grid = document.getElementById('letter-grid');
        const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('');
        const completedItems = data.results.map(r => r.item);
        
        grid.innerHTML = alphabet.map(letter => `
            <div class="letter-card ${completedItems.includes(letter) ? 'completed' : ''}">
                <span>${letter}</span>
                ${completedItems.includes(letter) ? '<span>✓</span>' : ''}
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Failed to load dashboard:', error);
    }
}

// Load on page ready
document.addEventListener('DOMContentLoaded', loadDashboard);
```

---

## Django ORM Query Examples

### Common Queries for Progress Data

```python
from django.db.models import Count, Q
from apps.learning.models import LearningProgress

# 1. Get all completed letters for a user
completed_letters = LearningProgress.objects.filter(
    user=request.user,
    module='alphabet',
    completed=True
).values_list('item', flat=True)

# 2. Get completion count per module
module_stats = LearningProgress.objects.filter(
    user=request.user
).values('module').annotate(
    completed_count=Count('id')
)

# 3. Get most recent completions
recent = LearningProgress.objects.filter(
    user=request.user
).order_by('-completed_at')[:10]

# 4. Get users who completed a specific letter
users_completed_a = LearningProgress.objects.filter(
    module='alphabet',
    item='A',
    completed=True
).select_related('user')

# 5. Check if user completed all letters
from django.db.models import Count

all_completed = LearningProgress.objects.filter(
    user=request.user,
    module='alphabet',
    completed=True
).count() == 26

# 6. Get completion dates for chart/timeline
timeline = LearningProgress.objects.filter(
    user=request.user,
    module='alphabet'
).values('completed_at__date').annotate(
    daily_count=Count('id')
).order_by('completed_at__date')
```

---

## Summary

### For Child Dashboard:
- Show personal progress with visual indicators
- Display completed vs. incomplete items
- Show recent activity/achievements
- Embed React app for interactive learning

### For Teacher Dashboard:
- Show all students' progress in a table
- Display aggregate statistics
- Filter by module (alphabet, numbers, etc.)
- Link to detailed student views

### API Integration:
- Use Django templates with context data OR
- Use React/JavaScript to fetch from API endpoints
- Both approaches work; choose based on your app architecture
