from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import Routine, Task, TaskCompletion, RoutineSchedule, TimetableEntry
from .forms import (
    RoutineForm, TaskForm, RoutineScheduleForm, TaskReorderForm, TimetableEntryForm
)

User = get_user_model()

@login_required
def routine_list(request):
    """Display list of routines based on user role"""
    user = request.user
    routines = []
    
    # Redirect teachers/therapists to their dedicated dashboard
    if user.role in ['teacher', 'therapist']:
        return redirect('routines:teacher_dashboard')
    
    if user.role == 'child':
        # Child is redirected directly to their personalized timetable
        if hasattr(user, 'routine') and user.routine.is_active:
            return redirect('routines:routine_detail', routine_id=user.routine.id)
    elif user.role == 'parent':
        # Parents see routines of their children
        children = user.parent_profile.children.all()
        for child_profile in children:
            if hasattr(child_profile.user, 'routine') and child_profile.user.routine.is_active:
                routines.append(child_profile.user.routine)
    
    context = {
        'routines': routines,
        'user_role': user.role
    }
    return render(request, 'routines/routine_list.html', context)


@login_required
def teacher_dashboard(request):
    """Teacher dashboard for routine management"""
    if request.user.role not in ['teacher', 'therapist']:
        messages.error(request, "Access denied.")
        return redirect('dashboard')
    
    # Fetch existing routines created by this teacher
    recent_routines = Routine.objects.filter(created_by=request.user).order_by('-updated_at')[:10]
        
    context = {
        'recent_routines': recent_routines
    }
    return render(request, 'routines/teacher_dashboard.html', context)


@login_required
def child_search(request):
    """AJAX search for children"""
    if request.user.role not in ['teacher', 'therapist']:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'results': []})
        
    # Search by name or phone
    children = User.objects.filter(
        role='child'
    ).filter(
        Q(first_name__icontains=query) | 
        Q(last_name__icontains=query) | 
        Q(phone_number__icontains=query) |
        Q(email__icontains=query)
    )[:20]
    
    results = []
    for child in children:
        has_routine = hasattr(child, 'routine')
        routine_id = child.routine.id if has_routine else None
        
        results.append({
            'id': child.id,
            'name': child.get_full_name(),
            'phone': child.phone_number,
            'has_routine': has_routine,
            'routine_id': routine_id
        })
        
    return JsonResponse({'results': results})


@login_required
def routine_detail(request, routine_id):
    routine = get_object_or_404(Routine, id=routine_id)
    user = request.user

    # Permission checks
    if user.role == 'child' and routine.child != user:
        messages.error(request, "Access denied.")
        return redirect('routines:routine_list')

    if user.role == 'parent':
        if not user.parent_profile.children.filter(user=routine.child).exists():
            messages.error(request, "Access denied.")
            return redirect('routines:routine_list')

    # Serialize timetable entries safely
    timetable = {
        'school': [],
        'leave': [],
    }

    entries = (
        TimetableEntry.objects
        .filter(routine=routine)
        .order_by('time')
    )

    for e in entries:
        timetable[e.day_type].append({
            'id': e.id,
            'time': e.time.strftime('%I:%M %p'),
            'task_type': e.task_type,
            'task_type_display': e.get_task_type_display(),
            'custom_description': e.custom_description or '',
            'notes': e.notes or '',
        })

    entry_form = TimetableEntryForm() if user.role in ['teacher', 'therapist'] else None

    return render(request, 'routines/routine_detail.html', {
        'routine': routine,
        'timetable': timetable,   # ✅ PURE DATA
        'entry_form': entry_form,
        'day_types': [('school', 'School Days'), ('leave', 'Leave Days')],
        'user_role': user.role,
    })

@login_required
@require_POST
def timetable_entry_add(request, routine_id):
    routine = get_object_or_404(Routine, id=routine_id)

    if request.user.role not in ['teacher', 'therapist']:
        return JsonResponse({'error': 'Permission denied'}, status=403)

    form = TimetableEntryForm(request.POST)

    if not form.is_valid():
        return JsonResponse({'errors': form.errors}, status=400)

    entry = form.save(commit=False)
    entry.routine = routine
    
    # Explicitly pull the calculated time from form.cleaned_data
    calculated_time = form.cleaned_data.get('time')
    entry.time = calculated_time

    # Prevent duplicate time per day type
    exists = TimetableEntry.objects.filter(
        routine=routine,
        day_type=entry.day_type,
        time=calculated_time
    ).exists()

    if exists:
        return JsonResponse({
            'error': 'An entry already exists for this time.'
        }, status=400)

    entry.save()
    return JsonResponse({'success': True})

