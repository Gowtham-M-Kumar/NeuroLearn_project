from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class Game(models.Model):
    """General game model"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class ColorMatchingGame(models.Model):
    """Color matching game with different levels"""
    level = models.IntegerField(unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    time_limit = models.IntegerField(help_text="Time limit in seconds")
    points_per_match = models.IntegerField(default=10)
    required_matches = models.IntegerField(help_text="Number of matches required to complete level")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['level']

    def __str__(self):
        return f"{self.name} - Level {self.level}"

class Color(models.Model):
    """Color model for the matching game"""
    name = models.CharField(max_length=50, unique=True)
    hex_code = models.CharField(max_length=7, help_text="Hex color code (e.g., #FF0000)")
    category = models.CharField(max_length=20, choices=[
        ('primary', 'Primary'),
        ('secondary', 'Secondary'),
        ('warm', 'Warm'),
        ('cool', 'Cool'),
        ('neutral', 'Neutral'),
    ])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class ColorMatchingLevel(models.Model):
    """Configuration for each level of the color matching game"""
    game = models.OneToOneField(ColorMatchingGame, on_delete=models.CASCADE, related_name='level_config')
    colors = models.ManyToManyField(Color, related_name='levels')
    grid_size = models.IntegerField(default=4, help_text="Grid size (e.g., 4 for 4x4 grid)")
    shuffle_count = models.IntegerField(default=3, help_text="Number of times to shuffle cards")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Level {self.game.level} Configuration"

class Animal(models.Model):
    """Animal model for the matching game"""
    name = models.CharField(max_length=100, unique=True)
    image = models.ImageField(upload_to='games/animals/')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class AnimalMatchingLevel(models.Model):
    """Configuration for each level of the animal matching game"""
    level = models.IntegerField(unique=True)
    name = models.CharField(max_length=100)
    animal_count = models.IntegerField(help_text="Number of animals to match in this level")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['level']

    def __str__(self):
        return f"{self.name} - Level {self.level}"

class GameSession(models.Model):
    """Track individual game sessions for children"""
    child = models.ForeignKey(User, on_delete=models.CASCADE, related_name='game_sessions')
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    level = models.IntegerField()
    score = models.IntegerField(default=0)
    time_taken = models.IntegerField(help_text="Time taken in seconds", default=0)
    completed = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.child.username} - {self.game.name} Level {self.level}"

class ColorMatchingSession(models.Model):
    """Specific session data for color matching game"""
    game_session = models.OneToOneField(GameSession, on_delete=models.CASCADE, related_name='color_matching_data')
    matches_found = models.IntegerField(default=0)
    total_attempts = models.IntegerField(default=0)
    accuracy = models.FloatField(default=0.0, help_text="Accuracy percentage")

    def __str__(self):
        return f"Color Matching Session - {self.game_session}"

class AnimalMatchingSession(models.Model):
    """Specific session data for animal matching game"""
    game_session = models.OneToOneField(GameSession, on_delete=models.CASCADE, related_name='animal_matching_data')
    matches_found = models.IntegerField(default=0)
    total_attempts = models.IntegerField(default=0)
    
    def __str__(self):
        return f"Animal Matching Session - {self.game_session}"

class GameProgress(models.Model):
    """Track overall progress for each child in each game"""
    child = models.ForeignKey(User, on_delete=models.CASCADE, related_name='game_progress')
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='progress')
    highest_level_completed = models.IntegerField(default=0)
    total_score = models.IntegerField(default=0)
    total_sessions = models.IntegerField(default=0)
    average_accuracy = models.FloatField(default=0.0)
    last_played = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['child', 'game']
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.child.username} - {self.game.name} Progress"
