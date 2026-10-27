from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.db.models import Q
import json
from .models import Drawing, DrawingSession
from .forms import DrawingForm
from django.db import models
from django.utils import timezone


@login_required
def drawing_dashboard(request):
    """Main drawing dashboard for children"""
    if request.user.role != 'child':
        messages.error(request, "Only children can access the drawing dashboard.")
        return redirect('home')
    
    drawings = Drawing.objects.filter(child=request.user).order_by('-updated_at')
    recent_drawings = drawings[:5]
    for d in recent_drawings:
        d.json_canvas_data = json.dumps(d.get_canvas_data()) if hasattr(d, 'get_canvas_data') else '{}'
    context = {
        'drawings': drawings,
        'recent_drawings': recent_drawings,
    }
    return render(request, 'drawing/dashboard.html', context)


@login_required
def drawing_canvas(request, drawing_id=None):
    """Main drawing canvas interface"""
    if request.user.role != 'child':
        messages.error(request, "Only children can access the drawing canvas.")
        return redirect('home')
    
    drawing = None
    if drawing_id:
        drawing = get_object_or_404(Drawing, id=drawing_id, child=request.user)
    
    context = {
        'drawing': drawing,
    }
    return render(request, 'drawing/canvas.html', context)


@login_required
def drawing_list(request):
    """List all drawings accessible to the user"""
    if request.user.role == 'child':
        drawings = Drawing.objects.filter(child=request.user)
    elif request.user.role == 'parent':
        children = request.user.parent_profile.children.all()
        child_users = [child.user for child in children]
        drawings = Drawing.objects.filter(
            child__in=child_users,
            shared_with_parents=True
        )
    elif request.user.role == 'therapist':
        children = request.user.therapist_profile.assigned_children.all()
        child_users = [child.user for child in children]
        drawings = Drawing.objects.filter(
            child__in=child_users,
            shared_with_therapists=True
        )
    elif request.user.role == 'teacher':
        children = request.user.teacher_profile.assigned_children.all()
        child_users = [child.user for child in children]
        drawings = Drawing.objects.filter(
            child__in=child_users,
            shared_with_teachers=True
        )
    else:
        drawings = Drawing.objects.none()
    
    drawings = drawings.order_by('-updated_at')
    for d in drawings:
        d.json_canvas_data = json.dumps(d.get_canvas_data()) if hasattr(d, 'get_canvas_data') else '{}'
    
    context = {
        'drawings': drawings,
    }
    return render(request, 'drawing/drawing_list.html', context)


@login_required
def drawing_detail(request, drawing_id):
    """View a specific drawing"""
    drawing = get_object_or_404(Drawing, id=drawing_id)
    
    if not drawing.can_be_viewed_by(request.user):
        messages.error(request, "You don't have permission to view this drawing.")
        return redirect('drawing:drawing_list')
    
    # Prepare JSON data for the template's preview canvas
    drawing.json_canvas_data = json.dumps(drawing.get_canvas_data())
    
    context = {
        'drawing': drawing,
    }
    return render(request, 'drawing/drawing_detail.html', context)


@method_decorator(csrf_exempt, name='dispatch')
class DrawingCreateView(CreateView):
    """Create a new drawing"""
    model = Drawing
    form_class = DrawingForm
    template_name = 'drawing/drawing_form.html'

    def get_success_url(self):
        return reverse_lazy('drawing:drawing_canvas_edit', kwargs={'drawing_id': self.object.id})
    
    def form_valid(self, form):
        form.instance.child = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, "Drawing created successfully!")
        return response
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.role != 'child':
            messages.error(request, "Only children can create drawings.")
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)