@login_required
@require_POST
def timetable_entry_edit(request, entry_id):
    """AJAX view to edit a timetable entry"""
    entry = get_object_or_404(TimetableEntry, id=entry_id)
    if request.user.role not in ['teacher', 'therapist']:
        return JsonResponse({'error': 'Permission denied'}, status=403)
        
    form = TimetableEntryForm(request.POST, instance=entry)
    if not form.is_valid():
        return JsonResponse({'errors': form.errors}, status=400)
        
    # Prevent duplicate time per day type (excluding self)
    exists = TimetableEntry.objects.filter(
        routine=entry.routine,
        day_type=form.cleaned_data.get('day_type'),
        time=form.cleaned_data.get('time')
    ).exclude(id=entry.id).exists()
    
    if exists:
        return JsonResponse({'error': 'An entry already exists for this time.'}, status=400)
        
    form.save()
    return JsonResponse({'success': True})


@login_required
@require_POST
def timetable_entry_delete(request, entry_id):
    """AJAX view to delete a timetable entry"""
    entry = get_object_or_404(TimetableEntry, id=entry_id)
    if request.user.role not in ['teacher', 'therapist']:
        return JsonResponse({'error': 'Permission denied'}, status=403)
        
    entry.delete()
    return JsonResponse({'success': True})


@login_required
def routine_create(request, child_id):
    """Bypasses the intermediate form and auto-creates a routine profile for the child."""
    if request.user.role not in ['therapist', 'teacher']:
        messages.error(request, "Permission denied.")
        return redirect('routines:routine_list')
        
    child = get_object_or_404(User, id=child_id, role='child')
    
    # If routine already exists, jump straight to the timetable management
    if hasattr(child, 'routine'):
        return redirect('routines:routine_detail', routine_id=child.routine.id)
        
    # Standardize the routine creation
    routine = Routine.objects.create(
        title=f"Routine for {child.get_full_name()}",
        description=f"Personalized clinical timetable for {child.get_full_name()}",
        created_by=request.user,
        child=child
    )
    
    messages.success(request, f"Routine setup started for {child.get_full_name()}. You can now build the timetable below.")
    return redirect('routines:routine_detail', routine_id=routine.id)


@login_required
def routine_edit(request, routine_id):
    """Edit an existing routine"""
    routine = get_object_or_404(Routine, id=routine_id)
    
    # Teachers can edit any routine as per requirements "A teacher can edit any child's routine at any time"
    if request.user.role not in ['therapist', 'teacher']:
        messages.error(request, "Permission denied.")
        return redirect('routines:routine_detail', routine_id=routine.id)
    
    if request.method == 'POST':
        form = RoutineForm(request.POST, instance=routine)
        if form.is_valid():
            form.save()
            messages.success(request, "Routine updated successfully!")
            return redirect('routines:routine_detail', routine_id=routine.id)
    else:
        form = RoutineForm(instance=routine)
    
    context = {
        'form': form,
        'routine': routine,
        'title': f'Edit Routine: {routine.title} ({routine.child.get_full_name()})'
    }
    return render(request, 'routines/routine_form.html', context)


@login_required
def task_create(request, routine_id):
    """Add a new task to a routine"""
    routine = get_object_or_404(Routine, id=routine_id)
    
    if request.user.role not in ['therapist', 'teacher']:
        messages.error(request, "Permission denied.")
        return redirect('routines:routine_detail', routine_id=routine.id)
    
    if request.method == 'POST':
        form = TaskForm(request.POST, request.FILES)
        if form.is_valid():
            task = form.save(commit=False)
            task.routine = routine
            # Set order to last
            last_order = routine.tasks.order_by('-order').first()
            task.order = (last_order.order + 1) if last_order else 1
            task.save()
            messages.success(request, "Task added!")
            return redirect('routines:routine_detail', routine_id=routine.id)
    else:
        form = TaskForm()
    
    context = {
        'form': form,
        'routine': routine,
        'title': f'Add Task to {routine.title}'
    }
    return render(request, 'routines/task_form.html', context)


@login_required
def task_edit(request, task_id):
    """Edit an existing task"""
    task = get_object_or_404(Task, id=task_id)
    
    if request.user.role not in ['therapist', 'teacher']:
        messages.error(request, "Permission denied.")
        return redirect('routines:routine_detail', routine_id=task.routine.id)
    
    if request.method == 'POST':
        form = TaskForm(request.POST, request.FILES, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, "Task updated!")
            return redirect('routines:routine_detail', routine_id=task.routine.id)
    else:
        form = TaskForm(instance=task)
    
    context = {
        'form': form,
        'task': task,
        'routine': task.routine,
        'title': f'Edit Task: {task.title}'
    }
    return render(request, 'routines/task_form.html', context)

