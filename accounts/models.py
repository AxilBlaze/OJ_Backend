import uuid
from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Problem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()  # Or store file path if using files
    difficulty = models.CharField(max_length=50, choices=[('Easy', 'Easy'), ('Medium', 'Medium'), ('Hard', 'Hard')], default='Easy')
    tags = models.CharField(max_length=255, blank=True, null=True) # Comma-separated tags
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    admin_verified_code = models.TextField(blank=True, null=True)
    problem_file = models.CharField(max_length=255, blank=True, null=True)  # Path to problem file

    def __str__(self):
        return self.title

class TestCase(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    input_file = models.CharField(max_length=255)   # Path to input file
    output_file = models.CharField(max_length=255)  # Path to output file

    def __str__(self):
        return f"TestCase for {self.problem.title}"

class Submission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    code = models.TextField()
    language = models.CharField(max_length=50)
    submitted_at = models.DateTimeField(auto_now_add=True)
    verdict = models.CharField(max_length=50)

    def __str__(self):
        return f"Submission by {self.user.username} for {self.problem.title}"
