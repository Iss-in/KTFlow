import uuid
from django.db import models
from django.conf import settings

class KTSession(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='kt_sessions'
    )
    share_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Attachment(models.Model):
    FILE_TYPE_CHOICES = [
        ('audio', 'Audio'),
        ('video', 'Video'),
        ('pdf', 'PDF'),
        ('text', 'Text'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('done', 'Done'),
    ]


    id = models.AutoField(primary_key=True)
    session = models.ForeignKey(
        KTSession, on_delete=models.CASCADE, related_name='attachments'
    )
    file_type = models.CharField(max_length=10, choices=FILE_TYPE_CHOICES)
    file_url = models.URLField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    transcript = models.TextField(null=True, blank=True)
    summary = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file_type} for session {self.session.title}"
from django.db import models

# Create your models here.
