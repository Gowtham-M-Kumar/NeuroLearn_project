from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import transaction
import json
import random
from datetime import datetime

from .models import (
    Game, ColorMatchingGame, Color, ColorMatchingLevel,
    Animal, AnimalMatchingLevel,
    GameSession, ColorMatchingSession, AnimalMatchingSession, GameProgress
)

@login_required
def games_dashboard(request):
    """Display available games"""
    games = Game.objects.filter(is_active=True)
    progress = GameProgress.objects.filter(child=request.user)
    progress_dict = {p.game_id: p for p in progress}
    
    context = {
        'games': games,
        'progress': progress_dict,
        'progress_list': list(progress),
    }
    return render(request, 'games/dashboard.html', context)

@login_required
def color_matching_levels(request):
    """Display color matching game levels"""
    game = Game.objects.filter(name__icontains='color matching').first()
    if not game:
        # Fallback if somehow missing
        game = Game.objects.create(name="Color Matching", description="Match colors to boost your memory!")
    levels = ColorMatchingGame.objects.filter(is_active=True).order_by('level')
    
    # Get user's progress for this game
    progress, created = GameProgress.objects.get_or_create(
        child=request.user,
        game=game,
        defaults={'highest_level_completed': 0}
    )
    
    # Annotate levels with UI status
    levels_list = []
    for l in levels:
        l.is_unlocked = (l.level == 1 or progress.highest_level_completed >= l.level - 1)
        l.is_completed = (progress.highest_level_completed >= l.level)
        
        # UI Properties
        if not l.is_unlocked:
            l.status_icon = 'lock'
            l.status_bg = 'var(--border-subtle)'
        elif l.is_completed:
            l.status_icon = 'check_circle'
            l.status_bg = '#10b981'
        else:
            l.status_icon = 'grid_view'
            l.status_bg = 'var(--accent-primary)'
            
        levels_list.append(l)
    
    context = {
        'game': game,
        'levels': levels_list,
        'progress': progress,
    }
    return render(request, 'games/color_matching_levels.html', context)

@login_required
def color_matching_game(request, level):
    """Play color matching game for specific level"""
    game = Game.objects.filter(name__icontains='color matching').first()
    if not game:
        game = Game.objects.create(name="Color Matching", description="Match colors to boost your memory!")
    level_obj = get_object_or_404(ColorMatchingGame, level=level, is_active=True)
    
    # Check if level is unlocked
    progress = GameProgress.objects.filter(child=request.user, game=game).first()
    if level > 1 and (not progress or progress.highest_level_completed < level - 1):
        messages.warning(request, "Complete previous levels to unlock this one!")
        return redirect('games:color_matching_levels')
        
    level_config = get_object_or_404(ColorMatchingLevel, game=level_obj)
    
    # Get colors for this level
    colors = list(level_config.colors.all())
    
    if not colors:
        return JsonResponse({'error': 'No colors configured for this level'}, status=400)
    
    # Create game session
    session, created = GameSession.objects.get_or_create(
        child=request.user,
        game=game,
        level=level,
        defaults={'started_at': timezone.now()}
    )
    
    # Prepare game data
    grid_size = level_config.grid_size
    num_colors_needed = (grid_size * grid_size) // 2
    
    # Select colors for this game
    game_colors = random.sample(colors, min(num_colors_needed, len(colors)))
    
    # Create pairs of cards
    cards = []
    for color in game_colors:
        cards.extend([color] * 2)  # Each color appears twice
    
    # Shuffle cards
    random.shuffle(cards)
    
    # Arrange cards in grid
    grid = []
    for i in range(grid_size):
        row = []
        for j in range(grid_size):
            card_index = i * grid_size + j
            if card_index < len(cards):
                row.append({
                    'id': card_index,
                    'color': cards[card_index].hex_code,
                    'name': cards[card_index].name,
                    'row': i,
                    'col': j
                })
        grid.append(row)
    
    context = {
        'game': game,
        'level': level_obj,
        'session': session,
        'grid': grid,
        'grid_size': grid_size,
        'time_limit': level_obj.time_limit,
        'required_matches': level_obj.required_matches,
        'colors': game_colors,
    }
    return render(request, 'games/color_matching.html', context)

