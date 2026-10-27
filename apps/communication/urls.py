from django.urls import path
from . import views

app_name = 'communication'

urlpatterns = [
    path('', views.aac_dashboard, name='dashboard'),
    path('category/<int:category_id>/', views.aac_category_detail, name='category_detail'),
    path('learning/<int:symbol_id>/', views.aac_learning_mode, name='learning_mode'),
    path('type/', views.aac_type_mode, name='type_mode'),
]
