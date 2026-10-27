from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import UpdateView
from django.urls import reverse_lazy
from django.db.models import Sum, Avg, Count, F, Q, Max
from django.utils import timezone
from datetime import timedelta
from .forms import (
    CustomUserCreationForm, CustomAuthenticationForm,
    TeacherProfileForm, ChildProfileForm, UserProfileForm
)
from .models import CustomUser, TeacherProfile, ChildProfile


def login_view(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('users:dashboard')
    
    # We need both forms for the sliding UI
    login_form = None
    register_form = CustomUserCreationForm()

    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.get_full_name()}!')
                return redirect('users:dashboard')
            else:
                messages.error(request, 'Invalid email or password.')
        login_form = form
    else:
        login_form = CustomAuthenticationForm()
    
    return render(request, 'users/login.html', {
        'form': login_form, # keep for compatibility
        'login_form': login_form,
        'register_form': register_form,
        'is_register': False
    })


def logout_view(request):
    """User logout view"""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('users:login')


def register_view(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('users:dashboard')
    
    # We need both forms for the sliding UI
    register_form = None
    login_form = CustomAuthenticationForm()

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.email  # Set username to email
            user.save()
            
            # Create appropriate profile based on role
            if user.role == CustomUser.UserRole.TEACHER:
                TeacherProfile.objects.create(user=user)
            else:  # CHILD role
                ChildProfile.objects.create(user=user, age=5)  # Default age
            
            # Log the user in
            login(request, user)
            role_name = user.get_role_display()
            messages.success(request, f'Account created successfully as {role_name}! Welcome, {user.get_full_name() or user.email}.')
            return redirect('users:dashboard')
        else:
            # Show form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
        register_form = form
    else:
        register_form = CustomUserCreationForm()
    
    return render(request, 'users/register.html', {
        'form': register_form, # keep for compatibility
        'register_form': register_form,
        'login_form': login_form,
        'is_register': True
    })


@login_required
def dashboard_view(request):
    """Dashboard view with analytics for teachers and overview for children"""
    user = request.user
    
    context = {
        'user': user,
    }
    
    # Add role-specific context
    if user.role == CustomUser.UserRole.TEACHER:
        try:
            from apps.games.models import GameSession, GameProgress
            from apps.learning.models import ChildLetterProgress, ChildNumberProgress, ChildWordProgress, ChildEmotionProgress, Letter, Number, Word, Emotion
            from apps.drawing.models import Drawing, DrawingSession

            teacher_profile = user.teacher_profile
            assigned_children = teacher_profile.assigned_children.all()
            
            # Fallback to all children if none assigned to this specific teacher
            if not assigned_children.exists():
                assigned_children = ChildProfile.objects.all()
                
            assigned_user_ids = assigned_children.values_list('user_id', flat=True)
            
            # --- A) KPI SUMMARY CARDS ---
            total_students = assigned_children.count()
            
            # Activities Completed
            game_completed = GameSession.objects.filter(child_id__in=assigned_user_ids, completed=True).count()
            learning_completed = (
                ChildLetterProgress.objects.filter(child_id__in=assigned_user_ids, completed=True).count() +
                ChildNumberProgress.objects.filter(child_id__in=assigned_user_ids, completed=True).count() +
                ChildWordProgress.objects.filter(child_id__in=assigned_user_ids, completed=True).count() +
                ChildEmotionProgress.objects.filter(child_id__in=assigned_user_ids, completed=True).count()
            )
            drawing_completed = Drawing.objects.filter(child_id__in=assigned_user_ids).count()
            total_activities = game_completed + learning_completed + drawing_completed
            
            # Average Success Rate (Game accuracy as proxy)
            avg_accuracy = GameProgress.objects.filter(child_id__in=assigned_user_ids).aggregate(Avg('average_accuracy'))['average_accuracy__avg'] or 0.0
            
            # Average Engagement Time
            game_time = GameSession.objects.filter(child_id__in=assigned_user_ids).aggregate(Avg('time_taken'))['time_taken__avg'] or 0
            drawing_time = DrawingSession.objects.filter(child_id__in=assigned_user_ids).aggregate(Avg('duration_seconds'))['duration_seconds__avg'] or 0
            avg_engagement = (game_time + drawing_time) / 2 if (game_time and drawing_time) else (game_time or drawing_time or 0)
            
            # --- B) ACTIVITY OVERVIEW SECTION ---
            # Basic stats for categories
            # Learning
            total_learning_items = Letter.objects.count() + Number.objects.count() + Word.objects.count() + Emotion.objects.filter(is_active=True).count()
            if total_learning_items == 0: total_learning_items = 26 + 21 + 50 + 8
            learning_success = (learning_completed / (total_learning_items * total_students)) * 100 if total_students and total_learning_items else 0
            
            # Games
            game_success = avg_accuracy
            
            # Drawing
            drawing_completion_rate = (drawing_completed / (total_students or 1)) * 5 # Mock engagement rate if we just want a number, or just show count
            # Actually let's just use the count of drawings as a percentage of "expected" or similar, or just show the % of students with at least one drawing.
            students_with_drawing = Drawing.objects.filter(child_id__in=assigned_user_ids).values('child_id').distinct().count()
            drawing_engagement = (students_with_drawing / total_students * 100) if total_students else 0
            
            # Needs attention if accuracy < 50%, inactive for 7+ days, or never logged in
            week_ago = timezone.now() - timedelta(days=7)
            needing_attention = assigned_children.filter(
                Q(user__game_progress__average_accuracy__lt=50) | 
                Q(user__last_login__lt=week_ago) |
                Q(user__last_login__isnull=True)
            ).distinct()[:10]  # Allow more than 5 since many might be new

            # --- D) RECENT ACTIVITY FEED (All modules) ---
            from apps.learning.models import ChildLetterProgress, ChildNumberProgress, ChildWordProgress, ChildEmotionProgress
            from apps.routines.models import TaskCompletion

            # Collect all recent activities across every module
            unified_feed = []

            # Games
            for gs in GameSession.objects.filter(child_id__in=assigned_user_ids).order_by('-started_at')[:10]:
                unified_feed.append({
                    'type': 'game',
                    'icon': 'sports_esports',
                    'color': '#f59e0b',
                    'label': 'Game',
                    'message': f'{gs.child.get_full_name()} played {gs.game.name} (Level {gs.level}, Score {gs.score})',
                    'timestamp': gs.started_at,
                    'child': gs.child,
                })

            # Drawings
            for dr in Drawing.objects.filter(child_id__in=assigned_user_ids).order_by('-updated_at')[:10]:
                unified_feed.append({
                    'type': 'drawing',
                    'icon': 'palette',
                    'color': '#10b981',
                    'label': 'Drawing',
                    'message': f'{dr.child.get_full_name()} saved drawing "{dr.title}"',
                    'timestamp': dr.updated_at,
                    'child': dr.child,
                })

            # Learning – Letters
            for lp in ChildLetterProgress.objects.filter(child_id__in=assigned_user_ids, completed=True).select_related('child', 'letter').order_by('-timestamp')[:10]:
                unified_feed.append({
                    'type': 'learning',
                    'icon': 'abc',
                    'color': '#8b5cf6',
                    'label': 'Learning',
                    'message': f'{lp.child.get_full_name()} mastered Letter {lp.letter.char}',
                    'timestamp': lp.timestamp,
                    'child': lp.child,
                })

            # Learning – Numbers
            for np in ChildNumberProgress.objects.filter(child_id__in=assigned_user_ids, completed=True).select_related('child', 'number').order_by('-timestamp')[:10]:
                unified_feed.append({
                    'type': 'learning',
                    'icon': '123',
                    'color': '#8b5cf6',
                    'label': 'Learning',
                    'message': f'{np.child.get_full_name()} completed Number {np.number.value}',
                    'timestamp': np.timestamp,
                    'child': np.child,
                })

            # Learning – Words
            for wp in ChildWordProgress.objects.filter(child_id__in=assigned_user_ids, completed=True).select_related('child', 'word').order_by('-timestamp')[:10]:
                unified_feed.append({
                    'type': 'learning',
                    'icon': 'spellcheck',
                    'color': '#8b5cf6',
                    'label': 'Learning',
                    'message': f'{wp.child.get_full_name()} learned the word "{wp.word.text}"',
                    'timestamp': wp.timestamp,
                    'child': wp.child,
                })

            # Learning – Emotions
            for ep in ChildEmotionProgress.objects.filter(child_id__in=assigned_user_ids, completed=True).select_related('child', 'emotion').order_by('-timestamp')[:10]:
                unified_feed.append({
                    'type': 'emotion',
                    'icon': 'mood',
                    'color': '#ec4899',
                    'label': 'Emotion',
                    'message': f'{ep.child.get_full_name()} learned the "{ep.emotion.name}" emotion',
                    'timestamp': ep.timestamp,
                    'child': ep.child,
                })

            # Routines – Task Completions
            for tc in TaskCompletion.objects.filter(child_id__in=assigned_user_ids).select_related('child', 'task__routine').order_by('-completed_at')[:10]:
                unified_feed.append({
                    'type': 'routine',
                    'icon': 'task_alt',
                    'color': '#06b6d4',
                    'label': 'Routine',
                    'message': f'{tc.child.get_full_name()} completed routine task "{tc.task.title}"',
                    'timestamp': tc.completed_at,
                    'child': tc.child,
                })

            # Sort by most recent and take top 15
            unified_feed.sort(key=lambda x: x['timestamp'], reverse=True)
            recent_activity_feed = unified_feed[:15]

            # Routine completions for KPIs
            routine_completed = TaskCompletion.objects.filter(child_id__in=assigned_user_ids).count()
            total_activities = game_completed + learning_completed + drawing_completed + routine_completed

            context.update({
                'profile': teacher_profile,
                'assigned_children': assigned_children,
                'kpis': {
                    'total_students': total_students,
                    'total_activities': total_activities,
                    'avg_accuracy': round(avg_accuracy, 1),
                    'avg_engagement': round(avg_engagement / 60, 1),  # minutes
                },
                'overview': {
                    'learning': round(learning_success, 1),
                    'games': round(game_success, 1),
                    'drawing': round(drawing_engagement, 1),
                },
                'needing_attention': needing_attention,
                'recent_activity_feed': recent_activity_feed,
                # Keep legacy vars for backward compat
                'recent_games': GameSession.objects.filter(child_id__in=assigned_user_ids).order_by('-started_at')[:5],
                'recent_drawings': Drawing.objects.filter(child_id__in=assigned_user_ids).order_by('-updated_at')[:5],
            })
        except TeacherProfile.DoesNotExist:
            pass
    
    elif user.role == CustomUser.UserRole.CHILD:
        try:
            child_profile = user.child_profile
            context['profile'] = child_profile
            
            # --- Dynamic Content Logic for Child Dashboard ---
            from apps.learning.models import ChildLetterProgress, ChildNumberProgress, ChildWordProgress, ChildEmotionProgress, Emotion
            from apps.games.models import GameSession
            
            latest_activities = []
            
            # Letters
            latest_letter = ChildLetterProgress.objects.filter(child=user).select_related('letter').order_by('-timestamp').first()
            total_letters = 26
            completed_letters = ChildLetterProgress.objects.filter(child=user, completed=True).count()
            letters_progress_pct = int((completed_letters / total_letters) * 100) if total_letters else 0
            
            if latest_letter:
                latest_activities.append({
                    'type': 'Learning / Letters',
                    'title': f'Alphabet Tracing: {latest_letter.letter.char}',
                    'timestamp': latest_letter.timestamp,
                    'url': f'/learning/alphabet/{latest_letter.letter.char.lower()}/',
                    'progress': letters_progress_pct
                })
                
            # Numbers
            latest_number = ChildNumberProgress.objects.filter(child=user).select_related('number').order_by('-timestamp').first()
            total_numbers = 21
            completed_numbers = ChildNumberProgress.objects.filter(child=user, completed=True).count()
            numbers_progress_pct = int((completed_numbers / total_numbers) * 100) if total_numbers else 0
            
            if latest_number:
                latest_activities.append({
                    'type': 'Learning / Numbers',
                    'title': f'Number Practice: {latest_number.number.value}',
                    'timestamp': latest_number.timestamp,
                    'url': f'/learning/numbers/{latest_number.number.value}/',
                    'progress': numbers_progress_pct
                })
                
            # Words
            latest_word = ChildWordProgress.objects.filter(child=user).select_related('word').order_by('-timestamp').first()
            total_words = 50
            completed_words = ChildWordProgress.objects.filter(child=user, completed=True).count()
            words_progress_pct = int((completed_words / total_words) * 100) if total_words else 0
            
            if latest_word:
                latest_activities.append({
                    'type': 'Learning / Words',
                    'title': f'Word Practice: {latest_word.word.text}',
                    'timestamp': latest_word.timestamp,
                    'url': f'/learning/words/{latest_word.word.id}/',
                    'progress': words_progress_pct
                })
                
            # Emotions
            latest_emotion = ChildEmotionProgress.objects.filter(child=user).select_related('emotion').order_by('-timestamp').first()
            total_emotions = Emotion.objects.filter(is_active=True).count()
            completed_emotions = ChildEmotionProgress.objects.filter(child=user, completed=True).count()
            emotions_progress_pct = int((completed_emotions / total_emotions) * 100) if total_emotions else 0
            
            if latest_emotion:
                latest_activities.append({
                    'type': 'Learning / Emotions',
                    'title': f'Emotion: {latest_emotion.emotion.name}',
                    'timestamp': latest_emotion.timestamp,
                    'url': f'/learning/emotions/{latest_emotion.emotion.id}/',
                    'progress': emotions_progress_pct
                })
                
            # Games
            latest_game = GameSession.objects.filter(child=user).select_related('game').order_by('-started_at').first()
            games_progress_pct = 0
            if latest_game:
                games_progress_pct = latest_game.score if latest_game.score <= 100 else 100
                
                game_url = '/games/'
                if 'color' in latest_game.game.name.lower():
                    game_url = '/games/color-matching/'
                elif 'animal' in latest_game.game.name.lower():
                    game_url = '/games/animal-matching/'
                    
                latest_activities.append({
                    'type': 'Games',
                    'title': f'{latest_game.game.name} - Level {latest_game.level}',
                    'timestamp': latest_game.started_at,
                    'url': game_url,
                    'progress': games_progress_pct
                })
                
            # Sort all by timestamp
            if latest_activities:
                latest_activities.sort(key=lambda x: x['timestamp'], reverse=True)
                context['continue_activity'] = latest_activities[0]
            else:
                context['continue_activity'] = {
                    'type': 'Learning Area',
                    'title': 'Start a New Journey',
                    'url': '/learning/',
                    'progress': 0
                }
                
            # Module progress for cards
            context['module_progress'] = {
                'letters': letters_progress_pct,
                'numbers': numbers_progress_pct,
                'words': words_progress_pct,
                'emotions': emotions_progress_pct,
                'games': games_progress_pct
            }
                
        except ChildProfile.DoesNotExist:
            pass
            
    elif user.role == CustomUser.UserRole.PARENT:
        try:
            parent_profile = user.parent_profile
            context['parent_profile'] = parent_profile
            context['children'] = parent_profile.assigned_children.all()
        except ParentProfile.DoesNotExist:
            pass
    
    return render(request, f'users/dashboard_{user.role}.html', context)


@login_required
def analytics_view(request):
    """View for cross-student class analytics (Teacher only)"""
    if request.user.role != 'teacher':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')
    
    teacher_profile = request.user.teacher_profile
    assigned_children = teacher_profile.assigned_children.all()
    
    # Fallback to all children if none assigned to this specific teacher
    if not assigned_children.exists():
        assigned_children = ChildProfile.objects.all()
        
    assigned_user_ids = assigned_children.values_list('user_id', flat=True)
    assigned_child_ids = assigned_children.values_list('id', flat=True)
    
    # 1. CLASS OVERVIEW METRICS
    total_students = assigned_children.count()
    
    from apps.games.models import GameSession, GameProgress, Game
    from apps.learning.models import ChildLetterProgress, ChildNumberProgress, ChildWordProgress, ChildEmotionProgress, Letter, Number, Word, Emotion
    from apps.drawing.models import Drawing, DrawingSession
    from apps.routines.models import TaskCompletion

    # Learning completion aggregation
    # Set defaults if tables are empty
    l_total = Letter.objects.count() or 26
    n_total = Number.objects.count() or 21
    w_total = Word.objects.count() or 50
    e_total = Emotion.objects.filter(is_active=True).count() or 8
    total_learning_available = l_total + n_total + w_total + e_total
    
    l_completed = ChildLetterProgress.objects.filter(child_id__in=assigned_user_ids, completed=True).count()
    n_completed = ChildNumberProgress.objects.filter(child_id__in=assigned_user_ids, completed=True).count()
    w_completed = ChildWordProgress.objects.filter(child_id__in=assigned_user_ids, completed=True).count()
    e_completed = ChildEmotionProgress.objects.filter(child_id__in=assigned_user_ids, completed=True).count()
    
    total_completed = l_completed + n_completed + w_completed + e_completed
    denom = (total_learning_available * total_students)
    avg_completion_rate = (total_completed / denom) * 100 if denom else 0
    
    # Game accuracy
    avg_game_success = GameProgress.objects.filter(child_id__in=assigned_user_ids).aggregate(Avg('average_accuracy'))['average_accuracy__avg'] or 0.0
    
    # Total drawings & Routine Tasks
    total_drawings = Drawing.objects.filter(child_id__in=assigned_user_ids).count()
    total_routine_tasks = TaskCompletion.objects.filter(child_id__in=assigned_user_ids).count()
    
    # 2. LEARNING ANALYTICS (CROSS-STUDENT)
    most_attempted_letters = ChildLetterProgress.objects.filter(child_id__in=assigned_user_ids).values('letter__char').annotate(count=Sum('attempts')).order_by('-count')[:5]
    difficult_letters = ChildLetterProgress.objects.filter(child_id__in=assigned_user_ids, completed=False).values('letter__char').annotate(count=Count('id')).order_by('-count')[:5]
    
    top_emotions = ChildEmotionProgress.objects.filter(child_id__in=assigned_user_ids, completed=True).values('emotion__name').annotate(count=Count('id')).order_by('-count')[:5]
    
    # 3. GAME ANALYTICS
    game_stats = GameProgress.objects.filter(child_id__in=assigned_user_ids).values('game__name').annotate(
        avg_acc=Avg('average_accuracy'),
        total_sess=Sum('total_sessions'),
        max_lvl=Max('highest_level_completed')
    ).order_by('-total_sess')

    # 4. DRAWING ANALYTICS
    top_creators = Drawing.objects.filter(child_id__in=assigned_user_ids).values('child__first_name', 'child__profile_picture').annotate(count=Count('id')).order_by('-count')[:5]
    
    # 5. RISK INDICATORS
    week_ago = timezone.now() - timedelta(days=7)
    at_risk = ChildProfile.objects.filter(
        id__in=assigned_child_ids,
        user__last_login__lt=week_ago
    ).select_related('user').distinct()[:10]

    context = {
        'profile': teacher_profile,
        'assigned_children': assigned_children,
        'overview': {
            'total_students': total_students,
            'avg_learning_completion': round(avg_completion_rate, 1),
            'avg_game_accuracy': round(avg_game_success, 1),
            'total_drawings': total_drawings,
            'total_routine_tasks': total_routine_tasks,
        },
        'learning': {
            'most_attempted': most_attempted_letters,
            'difficult': difficult_letters,
            'top_emotions': top_emotions,
        },
        'game_stats': game_stats,
        'top_creators': top_creators,
        'at_risk': at_risk,
    }
    
    return render(request, 'users/analytics.html', context)


@login_required
def profile_view(request):
    """User profile view and edit"""
    user = request.user
    
    if request.method == 'POST':
        user_form = UserProfileForm(request.POST, request.FILES, instance=user)
        
        if user.role == CustomUser.UserRole.TEACHER:
            try:
                profile = user.teacher_profile
                profile_form = TeacherProfileForm(request.POST, instance=profile)
            except TeacherProfile.DoesNotExist:
                profile = TeacherProfile.objects.create(user=user)
                profile_form = TeacherProfileForm(request.POST, instance=profile)
        elif user.role == CustomUser.UserRole.CHILD:
            try:
                profile = user.child_profile
                profile_form = ChildProfileForm(request.POST, instance=profile)
            except ChildProfile.DoesNotExist:
                profile = ChildProfile.objects.create(user=user, age=5)  # Default age
                profile_form = ChildProfileForm(request.POST, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('users:profile')
    else:
        user_form = UserProfileForm(instance=user)
        
        if user.role == CustomUser.UserRole.TEACHER:
            try:
                profile = user.teacher_profile
                profile_form = TeacherProfileForm(instance=profile)
            except TeacherProfile.DoesNotExist:
                profile = TeacherProfile.objects.create(user=user)
                profile_form = TeacherProfileForm(instance=profile)
        elif user.role == CustomUser.UserRole.CHILD:
            try:
                profile = user.child_profile
                profile_form = ChildProfileForm(instance=profile)
            except ChildProfile.DoesNotExist:
                profile = ChildProfile.objects.create(user=user, age=5)  # Default age
                profile_form = ChildProfileForm(instance=profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'user': user,
    }
    
    return render(request, 'users/profile.html', context)


@login_required
def user_list_view(request):
    """View for listing users (Teacher only)"""
    if request.user.role != 'teacher':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')
    
    try:
        # Show only assigned children for teachers
        users = CustomUser.objects.filter(
            id__in=request.user.teacher_profile.assigned_children.values_list('user_id', flat=True)
        ).order_by('-date_joined')
    except TeacherProfile.DoesNotExist:
        users = CustomUser.objects.none()
        
    return render(request, 'users/user_list.html', {'users': users})


@login_required
def user_detail_view(request, user_id):
    """View for user details (Teacher-facing Student Profile & Analytics)"""
    if request.user.role != 'teacher':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')
    
    user_detail = get_object_or_404(CustomUser, id=user_id)
    
    # Check if the user is a child
    if user_detail.role != 'child':
        messages.error(request, 'Profile not found or access denied.')
        return redirect('users:dashboard')

    context = {
        'user_detail': user_detail,
    }

    if user_detail.role == 'child':
        from apps.games.models import GameSession, GameProgress
        from apps.learning.models import ChildLetterProgress, ChildNumberProgress, ChildWordProgress, ChildEmotionProgress, Emotion
        from apps.drawing.models import Drawing, DrawingSession
        from apps.routines.models import TaskCompletion
        
        # 1. STUDENT OVERVIEW ANALYTICS
        game_sessions = GameSession.objects.filter(child=user_detail)
        total_game_completed = game_sessions.filter(completed=True).count()
        
        letter_progress = ChildLetterProgress.objects.filter(child=user_detail)
        number_progress = ChildNumberProgress.objects.filter(child=user_detail)
        word_progress = ChildWordProgress.objects.filter(child=user_detail)
        emotion_progress = ChildEmotionProgress.objects.filter(child=user_detail)
        task_completions = TaskCompletion.objects.filter(child=user_detail)
        
        learning_completed = (
            letter_progress.filter(completed=True).count() +
            number_progress.filter(completed=True).count() +
            word_progress.filter(completed=True).count() +
            emotion_progress.filter(completed=True).count()
        )
        
        drawings = Drawing.objects.filter(child=user_detail)
        total_drawings = drawings.count()
        total_routine_tasks = task_completions.count()
        
        total_activities = total_game_completed + learning_completed + total_drawings + total_routine_tasks
        
        # Overall success rate (proxied by average game accuracy)
        overall_accuracy = GameProgress.objects.filter(child=user_detail).aggregate(Avg('average_accuracy'))['average_accuracy__avg'] or 0.0
        
        # 2. LEARNING PROGRESS
        total_emotions = Emotion.objects.filter(is_active=True).count() or 8
        learning_stats = {
            'letters': {
                'count': letter_progress.filter(completed=True).count(),
                'total': 26,
                'percentage': round((letter_progress.filter(completed=True).count() / 26) * 100, 1) if 26 else 0
            },
            'numbers': {
                'count': number_progress.filter(completed=True).count(),
                'total': 21,
                'percentage': round((number_progress.filter(completed=True).count() / 21) * 100, 1) if 21 else 0
            },
            'words': {
                'count': word_progress.filter(completed=True).count(),
                'total': 50,
                'percentage': round((word_progress.filter(completed=True).count() / 50) * 100, 1) if 50 else 0
            },
            'emotions': {
                'count': emotion_progress.filter(completed=True).count(),
                'total': total_emotions,
                'percentage': round((emotion_progress.filter(completed=True).count() / total_emotions) * 100, 1) if total_emotions else 0
            }
        }
        
        # 3. GAME PERFORMANCE
        game_progress = GameProgress.objects.filter(child=user_detail).select_related('game')
        avg_game_time = game_sessions.aggregate(Avg('time_taken'))['time_taken__avg'] or 0
        
        # 4. DRAWING GALLERY
        drawing_gallery = drawings.order_by('-updated_at')
        
        # 5. ACTIVITY TIMELINE (All modules)
        activity_list = []
        
        for gs in game_sessions.order_by('-started_at')[:10]:
            activity_list.append({
                'type': 'game',
                'title': gs.game.name,
                'detail': f"Level {gs.level} — Score: {gs.score}",
                'timestamp': gs.started_at,
                'icon': 'sports_esports',
                'color': '#f59e0b',
            })
            
        for dr in drawings.order_by('-updated_at')[:10]:
            activity_list.append({
                'type': 'drawing',
                'title': dr.title,
                'detail': "Drawing saved",
                'timestamp': dr.updated_at,
                'icon': 'palette',
                'color': '#10b981',
            })
            
        for lp in letter_progress.filter(completed=True).order_by('-timestamp')[:10]:
            activity_list.append({
                'type': 'learning',
                'title': f"Letter {lp.letter.char}",
                'detail': "Alphabet tracing completed",
                'timestamp': lp.timestamp,
                'icon': 'abc',
                'color': '#8b5cf6',
            })

        for np in number_progress.filter(completed=True).order_by('-timestamp')[:10]:
            activity_list.append({
                'type': 'learning',
                'title': f"Number {np.number.value}",
                'detail': "Number practice completed",
                'timestamp': np.timestamp,
                'icon': '123',
                'color': '#8b5cf6',
            })

        for wp in word_progress.filter(completed=True).order_by('-timestamp')[:10]:
            activity_list.append({
                'type': 'learning',
                'title': f"Word: {wp.word.text}",
                'detail': "Word learning completed",
                'timestamp': wp.timestamp,
                'icon': 'spellcheck',
                'color': '#8b5cf6',
            })

        for ep in emotion_progress.filter(completed=True).order_by('-timestamp')[:10]:
            activity_list.append({
                'type': 'emotion',
                'title': f"Emotion: {ep.emotion.name}",
                'detail': "Emotion learning completed",
                'timestamp': ep.timestamp,
                'icon': 'mood',
                'color': '#ec4899',
            })

        for tc in task_completions.order_by('-completed_at')[:10]:
            activity_list.append({
                'type': 'routine',
                'title': tc.task.title,
                'detail': f"Routine task completed — {tc.task.routine.title}",
                'timestamp': tc.completed_at,
                'icon': 'task_alt',
                'color': '#06b6d4',
            })
            
        activity_timeline = sorted(activity_list, key=lambda x: x['timestamp'], reverse=True)[:20]
        
        context.update({
            'stats': {
                'total_activities': total_activities,
                'overall_accuracy': round(overall_accuracy, 1),
                'avg_game_time': round(avg_game_time / 60, 1) if avg_game_time else 0,
            },
            'learning_stats': learning_stats,
            'game_progress': game_progress,
            'drawing_gallery': drawing_gallery,
            'activity_timeline': activity_timeline,
        })

    return render(request, 'users/user_detail.html', context)



@login_required
def students_view(request):
    """Students search and recent view for teachers"""
    if request.user.role != 'teacher':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')
    
    query = request.GET.get('q', '').strip()
    search_results = None
    
    if query:
        search_results = CustomUser.objects.filter(
            Q(role='child') & (
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(phone_number__icontains=query) |
                Q(username__icontains=query)
            )
        ).distinct()
    
    # 5 Most recently joined students
    recent_students = CustomUser.objects.filter(role='child').order_by('-date_joined')[:5]
    
    context = {
        'is_teacher': True,
        'recent_students': recent_students,
        'search_results': search_results,
        'query': query,
    }
    
    return render(request, 'users/students.html', context)


@login_required
def reports_view(request):
    """Reports view for teachers - Aggregates performance data into summaries"""
    if request.user.role != 'teacher':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')
    
    try:
        teacher_profile = request.user.teacher_profile
        assigned_children = teacher_profile.assigned_children.all()
        if not assigned_children.exists():
            assigned_children = ChildProfile.objects.all()
        assigned_ids = assigned_children.values_list('id', flat=True)
        assigned_user_ids = assigned_children.values_list('user_id', flat=True)
        
        from apps.games.models import GameProgress, GameSession
        from apps.learning.models import ChildLetterProgress, ChildNumberProgress, ChildWordProgress, ChildEmotionProgress
        from apps.drawing.models import Drawing
        from apps.routines.models import TaskCompletion

        # Monthly Class Summary (Derived)
        month_ago = timezone.now() - timedelta(days=30)
        
        student_reports = []
        for child in assigned_children:
            # Game performance - Use user_id as those models link to User
            game_perf = GameProgress.objects.filter(child_id=child.user_id).aggregate(
                avg_acc=Avg('average_accuracy'),
                total_sess=Sum('total_sessions')
            )
            
            # Learning progress - Use user_id
            l_comp = ChildLetterProgress.objects.filter(child_id=child.user_id, completed=True).count()
            n_comp = ChildNumberProgress.objects.filter(child_id=child.user_id, completed=True).count()
            w_comp = ChildWordProgress.objects.filter(child_id=child.user_id, completed=True).count()
            e_comp = ChildEmotionProgress.objects.filter(child_id=child.user_id, completed=True).count()
            
            # Drawing - Use user_id
            draw_count = Drawing.objects.filter(child_id=child.user_id).count()
            
            # Routine Tasks
            task_count = TaskCompletion.objects.filter(child_id=child.user_id).count()
            
            student_reports.append({
                'name': child.user.get_full_name(),
                'id': child.user.id,
                'game_accuracy': round(game_perf['avg_acc'] or 0, 1),
                'game_sessions': game_perf['total_sess'] or 0,
                'learning_total': l_comp + n_comp + w_comp + e_comp,
                'drawings': draw_count,
                'routine_tasks': task_count,
            })

        context = {
            'is_teacher': True,
            'student_reports': student_reports,
            'class_summary': {
                'total_students': assigned_children.count(),
                'avg_class_accuracy': round(GameProgress.objects.filter(child_id__in=assigned_user_ids).aggregate(Avg('average_accuracy'))['average_accuracy__avg'] or 0, 1),
                'total_drawings': Drawing.objects.filter(child_id__in=assigned_user_ids).count(),
                'total_routine_tasks': TaskCompletion.objects.filter(child_id__in=assigned_user_ids).count(),
            }
        }
        
        return render(request, 'users/reports.html', context)
    except TeacherProfile.DoesNotExist:
        messages.error(request, 'Teacher profile not found.')
        return redirect('users:dashboard')


@login_required
def notifications_view(request):
    """Notifications view for teachers - Generates dynamic alerts based on activity"""
    if request.user.role != 'teacher':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')
    
    try:
        teacher_profile = request.user.teacher_profile
        assigned_children = teacher_profile.assigned_children.all()
        if not assigned_children.exists():
            assigned_children = ChildProfile.objects.all()
        assigned_ids = assigned_children.values_list('id', flat=True)
        assigned_user_ids = assigned_children.values_list('user_id', flat=True)
        
        from apps.games.models import GameSession
        from apps.learning.models import ChildLetterProgress, ChildNumberProgress, ChildWordProgress
        from apps.drawing.models import Drawing

        notifications = []
        
        # 1. Recent Game Completions
        recent_games = GameSession.objects.filter(child_id__in=assigned_user_ids, completed=True).order_by('-completed_at')[:5]
        for game in recent_games:
            notifications.append({
                'type': 'success',
                'message': f'{game.child.get_full_name()} completed {game.game.name} (Level {game.level})',
                'timestamp': game.completed_at or game.started_at,
                'icon': 'emoji_events'
            })
            
        # 2. Recent Drawing Submissions
        recent_drawings = Drawing.objects.filter(child_id__in=assigned_user_ids).order_by('-updated_at')[:5]
        for drawing in recent_drawings:
            notifications.append({
                'type': 'info',
                'message': f'{drawing.child.get_full_name()} submitted a new drawing: "{drawing.title}"',
                'timestamp': drawing.updated_at,
                'icon': 'palette'
            })
            
        # 3. Learning Milestones
        recent_learning = ChildLetterProgress.objects.filter(child_id__in=assigned_user_ids, completed=True).order_by('-timestamp')[:5]
        for item in recent_learning:
            notifications.append({
                'type': 'primary',
                'message': f'{item.child.get_full_name()} mastered Letter {item.letter.char}',
                'timestamp': item.timestamp,
                'icon': 'menu_book'
            })

        # 4. Success Indicators / Risk
        week_ago = timezone.now() - timedelta(days=7)
        inactive_students = assigned_children.filter(user__last_login__lt=week_ago)
        for student in inactive_students:
            notifications.append({
                'type': 'warning',
                'message': f'{student.user.get_full_name()} hasn\'t logged in for over a week',
                'timestamp': student.user.last_login or timezone.now(),
                'icon': 'person_off'
            })

        # Sort all by timestamp
        notifications.sort(key=lambda x: x['timestamp'], reverse=True)

        context = {
            'is_teacher': True,
            'notifications': notifications[:20], # Show top 20
        }
        
        return render(request, 'users/notifications.html', context)
    except TeacherProfile.DoesNotExist:
        messages.error(request, 'Teacher profile not found.')
        return redirect('users:dashboard')


@login_required
def settings_view(request):
    """Settings view for teachers"""
    if request.user.role != 'teacher':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')
    
    try:
        teacher_profile = TeacherProfile.objects.get(user=request.user)
        context = {
            'is_teacher': True,
            'profile': teacher_profile,
        }
    except TeacherProfile.DoesNotExist:
        messages.error(request, 'Teacher profile not found.')
        return redirect('users:dashboard')
    
    return render(request, 'users/settings.html', context)
