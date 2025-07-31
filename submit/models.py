from django.db import models

# Create your models here.


class CodeSubmission(models.Model):
    LANGUAGE_CHOICES = [
        ('cpp', 'C++'),
        ('py', 'Python'),
    ]
    
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES)
    code = models.TextField()
    input_data = models.TextField(blank=True)
    output_data = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.language} submission at {self.submitted_at}"
