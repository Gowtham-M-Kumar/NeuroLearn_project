# Django + React Alphabet Learning Integration Guide

## Overview

This guide explains how the React-based Alphabet Learning app integrates with the Django backend to track and store learning progress per child.

## Architecture

- **Backend**: Django with Django REST Framework (DRF)
- **Frontend**: React app (from Figma design)
- **Authentication**: Django session authentication (cookies)
- **Data Flow**: React → Django API → Database → Dashboard display

---

## Backend Implementation

### 1. Database Model

**File**: `apps/learning/models.py`

```python
class LearningProgress(models.Model):
    """
    Generic progress tracker for any learning module.
    Stores completion status per user, module, and item.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    module = models.CharField(max_length=50)  # e.g., "alphabet", "numbers"
    item = models.CharField(max_length=50)    # e.g., "A", "B", "1", "2"
    completed = models.BooleanField(default=True)
    completed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'module', 'item')  # Prevents duplicates
```

**Key Features**:
- Prevents duplicate completions with `unique_together`
- Scoped to individual users
- Supports multiple learning modules
- Auto-timestamps completion

### 2. API Serializers

**File**: `apps/learning/serializers.py`

Two serializers handle the data:

1. **LearningProgressSerializer**: Full model serialization
2. **ProgressCompleteSerializer**: Input validation for POST requests

### 3. API Endpoints

**File**: `apps/learning/views.py`

#### POST `/learning/api/complete/`
Marks an item as completed for the logged-in user.

**Request**:
```json
{
  "module": "alphabet",
  "item": "A",
  "completed": true
}
```

**Response (201 Created or 200 OK)**:
```json
{
  "message": "Progress saved successfully",
  "created": true,
  "data": {
    "id": 1,
    "module": "alphabet",
    "item": "A",
    "completed": true,
    "completed_at": "2026-01-06T12:00:00Z"
  }
}
```

**Features**:
- Uses `get_or_create()` to prevent duplicates
- Returns 201 for new items, 200 for existing
- Validates input data
- Requires authentication

#### GET `/learning/api/progress/`
Retrieves all progress for the logged-in user.

**Optional Query Parameter**: `?module=alphabet`

**Response**:
```json
{
  "count": 5,
  "results": [
    {
      "id": 1,
      "module": "alphabet",
      "item": "A",
      "completed": true,
      "completed_at": "2026-01-06T12:00:00Z"
    }
  ]
}
```

### 4. URL Configuration

**File**: `apps/learning/urls.py`

```python
urlpatterns = [
    # ... existing paths ...
    path('api/complete/', views.mark_item_complete, name='api_mark_complete'),
    path('api/progress/', views.get_user_progress, name='api_get_progress'),
]
```

**Full URLs**:
- `POST /learning/api/complete/`
- `GET /learning/api/progress/`

---

## Frontend Implementation (React)

### API Integration Functions

**File**: `docs/react_api_integration.js`

#### 1. Mark Letter as Complete

```javascript
import { markLetterComplete } from './api';

// When child completes a letter
const handleLetterComplete = async (letter) => {
  try {
    await markLetterComplete(letter);
    console.log(`${letter} completed!`);
  } catch (error) {
    console.error('Failed to save:', error);
  }
};
```

#### 2. Fetch Progress on Load

```javascript
import { getUserProgress } from './api';

useEffect(() => {
  async function loadProgress() {
    try {
      const data = await getUserProgress('alphabet');
      setProgressData(data.results);
    } catch (error) {
      console.error('Failed to load progress:', error);
    }
  }
  loadProgress();
}, []);
```

#### 3. Check Completion Status

```javascript
import { isLetterCompleted } from './api';

const completed = isLetterCompleted(progressData, 'A');
// Use to lock/unlock UI elements
```

### Important: CSRF Token Handling

All POST requests **must** include Django's CSRF token:

```javascript
function getCsrfToken() {
  const name = 'csrftoken';
  const cookies = document.cookie.split(';');
  for (let cookie of cookies) {
    cookie = cookie.trim();
    if (cookie.startsWith(name + '=')) {
      return decodeURIComponent(cookie.substring(name.length + 1));
    }
  }
  return null;
}

// Include in POST headers
headers: {
  'X-CSRFToken': getCsrfToken(),
}
```

