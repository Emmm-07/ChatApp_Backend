from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class Messages(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_messages")
    message = models.TextField()
    timestamp =  models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"from {self.sender} to {self.recipient} "
        