@login_required
@require_POST
def task_delete(request, task_id):
    """Delete a task"""
    task = get_object_or_404(Task, id=task_id)
    if request.user.role not in ['teacher', 'therapist']:
         messages.error(request, "Permission denied.")
         return redirect('routines:routine_detail', routine_id=task.routine.id)
    
    routine_id = task.routine.id
    task.delete()
    messages.success(request, "Task deleted.")
    return redirect('routines:routine_detail', routine_id=routine_id)


@login_required
@require_POST
def task_complete(request, task_id):
    """Mark a task as completed"""
    task = get_object_or_404(Task, id=task_id)
    user = request.user
    
    # Identify the child
    child = None
    if user.role == 'child':
        child = user
    elif user.role == 'parent':
        if task.routine.child in [c.user for c in user.parent_profile.children.all()]:
            child = task.routine.child
            
    if not child or child != task.routine.child:
         messages.error(request, "Permission denied.")
         return redirect('routines:routine_detail', routine_id=task.routine.id)

    # Check already completed today
    today = timezone.now().date()
    if TaskCompletion.objects.filter(task=task, child=child, completed_at__date=today).exists():
        return JsonResponse({'status': 'already_completed'})
        
    TaskCompletion.objects.create(task=task, child=child, completed_by=user)
    return JsonResponse({'status': 'success'})


@login_required
@csrf_exempt
@require_POST
def task_reorder(request):
    """Reorder tasks via AJAX"""
    if request.user.role not in ['therapist', 'teacher']:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        task_id = request.POST.get('task_id')
        new_order = int(request.POST.get('new_order'))
        task = Task.objects.get(id=task_id)
        task.order = new_order
        task.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def routine_schedule(request, routine_id):
    """Schedule a routine for specific times"""
    routine = get_object_or_404(Routine, id=routine_id)
    
    if request.user.role not in ['therapist', 'teacher'] or routine.created_by != request.user:
        messages.error(request, "You don't have permission to schedule this routine.")
        return redirect('routines:routine_detail', routine_id=routine.id)
    
    if request.method == 'POST':
        form = RoutineScheduleForm(request.POST, user=request.user)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.routine = routine
            schedule.save()
            messages.success(request, "Routine scheduled successfully!")
            return redirect('routines:routine_detail', routine_id=routine.id)
    else:
        form = RoutineScheduleForm(user=request.user)
    
    # Get existing schedules
    schedules = RoutineSchedule.objects.filter(routine=routine)
    
    context = {
        'form': form,
        'routine': routine,
        'schedules': schedules,
        'title': f'Schedule Routine: {routine.title}'
    }
    return render(request, 'routines/routine_schedule.html', context)


@login_required
def routine_progress(request, routine_id):
    """View progress for a routine"""
    routine = get_object_or_404(Routine, id=routine_id)
    user = request.user
    
    # Check permissions
    if user.role == 'child' and routine.child != user:
        messages.error(request, "You don't have permission to view this routine.")
        return redirect('routines:routine_list')
    elif user.role == 'parent':
        # Check if routine belongs to one of parent's children
        is_parent_of_child = user.parent_profile.children.filter(user=routine.child).exists()
        if not is_parent_of_child:
            messages.error(request, "You don't have permission to view this routine.")
            return redirect('routines:routine_list')
    elif user.role in ['therapist', 'teacher'] and routine.created_by != user:
        messages.error(request, "You don't have permission to view this routine.")
        return redirect('routines:routine_list')
    
    # Get completion data
    if user.role == 'child':
        children = [user]
    elif user.role == 'parent':
        children_profiles = user.parent_profile.children.all()
        children = [child_profile.user for child_profile in children_profiles]
    else:
        # Since routine is 1-to-1 with child now, there is only one child
        children = [routine.child]
    
    # Get completion statistics
    completion_stats = []
    for child in children:
        if child == routine.child:
            total_tasks = routine.tasks.count()
            completed_tasks = TaskCompletion.objects.filter(
                task__routine=routine,
                child=child
            ).count()
            
            completion_stats.append({
                'child': child,
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'completion_rate': round((completed_tasks / total_tasks * 100) if total_tasks > 0 else 0, 1)
            })
    
    context = {
        'routine': routine,
        'completion_stats': completion_stats,
        'user_role': user.role
    }
    return render(request, 'routines/routine_progress.html', context)

