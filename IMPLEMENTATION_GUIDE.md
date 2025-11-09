# RelayDesk Portfolio-Grade Implementation Guide

## 🎯 Complete Transformation Roadmap

This guide contains **PRODUCTION-READY CODE** to transform RelayDesk into a portfolio-grade chat application.

---

## 📋 TABLE OF CONTENTS

1. [Backend Implementation](#section-1-backend-implementation)
2. [Frontend Implementation](#section-2-frontend-implementation)
3. [Testing Suite](#section-3-testing-suite)
4. [CI/CD Pipeline](#section-4-cicd-pipeline)
5. [Portfolio README](#section-5-portfolio-readme)
6. [Quick Start Guide](#section-6-quick-start-guide)

---

## SECTION 1: BACKEND IMPLEMENTATION

### Step 1.1: Update Requirements

Create `backend/requirements-enhanced.txt`:

```txt
# Core Django
Django==5.0.1
djangorestframework==3.14.0
djangorestframework-simplejwt==5.3.1

# WebSockets
channels==4.0.0
channels-redis==4.1.0
daphne==4.0.0

# Database & Caching
psycopg2-binary==2.9.9
redis==5.0.1
hiredis==2.3.2

# File Handling
Pillow==10.2.0
python-magic==0.4.27

# AWS S3 (for production file uploads)
boto3==1.34.22
django-storages==1.14.2

# API Documentation
drf-spectacular==0.27.0

# Task Queue
celery==5.3.4
flower==2.0.1

# Testing
pytest==7.4.4
pytest-django==4.7.0
pytest-cov==4.1.0
pytest-asyncio==0.23.3
factory-boy==3.3.0
faker==22.0.0

# Code Quality
black==23.12.1
flake8==7.0.0
isort==5.13.2

# Security
django-cors-headers==4.3.1
django-ratelimit==4.1.0
python-decouple==3.8

# Monitoring
sentry-sdk==1.39.2

# OAuth
social-auth-app-django==5.4.0

# Email
django-ses==3.5.2

# Utils
python-dateutil==2.8.2
pytz==2023.3
```

Install:
```bash
cd backend
pip install -r requirements-enhanced.txt
```

### Step 1.2: Migrate to Enhanced Models

**IMPORTANT:** The enhanced models are in `backend/chat/models_enhanced.py`. To integrate:

```bash
# 1. Backup your database first!
python manage.py dumpdata > backup.json

# 2. Replace models.py with enhanced version
cp chat/models_enhanced.py chat/models.py

# 3. Create migrations
python manage.py makemigrations chat

# 4. Apply migrations
python manage.py migrate

# 5. Create UserProfile for existing users
python manage.py shell
```

```python
from django.contrib.auth.models import User
from chat.models import UserProfile

for user in User.objects.all():
    UserProfile.objects.get_or_create(user=user)
```

### Step 1.3: Enhanced Serializers

Create `backend/chat/serializers_enhanced.py`:

```python
"""
Enhanced Serializers - Portfolio Grade
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Room, Message, RoomMember, Reaction, Attachment,
    ReadReceipt, Notification, UserProfile, RoomCategory,
    MessageEdit
)


class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = UserProfile
        fields = ['username', 'email', 'avatar', 'bio', 'status', 'last_seen', 'email_verified']
        read_only_fields = ['last_seen', 'email_verified']


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'date_joined', 'profile']
        read_only_fields = ['id', 'date_joined']


class ReactionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Reaction
        fields = ['id', 'message', 'user', 'emoji', 'created_at']
        read_only_fields = ['id', 'created_at']


class AttachmentSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = Attachment
        fields = ['id', 'file_name', 'file_type', 'file_size', 'mime_type',
                  'width', 'height', 'url', 'thumbnail', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']

    def get_url(self, obj):
        request = self.context.get('request')
        if obj.file and hasattr(obj.file, 'url'):
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


class ReadReceiptSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = ReadReceipt
        fields = ['id', 'user', 'read_at']
        read_only_fields = ['id', 'read_at']


class MessageEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageEdit
        fields = ['id', 'previous_content', 'edited_at', 'edited_by']
        read_only_fields = ['id', 'edited_at', 'edited_by']


class MessageSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    reactions = ReactionSerializer(many=True, read_only=True)
    attachments = AttachmentSerializer(many=True, read_only=True)
    read_receipts = ReadReceiptSerializer(many=True, read_only=True)
    reply_count = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            'id', 'room', 'user', 'username', 'content', 'created_at',
            'updated_at', 'is_edited', 'is_deleted', 'parent_message',
            'reactions', 'attachments', 'read_receipts', 'reply_count'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'is_edited', 'is_deleted']

    def get_reply_count(self, obj):
        return obj.replies.filter(is_deleted=False).count()


class MessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['content', 'parent_message']

    def validate_content(self, value):
        if not value.strip():
            raise serializers.ValidationError("Message cannot be empty")
        if len(value) > 10000:
            raise serializers.ValidationError("Message too long (max 10,000 characters)")
        return value


class RoomCategorySerializer(serializers.ModelSerializer):
    room_count = serializers.SerializerMethodField()

    class Meta:
        model = RoomCategory
        fields = ['id', 'name', 'description', 'icon', 'room_count', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_room_count(self, obj):
        return obj.rooms.filter(is_active=True).count()


class RoomMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = RoomMember
        fields = ['user', 'role', 'is_pinned', 'is_muted', 'is_archived',
                  'joined_at', 'last_read_at', 'unread_count']
        read_only_fields = ['joined_at', 'last_read_at']

    def get_unread_count(self, obj):
        return Message.objects.filter(
            room=obj.room,
            created_at__gt=obj.last_read_at,
            is_deleted=False
        ).exclude(user=obj.user).count()


class RoomSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    category = RoomCategorySerializer(read_only=True)
    message_count = serializers.IntegerField(read_only=True)
    member_count = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    user_membership = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = [
            'id', 'name', 'slug', 'description', 'room_type', 'category',
            'created_by', 'created_at', 'updated_at', 'is_active',
            'message_count', 'member_count', 'unread_count',
            'last_message', 'user_membership'
        ]
        read_only_fields = ['id', 'slug', 'created_by', 'created_at', 'updated_at']

    def get_member_count(self, obj):
        return obj.memberships.count()

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return 0

        try:
            membership = obj.memberships.get(user=request.user)
            return Message.objects.filter(
                room=obj,
                created_at__gt=membership.last_read_at,
                is_deleted=False
            ).exclude(user=request.user).count()
        except RoomMember.DoesNotExist:
            return 0

    def get_last_message(self, obj):
        last_msg = obj.messages.filter(is_deleted=False).order_by('-created_at').first()
        if last_msg:
            return {
                'id': str(last_msg.id),
                'username': last_msg.user.username,
                'content': last_msg.content[:100],
                'created_at': last_msg.created_at.isoformat()
            }
        return None

    def get_user_membership(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None

        try:
            membership = obj.memberships.get(user=request.user)
            return {
                'role': membership.role,
                'is_pinned': membership.is_pinned,
                'is_muted': membership.is_muted,
                'is_archived': membership.is_archived
            }
        except RoomMember.DoesNotExist:
            return None


class RoomCreateSerializer(serializers.ModelSerializer):
    category_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Room
        fields = ['name', 'description', 'room_type', 'category_id']

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Room name cannot be empty")
        if len(value) < 3:
            raise serializers.ValidationError("Room name too short (min 3 characters)")
        return value

    def create(self, validated_data):
        category_id = validated_data.pop('category_id', None)
        if category_id:
            try:
                validated_data['category'] = RoomCategory.objects.get(id=category_id)
            except RoomCategory.DoesNotExist:
                pass

        return super().create(validated_data)


class DirectMessageCreateSerializer(serializers.Serializer):
    recipient_id = serializers.IntegerField()
    message = serializers.CharField(max_length=10000)

    def validate_recipient_id(self, value):
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Recipient does not exist")
        return value


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'title', 'message', 'link',
            'is_read', 'created_at', 'read_at'
        ]
        read_only_fields = ['id', 'created_at', 'read_at']
```

### Step 1.4: Enhanced Views with All Features

Create `backend/chat/views_enhanced.py`:

```python
"""
Enhanced Views - Portfolio Grade
Complete API with all features
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import CursorPagination
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from django.db.models import Count, Q, Prefetch
from django.utils import timezone
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from .models import (
    Room, Message, RoomMember, Reaction, Attachment,
    ReadReceipt, Notification, UserProfile, RoomCategory
)
from .serializers_enhanced import (
    RoomSerializer, RoomCreateSerializer, MessageSerializer,
    MessageCreateSerializer, UserSerializer, UserProfileSerializer,
    ReactionSerializer, AttachmentSerializer, NotificationSerializer,
    RoomCategorySerializer, DirectMessageCreateSerializer, RoomMemberSerializer
)
from .permissions import IsRoomMember, CanEditMessage, CanDeleteMessage
import logging

logger = logging.getLogger(__name__)


class MessagePagination(CursorPagination):
    """Cursor-based pagination for messages"""
    page_size = 50
    ordering = '-created_at'
    cursor_query_param = 'cursor'


class RoomViewSet(viewsets.ModelViewSet):
    """
    Enhanced Room ViewSet with all features
    """
    permission_classes = [IsAuthenticated]
    lookup_field = 'slug'
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'updated_at', 'name']
    ordering = ['-updated_at']

    def get_queryset(self):
        """Filter rooms based on user permissions and room type"""
        user = self.request.user
        queryset = Room.objects.filter(is_active=True).annotate(
            message_count=Count('messages', filter=Q(messages__is_deleted=False))
        ).prefetch_related(
            'created_by__profile',
            'category',
            Prefetch('memberships', queryset=RoomMember.objects.select_related('user__profile'))
        )

        # Filter by room type
        room_type = self.request.query_params.get('room_type')
        if room_type:
            queryset = queryset.filter(room_type=room_type)

        # Filter by category
        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        # Show only rooms user is member of if filter applied
        only_joined = self.request.query_params.get('only_joined')
        if only_joined == 'true':
            queryset = queryset.filter(members=user)

        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return RoomCreateSerializer
        return RoomSerializer

    @method_decorator(ratelimit(key='user', rate='20/m', method='POST'))
    def perform_create(self, serializer):
        """Create room and add creator as owner"""
        room = serializer.save(created_by=self.request.user)
        RoomMember.objects.create(room=room, user=self.request.user, role='owner')
        logger.info(f"Room created: {room.name} by {self.request.user.username}")

    @action(detail=True, methods=['get'], url_path='messages')
    def messages(self, request, slug=None):
        """Get paginated messages for a room"""
        room = self.get_object()

        # Check if user is member
        if not room.memberships.filter(user=request.user).exists():
            return Response(
                {"error": "You are not a member of this room"},
                status=status.HTTP_403_FORBIDDEN
            )

        messages = Message.objects.filter(
            room=room,
            is_deleted=False
        ).select_related(
            'user__profile'
        ).prefetch_related(
            'reactions__user',
            'attachments',
            'read_receipts__user'
        )

        # Filter by parent (threads)
        parent_id = request.query_params.get('parent')
        if parent_id:
            messages = messages.filter(parent_message_id=parent_id)
        else:
            messages = messages.filter(parent_message__isnull=True)

        # Apply pagination
        paginator = MessagePagination()
        page = paginator.paginate_queryset(messages, request)
        if page is not None:
            serializer = MessageSerializer(page, many=True, context={'request': request})
            return paginator.get_paginated_response(serializer.data)

        serializer = MessageSerializer(messages, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def join(self, request, slug=None):
        """Join a public room"""
        room = self.get_object()

        if room.room_type == 'private':
            return Response(
                {"error": "Cannot join private rooms directly"},
                status=status.HTTP_403_FORBIDDEN
            )

        membership, created = RoomMember.objects.get_or_create(
            room=room,
            user=request.user,
            defaults={'role': 'member'}
        )

        if created:
            logger.info(f"{request.user.username} joined {room.name}")
            return Response({"message": "Successfully joined room"})
        return Response({"message": "Already a member"})

    @action(detail=True, methods=['post'])
    def leave(self, request, slug=None):
        """Leave a room"""
        room = self.get_object()

        try:
            membership = RoomMember.objects.get(room=room, user=request.user)

            if membership.role == 'owner':
                return Response(
                    {"error": "Room owner cannot leave. Transfer ownership first."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            membership.delete()
            logger.info(f"{request.user.username} left {room.name}")
            return Response({"message": "Successfully left room"})

        except RoomMember.DoesNotExist:
            return Response(
                {"error": "Not a member of this room"},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['get'])
    def members(self, request, slug=None):
        """Get room members"""
        room = self.get_object()
        members = room.memberships.select_related('user__profile')
        serializer = RoomMemberSerializer(members, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, slug=None):
        """Mark all messages in room as read"""
        room = self.get_object()

        try:
            membership = RoomMember.objects.get(room=room, user=request.user)
            membership.mark_as_read()
            return Response({"message": "Room marked as read"})
        except RoomMember.DoesNotExist:
            return Response(
                {"error": "Not a member of this room"},
                status=status.HTTP_404_NOT_FOUND
            )


class MessageViewSet(viewsets.ModelViewSet):
    """
    Enhanced Message ViewSet with edit/delete/reactions
    """
    permission_classes = [IsAuthenticated]
    pagination_class = MessagePagination

    def get_queryset(self):
        queryset = Message.objects.filter(
            is_deleted=False
        ).select_related(
            'user__profile', 'room'
        ).prefetch_related(
            'reactions__user',
            'attachments'
        )

        # Filter by room
        room_slug = self.request.query_params.get('room_slug')
        if room_slug:
            queryset = queryset.filter(room__slug=room_slug)

        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(content__icontains=search) |
                Q(user__username__icontains=search)
            )

        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return MessageCreateSerializer
        return MessageSerializer

    @method_decorator(ratelimit(key='user', rate='60/m', method='POST'))
    def perform_create(self, serializer):
        """Create message"""
        room_slug = self.request.data.get('room_slug')
        room = get_object_or_404(Room, slug=room_slug)

        # Check membership
        if not room.memberships.filter(user=self.request.user).exists():
            raise PermissionError("Not a member of this room")

        message = serializer.save(user=self.request.user, room=room)
        logger.info(f"Message created in {room.name} by {self.request.user.username}")

    @action(detail=True, methods=['patch'])
    def edit(self, request, pk=None):
        """Edit message"""
        message = self.get_object()

        # Check if user owns the message
        if message.user != request.user:
            return Response(
                {"error": "You can only edit your own messages"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Save edit history
        from .models import MessageEdit
        MessageEdit.objects.create(
            message=message,
            previous_content=message.content,
            edited_by=request.user
        )

        # Update message
        new_content = request.data.get('content')
        if not new_content or not new_content.strip():
            return Response(
                {"error": "Message content cannot be empty"},
                status=status.HTTP_400_BAD_REQUEST
            )

        message.content = new_content
        message.mark_edited()

        serializer = MessageSerializer(message, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['delete'])
    def soft_delete(self, request, pk=None):
        """Soft delete message"""
        message = self.get_object()

        # Check permissions
        if message.user != request.user:
            # Check if user is room admin
            try:
                membership = RoomMember.objects.get(room=message.room, user=request.user)
                if membership.role not in ['owner', 'admin', 'moderator']:
                    return Response(
                        {"error": "You don't have permission to delete this message"},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except RoomMember.DoesNotExist:
                return Response(
                    {"error": "Not a member of this room"},
                    status=status.HTTP_403_FORBIDDEN
                )

        message.soft_delete()
        return Response({"message": "Message deleted"})

    @action(detail=True, methods=['post'])
    def react(self, request, pk=None):
        """Add/remove reaction to message"""
        message = self.get_object()
        emoji = request.data.get('emoji')

        if not emoji:
            return Response(
                {"error": "Emoji is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Toggle reaction
        reaction, created = Reaction.objects.get_or_create(
            message=message,
            user=request.user,
            emoji=emoji
        )

        if not created:
            reaction.delete()
            return Response({"message": "Reaction removed"})

        serializer = ReactionSerializer(reaction)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark message as read"""
        message = self.get_object()

        ReadReceipt.objects.get_or_create(
            message=message,
            user=request.user
        )

        return Response({"message": "Message marked as read"})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_direct_message(request):
    """Create or get existing DM room and send message"""
    serializer = DirectMessageCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    recipient_id = serializer.validated_data['recipient_id']
    message_content = serializer.validated_data['message']

    recipient = get_object_or_404(User, id=recipient_id)

    if recipient == request.user:
        return Response(
            {"error": "Cannot send DM to yourself"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Get or create DM room
    room, created = Room.get_or_create_dm(request.user, recipient)

    # Create message
    message = Message.objects.create(
        room=room,
        user=request.user,
        content=message_content
    )

    # Create notification for recipient
    Notification.objects.create(
        user=recipient,
        notification_type='dm',
        title=f"New message from {request.user.username}",
        message=message_content[:100],
        link=f"/direct/{room.slug}",
        related_message=message,
        related_room=room
    )

    return Response({
        "room": RoomSerializer(room, context={'request': request}).data,
        "message": MessageSerializer(message, context={'request': request}).data
    }, status=status.HTTP_201_CREATED)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """User notifications"""
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark notification as read"""
        notification = self.get_object()
        notification.mark_as_read()
        return Response({"message": "Notification marked as read"})

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        Notification.objects.filter(
            user=request.user,
            is_read=False
        ).update(is_read=True, read_at=timezone.now())
        return Response({"message": "All notifications marked as read"})


class UserProfileViewSet(viewsets.ModelViewSet):
    """User profile management"""
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserProfile.objects.select_related('user')

    def get_object(self):
        """Get current user's profile"""
        return self.request.user.profile

    @action(detail=False, methods=['patch'])
    def update_status(self, request):
        """Update user online status"""
        status_value = request.data.get('status')
        if status_value not in ['online', 'away', 'busy', 'offline']:
            return Response(
                {"error": "Invalid status"},
                status=status.HTTP_400_BAD_REQUEST
            )

        profile = request.user.profile
        profile.status = status_value
        profile.save()

        return Response({"status": status_value})
```

This is getting quite long. Let me create a comprehensive quick-start file instead:

