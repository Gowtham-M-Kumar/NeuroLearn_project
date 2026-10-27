from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import Drawing, DrawingSession
from apps.users.models import ParentProfile
import json

User = get_user_model()


class DrawingModelTest(TestCase):
    def setUp(self):
        # Create test users
        self.child_user = User.objects.create_user(
            email='child@test.com',
            username='childtest',
            password='testpass123',
            role='child',
            first_name='Test',
            last_name='Child'
        )
        
        self.parent_user = User.objects.create_user(
            email='parent@test.com',
            username='parenttest',
            password='testpass123',
            role='parent',
            first_name='Test',
            last_name='Parent'
        )
        ParentProfile.objects.create(user=self.parent_user)
    
    def test_drawing_creation(self):
        """Test creating a drawing"""
        drawing = Drawing.objects.create(
            title="Test Drawing",
            child=self.child_user,
            canvas_data={'strokes': []},
            canvas_width=800,
            canvas_height=600
        )
        
        self.assertEqual(drawing.title, "Test Drawing")
        self.assertEqual(drawing.child, self.child_user)
        self.assertEqual(drawing.canvas_width, 800)
        self.assertEqual(drawing.canvas_height, 600)
        self.assertFalse(drawing.is_completed)
    
    def test_drawing_version_control(self):
        """Test drawing version control"""
        # Create original drawing
        original = Drawing.objects.create(
            title="Original Drawing",
            child=self.child_user,
            canvas_data={'strokes': [{'color': '#000000', 'size': 2}]}
        )
        
        # Create new version
        new_version = original.create_new_version()
        
        self.assertEqual(new_version.parent_drawing, original)
        self.assertEqual(new_version.version_number, 2)
        self.assertEqual(new_version.title, original.title)
    
    def test_drawing_permissions(self):
        """Test drawing permission system"""
        drawing = Drawing.objects.create(
            title="Test Drawing",
            child=self.child_user,
            shared_with_parents=True,
            shared_with_therapists=False,
            shared_with_teachers=True
        )
        
        # Child can always view their own drawing
        self.assertTrue(drawing.can_be_viewed_by(self.child_user))
        
        # Parent can view if shared
        self.assertTrue(drawing.can_be_viewed_by(self.parent_user))
        
        # Update sharing settings
        drawing.shared_with_parents = False
        drawing.save()
        
        # Parent can no longer view
        self.assertFalse(drawing.can_be_viewed_by(self.parent_user))


class DrawingViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create test users
        self.child_user = User.objects.create_user(
            email='child@test.com',
            username='childtest',
            password='testpass123',
            role='child',
            first_name='Test',
            last_name='Child'
        )
        
        self.parent_user = User.objects.create_user(
            email='parent@test.com',
            username='parenttest',
            password='testpass123',
            role='parent',
            first_name='Test',
            last_name='Parent'
        )
        
        # Create test drawing
        self.drawing = Drawing.objects.create(
            title="Test Drawing",
            child=self.child_user,
            canvas_data={'strokes': [{'color': '#000000', 'size': 2}]}
        )
    
    def test_drawing_dashboard_access(self):
        """Test drawing dashboard access"""
        # Login as child
        self.client.login(email='child@test.com', password='testpass123')
        
        # Access dashboard
        response = self.client.get(reverse('drawing:drawing_dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Login as parent (should redirect)
        self.client.login(email='parent@test.com', password='testpass123')
        response = self.client.get(reverse('drawing:drawing_dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirect
    
    def test_drawing_canvas_access(self):
        """Test drawing canvas access"""
        # Login as child
        self.client.login(email='child@test.com', password='testpass123')
        
        # Access canvas
        response = self.client.get(reverse('drawing:drawing_canvas'))
        self.assertEqual(response.status_code, 200)
        
        # Access specific drawing canvas
        response = self.client.get(reverse('drawing:drawing_canvas_edit', args=[self.drawing.id]))
        self.assertEqual(response.status_code, 200)
    
    def test_drawing_list_access(self):
        """Test drawing list access"""
        # Login as child
        self.client.login(email='child@test.com', password='testpass123')
        
        response = self.client.get(reverse('drawing:drawing_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Drawing")
    
    def test_drawing_detail_access(self):
        """Test drawing detail access"""
        # Login as child
        self.client.login(email='child@test.com', password='testpass123')
        
        response = self.client.get(reverse('drawing:drawing_detail', args=[self.drawing.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Drawing")
    
    def test_save_drawing_data(self):
        """Test saving drawing data via AJAX"""
        self.client.login(email='child@test.com', password='testpass123')
        
        data = {
            'canvas_data': {'strokes': [{'color': '#ff0000', 'size': 5}]},
            'width': 800,
            'height': 600,
            'is_completed': True,
            'strokes_count': 1,
            'colors_used': ['#ff0000'],
            'tools_used': ['brush']
        }
        
        response = self.client.post(
            reverse('drawing:save_drawing_data', args=[self.drawing.id]),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertTrue(result['success'])
        
        # Check if drawing was updated
        self.drawing.refresh_from_db()
        self.assertTrue(self.drawing.is_completed)
    
    def test_load_drawing_data(self):
        """Test loading drawing data via AJAX"""
        self.client.login(email='child@test.com', password='testpass123')
        
        response = self.client.get(reverse('drawing:load_drawing_data', args=[self.drawing.id]))
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(data['title'], "Test Drawing")
        self.assertIn('canvas_data', data)
    
    def test_create_new_version(self):
        """Test creating new version"""
        self.client.login(email='child@test.com', password='testpass123')
        
        response = self.client.post(reverse('drawing:create_new_version', args=[self.drawing.id]))
        self.assertEqual(response.status_code, 200)
        
        result = json.loads(response.content)
        self.assertTrue(result['success'])
        self.assertIn('new_drawing_id', result)
    
    def test_delete_drawing(self):
        """Test deleting a drawing"""
        self.client.login(email='child@test.com', password='testpass123')
        
        response = self.client.post(reverse('drawing:drawing_delete', args=[self.drawing.id]))
        self.assertEqual(response.status_code, 302)  # Redirect after delete
        
        # Check if drawing was deleted
        self.assertFalse(Drawing.objects.filter(id=self.drawing.id).exists())


class DrawingSessionTest(TestCase):
    def setUp(self):
        self.child_user = User.objects.create_user(
            email='child@test.com',
            username='childtest',
            password='testpass123',
            role='child'
        )
        
        self.drawing = Drawing.objects.create(
            title="Test Drawing",
            child=self.child_user
        )
    
    def test_session_creation(self):
        """Test creating a drawing session"""
        session = DrawingSession.objects.create(
            drawing=self.drawing,
            child=self.child_user,
            strokes_count=10,
            colors_used=['#ff0000', '#00ff00'],
            tools_used=['brush', 'eraser']
        )
        
        self.assertEqual(session.drawing, self.drawing)
        self.assertEqual(session.child, self.child_user)
        self.assertEqual(session.strokes_count, 10)
        self.assertEqual(len(session.colors_used), 2)
        self.assertEqual(len(session.tools_used), 2)
    
    def test_session_ending(self):
        """Test ending a drawing session"""
        session = DrawingSession.objects.create(
            drawing=self.drawing,
            child=self.child_user
        )
        
        self.assertIsNone(session.ended_at)
        self.assertEqual(session.duration_seconds, 0)
        
        # End session
        session.end_session(120)  # 2 minutes
        
        self.assertIsNotNone(session.ended_at)
        self.assertEqual(session.duration_seconds, 120)
