from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, api_views

app_name = 'routines'

router = DefaultRouter()
router.register(r'child-routines', api_views.ChildRoutineViewSet, basename='child-routine')

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
    
    # Routine management
    path('', views.routine_list, name='routine_list'),
    path('dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('search-children/', views.child_search, name='child_search'),
    path('create/<int:child_id>/', views.routine_create, name='routine_create'),
    path('<int:routine_id>/', views.routine_detail, name='routine_detail'),
    path('<int:routine_id>/edit/', views.routine_edit, name='routine_edit'),
    path('<int:routine_id>/progress/', views.routine_progress, name='routine_progress'),
    path('<int:routine_id>/schedule/', views.routine_schedule, name='routine_schedule'),
    
    # Task management
    path('<int:routine_id>/tasks/create/', views.task_create, name='task_create'),
    path('tasks/<int:task_id>/edit/', views.task_edit, name='task_edit'),
    path('tasks/<int:task_id>/delete/', views.task_delete, name='task_delete'),
    path('tasks/<int:task_id>/complete/', views.task_complete, name='task_complete'),
    # Timetable management
    path('<int:routine_id>/timetable/add/', views.timetable_entry_add, name='timetable_entry_add'),
    path('timetable/entry/<int:entry_id>/edit/', views.timetable_entry_edit, name='timetable_entry_edit'),
    path('timetable/entry/<int:entry_id>/delete/', views.timetable_entry_delete, name='timetable_entry_delete'),
    path('tasks/reorder/', views.task_reorder, name='task_reorder'),
]