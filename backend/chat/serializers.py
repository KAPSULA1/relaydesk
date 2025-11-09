from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Room, Message


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm']
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password": "Passwords must match"})
        return data
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered")
        return value
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


class MessageSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Message
        fields = ['id', 'room', 'user', 'username', 'content', 'created_at', 'updated_at', 'is_edited']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'is_edited']


class MessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['content']
    
    def validate_content(self, value):
        if not value.strip():
            raise serializers.ValidationError("Message cannot be empty")
        if len(value) > 5000:
            raise serializers.ValidationError("Message too long")
        return value


class RoomSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    message_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Room
        fields = ['id', 'name', 'slug', 'description', 'created_by', 'created_at', 'updated_at', 'is_active', 'message_count']
        read_only_fields = ['id', 'slug', 'created_by', 'created_at', 'updated_at']


class RoomCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ['name', 'description']
    
    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Room name cannot be empty")
        if len(value) < 3:
            raise serializers.ValidationError("Room name too short")
        if Room.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("Room already exists")
        return value
