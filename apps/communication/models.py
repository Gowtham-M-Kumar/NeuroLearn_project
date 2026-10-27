from django.db import models

class AACCategory(models.Model):
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, blank=True, help_text="Material Icon name")
    color = models.CharField(max_length=20, default="#FFFFFF", help_text="Hex color code")
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name_plural = "AAC Categories"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

class AACSymbol(models.Model):
    category = models.ForeignKey(AACCategory, on_delete=models.CASCADE, related_name='symbols')
    word = models.CharField(max_length=100)
    image = models.ImageField(upload_to='aac_symbols/', blank=True, null=True)
    audio = models.FileField(upload_to='aac_audio/', blank=True, null=True)
    action_description = models.CharField(max_length=255, blank=True, help_text="Context sentence (e.g., 'Dog barks')")
    color_code = models.CharField(max_length=20, blank=True, help_text="Override category color")
    is_quick_need = models.BooleanField(default=False, help_text="Show in Zone 1 Quick Needs")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'word']

    def __str__(self):
        return self.word