### Fetch Configuration

**Critical**: Always include credentials for session auth:

```javascript
fetch('/learning/api/progress/', {
  credentials: 'include',  // ← Required for Django cookies
  // ...
})
```

---

## Setup Instructions

### 1. Run Migrations

```bash
# Create migration files
python manage.py makemigrations learning

# Apply migrations to database
python manage.py migrate learning
```

### 2. Verify DRF Configuration

Ensure `settings.py` has:

```python
INSTALLED_APPS = [
    # ...
    'rest_framework',
    'apps.learning',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}
```

### 3. Test API Endpoints

```bash
# Start Django development server
python manage.py runserver

# Test in browser (must be logged in):
# GET: http://localhost:8000/learning/api/progress/
```

---

## Dashboard Integration

### Teacher Dashboard

Query progress for all students:

```python
from apps.learning.models import LearningProgress

# Get all alphabet progress
alphabet_progress = LearningProgress.objects.filter(
    module='alphabet'
).select_related('user')

# Group by user
from django.db.models import Count
user_stats = LearningProgress.objects.filter(
    module='alphabet'
).values('user__username').annotate(
    completed_count=Count('id')
)
```

### Child Dashboard

Progress is automatically scoped to `request.user` in API views, so children only see their own data.

---

## Security Considerations

✅ **Implemented**:
- Authentication required for all API endpoints
- Progress scoped to `request.user` (no data leakage)
- CSRF protection on POST requests
- Duplicate prevention with `unique_together`

❌ **Not Required** (per your specifications):
- JWT tokens (using session auth)
- Complex permission classes
- Rate limiting (add if needed)

---

## Testing Checklist

- [ ] Migrations applied successfully
- [ ] User can log in via Django
- [ ] GET `/learning/api/progress/` returns empty list for new users
- [ ] POST `/learning/api/complete/` saves progress
- [ ] Duplicate POST returns 200 (not 201)
- [ ] React app shows completed letters
- [ ] Progress persists across sessions
- [ ] Different users have separate progress

---

## Extending to Other Modules

To add progress tracking for numbers, words, etc.:

### Backend (No changes needed!)
The `LearningProgress` model is generic:

```python
# For numbers
await markItemComplete('numbers', '5')

# For words
await markItemComplete('words', 'cat')
```

### Frontend
Create module-specific helper functions:

```javascript
export async function markNumberComplete(number) {
  return markItemComplete('numbers', number.toString());
}

export async function markWordComplete(word) {
  return markItemComplete('words', word);
}
```

---

## Troubleshooting

### Issue: 403 Forbidden on POST
**Solution**: Ensure CSRF token is included in headers.

### Issue: 401 Unauthorized
**Solution**: User must be logged in. Check Django session cookie.

### Issue: Progress not showing
**Solution**: Check `credentials: 'include'` in fetch options.

### Issue: Duplicate entries
**Solution**: Already prevented by `unique_together` in model.

---

## File Summary

**Backend Files Created/Modified**:
- ✅ `apps/learning/models.py` - Added `LearningProgress` model
- ✅ `apps/learning/serializers.py` - Created (new file)
- ✅ `apps/learning/views.py` - Added 2 API views
- ✅ `apps/learning/urls.py` - Added API routes
- ✅ `apps/learning/migrations/0002_learningprogress.py` - Migration file

**Frontend Files**:
- ✅ `docs/react_api_integration.js` - API utilities and examples

**Documentation**:
- ✅ `docs/INTEGRATION_GUIDE.md` - This file

---

## Next Steps

1. **Apply migrations**: `python manage.py migrate`
2. **Test endpoints**: Use browser or Postman
3. **Integrate React app**: Copy functions from `react_api_integration.js`
4. **Update dashboards**: Display progress data in teacher/child views
5. **Add analytics**: Track completion rates, time spent, etc.

---

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review `docs/react_api_integration.js` for examples
3. Examine `apps/learning/views.py` for API logic
4. Test endpoints with Django admin or browser dev tools
