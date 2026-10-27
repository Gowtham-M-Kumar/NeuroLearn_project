from django.shortcuts import render, get_object_or_404
from .models import Letter, Number, Word, Emotion, ChildLetterProgress, ChildNumberProgress, ChildWordProgress, ChildEmotionProgress, Achievement, LearningProgress
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .serializers import LearningProgressSerializer, ProgressCompleteSerializer

@login_required
def alphabet_learning(request):
    letters = Letter.objects.all().order_by('char')
    completed_items = LearningProgress.objects.filter(
        user=request.user, module='alphabet', completed=True
    ).values_list('item', flat=True)
    return render(request, 'learning/alphabet_learning.html', {
        'letters': letters,
        'completed_items': list(completed_items)
    })

@login_required
def letter_detail(request, letter):
    letter_obj = get_object_or_404(Letter, char__iexact=letter)
    return render(request, 'learning/letter_detail.html', {'letter': letter_obj})

@login_required
def number_learning(request):
    numbers = Number.objects.all().order_by('value')
    completed_items = LearningProgress.objects.filter(
        user=request.user, module='numbers', completed=True
    ).values_list('item', flat=True)
    return render(request, 'learning/number_learning.html', {
        'numbers': numbers,
        'completed_items': list(completed_items)
    })

@login_required
def number_detail(request, number):
    number_obj = get_object_or_404(Number, value=number)
    return render(request, 'learning/number_detail.html', {'number': number_obj})

@login_required
def word_learning(request):
    categories = Word.CATEGORY_CHOICES
    completed_items = LearningProgress.objects.filter(
        user=request.user, module='words', completed=True
    ).values_list('item', flat=True)
    return render(request, 'learning/word_learning.html', {
        'categories': categories,
        'completed_items': list(completed_items)
    })

@login_required
def word_detail(request, word_id):
    word_obj = get_object_or_404(Word, id=word_id)
    return render(request, 'learning/word_detail.html', {'word': word_obj})

@login_required
def emotion_learning(request):
    emotions = Emotion.objects.filter(is_active=True).order_by('name')
    # Get IDs of emotions completed by this child
    completed_ids = ChildEmotionProgress.objects.filter(
        child=request.user, 
        completed=True
    ).values_list('emotion_id', flat=True)
    
    return render(request, 'learning/emotion_learning.html', {
        'emotions': emotions,
        'completed_ids': completed_ids
    })

@login_required
def emotion_detail(request, emotion_id):
    emotion_obj = get_object_or_404(Emotion, id=emotion_id)
    # Check if this emotion has already been completed by the current child
    completed = ChildEmotionProgress.objects.filter(child=request.user, emotion=emotion_obj, completed=True).exists()
    return render(request, 'learning/emotion_detail.html', {
        'emotion': emotion_obj,
        'completed': completed
    })

@login_required
def progress_dashboard(request):
    return render(request, 'learning/progress_dashboard.html')

def learning_dashboard(request):
    return render(request, 'learning/dashboard.html')