@method_decorator(csrf_exempt, name='dispatch')
class DrawingUpdateView(UpdateView):
    """Update drawing metadata"""
    model = Drawing
    form_class = DrawingForm
    template_name = 'drawing/drawing_form.html'
    success_url = reverse_lazy('drawing:drawing_dashboard')
    
    def get_queryset(self):
        return Drawing.objects.filter(child=self.request.user)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Drawing updated successfully!")
        return response


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def save_drawing_data(request, drawing_id):
    """Save canvas data via AJAX"""
    if request.user.role != 'child':
        return JsonResponse({'error': 'Only children can save drawings'}, status=403)
    
    try:
        drawing = get_object_or_404(Drawing, id=drawing_id, child=request.user)
        data = json.loads(request.body)
        
        # Update canvas data
        drawing.set_canvas_data(data.get('canvas_data', {}))
        drawing.canvas_width = data.get('width', 800)
        drawing.canvas_height = data.get('height', 600)
        drawing.is_completed = data.get('is_completed', False)
        drawing.save()
        
        # Update or create session
        session, created = DrawingSession.objects.get_or_create(
            drawing=drawing,
            child=request.user,
            ended_at__isnull=True
        )
        
        # Update session analytics
        session.strokes_count = data.get('strokes_count', 0)
        session.colors_used = data.get('colors_used', [])
        session.tools_used = data.get('tools_used', [])
        session.save()
        
        return JsonResponse({'success': True, 'message': 'Drawing saved successfully'})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def load_drawing_data(request, drawing_id):
    """Load canvas data via AJAX"""
    if request.user.role != 'child':
        return JsonResponse({'error': 'Only children can load drawings'}, status=403)
    
    try:
        drawing = get_object_or_404(Drawing, id=drawing_id, child=request.user)
        
        data = {
            'canvas_data': drawing.get_canvas_data(),
            'width': drawing.canvas_width,
            'height': drawing.canvas_height,
            'title': drawing.title,
            'is_completed': drawing.is_completed,
        }
        
        return JsonResponse(data)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def create_new_version(request, drawing_id):
    """Create a new version of a drawing"""
    if request.user.role != 'child':
        return JsonResponse({'error': 'Only children can create new versions'}, status=403)
    
    try:
        drawing = get_object_or_404(Drawing, id=drawing_id, child=request.user)
        new_drawing = drawing.create_new_version()
        
        return JsonResponse({
            'success': True,
            'new_drawing_id': new_drawing.id,
            'message': 'New version created successfully'
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def delete_drawing(request, drawing_id):
    """Delete a drawing"""
    if request.user.role != 'child':
        messages.error(request, "Only children can delete their drawings.")
        return redirect('drawing:drawing_list')
    
    drawing = get_object_or_404(Drawing, id=drawing_id, child=request.user)
    drawing.delete()
    messages.success(request, "Drawing deleted successfully!")
    return redirect('drawing:drawing_dashboard')


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def end_drawing_session(request, drawing_id):
    """End a drawing session"""
    if request.user.role != 'child':
        return JsonResponse({'error': 'Only children can end drawing sessions'}, status=403)
    
    try:
        drawing = get_object_or_404(Drawing, id=drawing_id, child=request.user)
        session = DrawingSession.objects.filter(
            drawing=drawing,
            child=request.user,
            ended_at__isnull=True
        ).first()
        
        if session:
            data = json.loads(request.body)
            session.end_session(data.get('duration_seconds'))
        
        return JsonResponse({'success': True})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def drawing_analytics(request):
    """View drawing analytics for therapists/parents/teachers"""
    if request.user.role == 'child':
        messages.error(request, "Children cannot view analytics.")
        return redirect('drawing:drawing_dashboard')
    
    # Get accessible children based on user role
    if request.user.role == 'parent':
        children = request.user.parent_profile.children.all()
    elif request.user.role == 'therapist':
        children = request.user.therapist_profile.assigned_children.all()
    elif request.user.role == 'teacher':
        children = request.user.teacher_profile.assigned_children.all()
    else:
        children = []
    
    # Get drawing statistics
    drawings = Drawing.objects.filter(child__in=children)
    sessions = DrawingSession.objects.filter(child__in=children)
    
    context = {
        'children': children,
        'total_drawings': drawings.count(),
        'total_sessions': sessions.count(),
        'avg_session_duration': sessions.aggregate(
            avg_duration=models.Avg('duration_seconds')
        )['avg_duration'] or 0,
    }
    
    return render(request, 'drawing/analytics.html', context)


@csrf_exempt
@login_required
def api_create_drawing(request):
    """API endpoint to create a new drawing via JSON POST and return the new drawing's ID."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    if request.user.role != 'child':
        return JsonResponse({'error': 'Only children can create drawings'}, status=403)
    try:
        data = json.loads(request.body)
        title = data.get('title', 'Untitled Drawing')
        canvas_data = data.get('canvas_data', {})
        width = data.get('width', 800)
        height = data.get('height', 600)
        is_completed = data.get('is_completed', False)
        shared_with_parents = data.get('shared_with_parents', True)
        shared_with_therapists = data.get('shared_with_therapists', True)
        shared_with_teachers = data.get('shared_with_teachers', True)
        
        drawing = Drawing.objects.create(
            title=title,
            child=request.user,
            canvas_data=canvas_data,
            canvas_width=width,
            canvas_height=height,
            is_completed=is_completed,
            shared_with_parents=shared_with_parents,
            shared_with_therapists=shared_with_therapists,
            shared_with_teachers=shared_with_teachers,
            created_at=timezone.now(),
            updated_at=timezone.now(),
        )
        return JsonResponse({'success': True, 'drawing_id': drawing.id})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
