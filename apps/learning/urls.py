from django.urls import path
from . import views

app_name = 'learning'

urlpatterns = [
    path('', views.learning_dashboard, name='learning_dashboard'),
    path('alphabet/', views.alphabet_learning, name='alphabet_learning'),
    path('alphabet/<str:letter>/', views.letter_detail, name='letter_detail'),
    path('numbers/', views.number_learning, name='number_learning'),
    path('numbers/<int:number>/', views.number_detail, name='number_detail'),
    path('words/', views.word_learning, name='word_learning'),
    path('words/<int:word_id>/', views.word_detail, name='word_detail'),
    path('emotions/', views.emotion_learning, name='emotion_learning'),
    path('emotions/<int:emotion_id>/', views.emotion_detail, name='emotion_detail'),
    path('progress/', views.progress_dashboard, name='progress_dashboard'),
    
    # API endpoints for React app integration
    path('api/complete/', views.mark_item_complete, name='api_mark_complete'),
    path('api/progress/', views.get_user_progress, name='api_get_progress'),
] 