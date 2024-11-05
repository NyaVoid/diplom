from django.db import models
from django.contrib.auth.models import User

class ImageFeed(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='uploads/')
    processed_image = models.ImageField(upload_to='processed_images/', null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ImageFeed {self.id} by {self.user.username}"