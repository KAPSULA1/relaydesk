"""
Chat Application Views
REST API endpoints for rooms, messages, and user management
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from django.db.models import Count
from .models import Room, Message
from .serializers import (
    RoomSerializer, RoomCreateSerializer, MessageSerializer,
    MessageCreateSerializer, UserSerializer, UserRegistrationSerializer
)
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Health check endpoint for monitoring"""
    return Response({
        'status': 'healthy',
        'message': 'RelayDesk API is running'
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """
    User registration endpoint
    Creates new user and returns JWT tokens
    """
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        
        logger.info(f"New user registered: {user.username}")
        
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    """Get current authenticated user details"""
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


class RoomViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Room CRUD operations
    Handles listing, creating, retrieving, updating rooms
    """
    queryset = Room.objects.filter(is_active=True).annotate(
        message_count=Count('messages')
    )
    permission_classes = [IsAuthenticated]
    lookup_field = 'slug'
    ordering = ['-created_at']  # ✅ THIS FIXES THE ERROR!
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return RoomCreateSerializer
        return RoomSerializer
    
    def perform_create(self, serializer):
        """Set current user as room creator"""
        room = serializer.save(created_by=self.request.user)
        logger.info(f"Room created: {room.name} by {self.request.user.username}")
    
    @action(detail=True, methods=['get'])
    def messages(self, request, slug=None):
        """
        Get paginated messages for a specific room
        Supports cursor-based pagination
        """
        room = self.get_object()
        messages = Message.objects.filter(room=room).select_related('user')
        
        # Apply pagination
        page = self.paginate_queryset(messages)
        if page is not None:
            serializer = MessageSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)


class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Message operations
    Handles creating and listing messages
    """
    queryset = Message.objects.all().select_related('user', 'room')
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return MessageCreateSerializer
        return MessageSerializer
    
    def get_queryset(self):
        """Filter messages by room if room_slug is provided"""
        queryset = super().get_queryset()
        room_slug = self.request.query_params.get('room_slug')
        
        if room_slug:
            queryset = queryset.filter(room__slug=room_slug)
        
        return queryset
    
    def perform_create(self, serializer):
        """Create message with current user and specified room"""
        room_slug = self.request.data.get('room_slug')
        room = get_object_or_404(Room, slug=room_slug)
        
        message = serializer.save(user=self.request.user, room=room)
        logger.info(f"Message created in {room.name} by {self.request.user.username}")


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def room_presence(request, room_slug):
    """
    Get list of users currently online in a room
    Uses Redis cache for presence tracking
    """
    cache_key = f"room_presence:{room_slug}"
    online_users = cache.get(cache_key, [])
    
    return Response({
        'room_slug': room_slug,
        'online_users': online_users,
        'count': len(online_users)
    })
