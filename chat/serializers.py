from rest_framework import serializers
from .models import Messages
from django.contrib.auth.models import User

class MessageSerializer(serializers.ModelSerializer):
    sender_fname = serializers.CharField(source='sender.first_name',read_only=True)
    class Meta:
        model = Messages
        fields = ["id", "message", "timestamp","recipient", "sender_fname"]
        

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','username','password','email','first_name','last_name', 'is_active']
        extra_kwargs = {'password': {'write_only': True}}  # Hide password from responses