# ============================================================================
# API ENDPOINTS FOR REACT APP INTEGRATION
# ============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_item_complete(request):
    """
    POST /api/learning/complete/
    
    Mark a learning item as completed for the current user.
    Prevents duplicate completions using get_or_create.
    
    Request body:
    {
        "module": "alphabet",
        "item": "A",
        "completed": true
    }
    
    Returns:
    - 201: Item marked as completed (newly created)
    - 200: Item was already completed
    - 400: Validation error
    """
    # DEBUG: Log which user is making the request
    print(f"[DEBUG] User making request: {request.user.username} (ID: {request.user.id})")
    
    serializer = ProgressCompleteSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    module = serializer.validated_data['module']
    item = serializer.validated_data['item']
    completed = serializer.validated_data.get('completed', True)
    
    print(f"[DEBUG] Saving: module={module}, item={item}, user={request.user.username}")
    
    # Use get_or_create to prevent duplicate entries
    # CRITICAL: This is scoped to request.user - each child gets their own progress
    progress, created = LearningProgress.objects.get_or_create(
        user=request.user,  # This ensures data is separate per child!
        module=module,
        item=item,
        defaults={'completed': completed}
    )
    
    # If already exists, update the completed status
    if not created and progress.completed != completed:
        progress.completed = completed
        progress.save()
    
    # --- SYNC WITH MODULE-SPECIFIC MODELS FOR TEACHER DASHBOARD ---
    # The teacher dashboard and student profiles aggregate data from these specific models.
    if completed:
        try:
            if module == 'emotions' or module == 'emotion':
                # For emotions, item is usually the emotion ID
                from .models import Emotion, ChildEmotionProgress
                try:
                    emotion_id = int(item)
                    Emotion.objects.filter(id=emotion_id).exists()
                    ChildEmotionProgress.objects.update_or_create(
                        child=request.user,
                        emotion_id=emotion_id,
                        defaults={'completed': True}
                    )
                except ValueError:
                    # Fallback to name if not numeric
                    emotion = Emotion.objects.filter(name__iexact=item).first()
                    if emotion:
                        ChildEmotionProgress.objects.update_or_create(
                            child=request.user,
                            emotion=emotion,
                            defaults={'completed': True}
                        )
            
            elif module == 'alphabet' or module == 'letters':
                from .models import Letter, ChildLetterProgress
                # For letters, item is usually the character like "A"
                letter = Letter.objects.filter(char__iexact=item).first()
                if letter:
                    ChildLetterProgress.objects.update_or_create(
                        child=request.user,
                        letter=letter,
                        defaults={'completed': True}
                    )
            
            elif module == 'numbers':
                from .models import Number, ChildNumberProgress
                try:
                    num_val = int(item)
                    number = Number.objects.filter(value=num_val).first()
                    if number:
                        ChildNumberProgress.objects.update_or_create(
                            child=request.user,
                            number=number,
                            defaults={'completed': True}
                        )
                except ValueError:
                    pass
            
            elif module == 'words':
                from .models import Word, ChildWordProgress
                try:
                    word_id = int(item)
                    ChildWordProgress.objects.update_or_create(
                        child=request.user,
                        word_id=word_id,
                        defaults={'completed': True}
                    )
                except ValueError:
                    word = Word.objects.filter(text__iexact=item).first()
                    if word:
                        ChildWordProgress.objects.update_or_create(
                            child=request.user,
                            word=word,
                            defaults={'completed': True}
                        )
        except Exception as e:
            print(f"[ERROR] Syncing learning progress to specific models: {e}")
    
    response_serializer = LearningProgressSerializer(progress)
    
    return Response(
        {
            'message': 'Progress saved successfully',
            'created': created,
            'data': response_serializer.data
        },
        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_progress(request):
    """
    GET /api/learning/progress/
    GET /api/learning/progress/?module=alphabet
    
    Retrieve all learning progress for the logged-in user.
    Optionally filter by module using query parameter.
    
    Query parameters:
    - module (optional): Filter progress by specific module
    
    Returns:
    {
        "count": 5,
        "user": "username",
        "user_id": 123,
        "results": [
            {
                "id": 1,
                "module": "alphabet",
                "item": "A",
                "completed": true,
                "completed_at": "2026-01-06T12:00:00Z"
            },
            ...
        ]
    }
    """
    # DEBUG: Log which user is requesting their progress
    print(f"[DEBUG] Progress requested by: {request.user.username} (ID: {request.user.id})")
    
    # Get progress for current user only - SCOPED PER CHILD
    progress = LearningProgress.objects.filter(user=request.user)
    
    # Optional: Filter by module
    module = request.query_params.get('module', None)
    if module:
        progress = progress.filter(module=module)
    
    serializer = LearningProgressSerializer(progress, many=True)
    
    return Response({
        'count': progress.count(),
        'user': request.user.username,  # Show which user's data this is
        'user_id': request.user.id,
        'results': serializer.data
    })