@csrf_exempt
@login_required
def save_game_result(request):
    """Save game session results via AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            session_id = data.get('session_id')
            score = data.get('score', 0)
            time_taken = data.get('time_taken', 0)
            matches_found = data.get('matches_found', 0)
            total_attempts = data.get('total_attempts', 0)
            completed = data.get('completed', False)
            
            with transaction.atomic():
                # Update game session
                session = GameSession.objects.get(id=session_id, child=request.user)
                session.score = score
                session.time_taken = time_taken
                session.completed = completed
                if completed:
                    session.completed_at = timezone.now()
                session.save()
                
                if 'color matching' in session.game.name.lower():
                    # Create or update color matching session data
                    color_session, created = ColorMatchingSession.objects.get_or_create(
                        game_session=session,
                        defaults={
                            'matches_found': matches_found,
                            'total_attempts': total_attempts,
                            'accuracy': (matches_found / total_attempts * 100) if total_attempts > 0 else 0
                        }
                    )
                    if not created:
                        color_session.matches_found = matches_found
                        color_session.total_attempts = total_attempts
                        color_session.accuracy = (matches_found / total_attempts * 100) if total_attempts > 0 else 0
                        color_session.save()
                    accuracy_val = color_session.accuracy
                elif 'animal matching' in session.game.name.lower():
                    # Create or update animal matching session data
                    animal_session, created = AnimalMatchingSession.objects.get_or_create(
                        game_session=session,
                        defaults={
                            'matches_found': matches_found,
                            'total_attempts': total_attempts,
                        }
                    )
                    if not created:
                        animal_session.matches_found = matches_found
                        animal_session.total_attempts = total_attempts
                        animal_session.save()
                    accuracy_val = (matches_found / total_attempts * 100) if total_attempts > 0 else 0
                else:
                    accuracy_val = 0
                
                # Update game progress
                progress, created = GameProgress.objects.get_or_create(
                    child=request.user,
                    game=session.game,
                    defaults={
                        'highest_level_completed': session.level if completed else 0,
                        'total_score': score,
                        'total_sessions': 1,
                        'average_accuracy': accuracy_val,
                        'last_played': timezone.now()
                    }
                )
                
                if not created:
                    progress.total_score += score
                    progress.total_sessions += 1
                    if completed and session.level > progress.highest_level_completed:
                        progress.highest_level_completed = session.level
                    
                    # Update average accuracy
                    progress.average_accuracy = ((progress.average_accuracy * (progress.total_sessions - 1)) + accuracy_val) / progress.total_sessions
                    
                    progress.last_played = timezone.now()
                    progress.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Game result saved successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def animal_matching_levels(request):
    """Display animal matching game levels"""
    game = Game.objects.filter(name__icontains='animal matching').first()
    if not game:
        game = Game.objects.create(name="Animal Matching", description="Match animal heads and bodies!")
    
    levels = AnimalMatchingLevel.objects.filter(is_active=True).order_by('level')
    
    # Get user's progress for this game
    progress, created = GameProgress.objects.get_or_create(
        child=request.user,
        game=game,
        defaults={'highest_level_completed': 0}
    )
    
    context = {
        'game': game,
        'levels': list(levels),
        'progress': progress,
    }
    return render(request, 'games/animal_matching_levels.html', context)

@login_required
def animal_matching_game(request, level):
    """Play animal matching game for specific level"""
    game = Game.objects.filter(name__icontains='animal matching').first()
    level_obj = get_object_or_404(AnimalMatchingLevel, level=level, is_active=True)
    
    # Check if level is unlocked
    progress = GameProgress.objects.filter(child=request.user, game=game).first()
    if level > 1 and (not progress or progress.highest_level_completed < level - 1):
        messages.warning(request, "Complete previous levels to unlock this one!")
        return redirect('games:animal_matching_levels')

    # Get random animals for this level
    all_animals = list(Animal.objects.filter(is_active=True))
    if not all_animals:
        messages.error(request, "No animals found in database!")
        return redirect('games:animal_matching_levels')
        
    num_animals = min(level_obj.animal_count, len(all_animals))
    selected_animals = random.sample(all_animals, num_animals)
    
    # Shuffle for the draggable parts
    draggable_animals = list(selected_animals)
    random.shuffle(draggable_animals)
    
    # Create session
    session, created = GameSession.objects.get_or_create(
        child=request.user,
        game=game,
        level=level,
        defaults={'started_at': timezone.now()}
    )
    
    # Mock URLs for Unsplash if no image is set
    mock_urls = {
        "Lion": "https://images.unsplash.com/photo-1546182990-dffeafbe841d?auto=format&fit=crop&w=600&h=600",
        "Elephant": "https://images.unsplash.com/photo-1557050543-4d5f4e07ef46?auto=format&fit=crop&w=600&h=600",
        "Giraffe": "https://images.unsplash.com/photo-1547721064-36202181c929?auto=format&fit=crop&w=600&h=600",
        "Panda": "https://images.unsplash.com/photo-1564349683136-77e08bef1ef1?auto=format&fit=crop&w=600&h=600",
        "Tiger": "https://images.unsplash.com/photo-1561731216-c3a4d99437d5?auto=format&fit=crop&w=600&h=600",
        "Zebra": "https://images.unsplash.com/photo-1501705388883-4ed8a543392c?auto=format&fit=crop&w=600&h=600",
        "Monkey": "https://images.unsplash.com/photo-1540573133985-87b6da6d54a9?auto=format&fit=crop&w=600&h=600",
        "Rabbit": "https://images.unsplash.com/photo-1585110396054-c8112c607ecf?auto=format&fit=crop&w=600&h=600",
        "Fox": "https://images.unsplash.com/photo-1474511320723-9a56873867b5?auto=format&fit=crop&w=600&h=600",
        "Deer": "https://images.unsplash.com/photo-1484406566174-9da000fda645?auto=format&fit=crop&w=600&h=600",
    }

    animal_list = []
    for animal in selected_animals:
        url = animal.image.url if animal.image else mock_urls.get(animal.name, "")
        animal_list.append({'id': animal.id, 'name': animal.name, 'image_url': url})

    draggable_list = []
    for animal in draggable_animals:
        url = animal.image.url if animal.image else mock_urls.get(animal.name, "")
        draggable_list.append({'id': animal.id, 'name': animal.name, 'image_url': url})

    context = {
        'game': game,
        'level': level_obj,
        'session': session,
        'animals': animal_list,
        'draggable_animals': draggable_list,
    }
    return render(request, 'games/animal_matching_game.html', context)

@login_required
def reset_game_progress(request, child_id, game_id):
    """Allow teachers to reset a child's progress for a specific game"""
    if request.user.role != 'teacher':
        messages.error(request, "Access denied.")
        return redirect('users:dashboard')
        
    child = get_object_or_404(User, id=child_id)
    game = get_object_or_404(Game, id=game_id)
    
    # Delete progress
    GameProgress.objects.filter(child=child, game=game).delete()
    # Delete sessions
    GameSession.objects.filter(child=child, game=game).delete()
    
    messages.success(request, f"Progress reset for {child.get_full_name()} in {game.name}.")
    return redirect('users:user_detail', user_id=child_id)

@login_required
def game_progress(request):


    """Display user's game progress"""
    progress_list = GameProgress.objects.filter(child=request.user).order_by('-updated_at')
    
    context = {
        'progress_list': progress_list,
    }
    return render(request, 'games/progress.html', context)

@login_required
def game_history(request):
    """Display user's game session history"""
    sessions = GameSession.objects.filter(child=request.user).order_by('-started_at')
    
    context = {
        'sessions': sessions,
    }
    return render(request, 'games/history.html', context)
