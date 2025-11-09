"""
Enhanced Chat Application Models - Portfolio Grade
Complete models with all professional features
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from django.db.models import Q
import uuid


class UserProfile(models.Model):
    """
    Extended user profile with avatar and status
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('online', 'Online'),
            ('away', 'Away'),
            ('busy', 'Busy'),
            ('offline', 'Offline'),
        ],
        default='offline'
    )
    last_seen = models.DateTimeField(auto_now=True)
    email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['-last_seen']),
        ]

    def __str__(self):
        return f"{self.user.username}'s profile"


class RoomCategory(models.Model):
    """
    Categories for organizing rooms
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='📁')  # Emoji or icon class
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Room Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Room(models.Model):
    """
    Enhanced Chat Room Model with categories and permissions
    """
    ROOM_TYPES = [
        ('public', 'Public'),
        ('private', 'Private'),
        ('direct', 'Direct Message'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES, default='public')
    category = models.ForeignKey(
        RoomCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rooms'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_rooms'
    )
    members = models.ManyToManyField(
        User,
        through='RoomMember',
        related_name='joined_rooms'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    # Direct message specific fields
    dm_participants = models.ManyToManyField(
        User,
        related_name='dm_rooms',
        blank=True
    )

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['-updated_at']),
            models.Index(fields=['room_type', '-updated_at']),
        ]
        constraints = [
            models.CheckConstraint(
                check=(
                    Q(room_type='direct', name__isnull=False) |
                    ~Q(room_type='direct')
                ),
                name='direct_rooms_must_have_name'
            )
        ]

    def save(self, *args, **kwargs):
        """Generate slug from name if not provided"""
        if not self.slug:
            base_slug = slugify(self.name) if self.name else str(uuid.uuid4())[:8]
            slug = base_slug
            counter = 1
            while Room.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.get_room_type_display()})"

    @classmethod
    def get_or_create_dm(cls, user1, user2):
        """Get existing DM room or create new one between two users"""
        # Check if DM already exists
        dm_rooms = cls.objects.filter(
            room_type='direct',
            dm_participants=user1
        ).filter(dm_participants=user2)

        if dm_rooms.exists():
            return dm_rooms.first(), False

        # Create new DM room
        room = cls.objects.create(
            name=f"DM: {user1.username} & {user2.username}",
            room_type='direct',
            created_by=user1,
            is_active=True
        )
        room.dm_participants.add(user1, user2)

        # Add as members
        RoomMember.objects.create(room=room, user=user1, role='member')
        RoomMember.objects.create(room=room, user=user2, role='member')

        return room, True


class RoomMember(models.Model):
    """
    Room membership with roles and permissions
    """
    ROLES = [
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('moderator', 'Moderator'),
        ('member', 'Member'),
    ]

    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='room_memberships')
    role = models.CharField(max_length=20, choices=ROLES, default='member')
    is_pinned = models.BooleanField(default=False)
    is_muted = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)
    last_read_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ['room', 'user']
        indexes = [
            models.Index(fields=['user', '-joined_at']),
            models.Index(fields=['room', 'user']),
        ]

    def __str__(self):
        return f"{self.user.username} in {self.room.name} ({self.role})"

    def mark_as_read(self):
        """Update last read timestamp"""
        self.last_read_at = timezone.now()
        self.save(update_fields=['last_read_at'])


class Message(models.Model):
    """
    Enhanced Message Model with edit history and metadata
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_edited = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # Thread/Reply support
    parent_message = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )

    # Metadata
    metadata = models.JSONField(default=dict, blank=True)  # For @mentions, links, etc.

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['room', 'created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['is_deleted', 'created_at']),
            models.Index(fields=['parent_message', 'created_at']),
        ]

    def __str__(self):
        status = " (deleted)" if self.is_deleted else ""
        return f"{self.user.username}: {self.content[:50]}{status}"

    def mark_edited(self):
        """Mark message as edited"""
        self.is_edited = True
        self.updated_at = timezone.now()
        self.save(update_fields=['is_edited', 'updated_at'])

    def soft_delete(self):
        """Soft delete message"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.content = "[This message was deleted]"
        self.save(update_fields=['is_deleted', 'deleted_at', 'content'])


class MessageEdit(models.Model):
    """
    Message edit history for audit trail
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='edit_history')
    previous_content = models.TextField()
    edited_at = models.DateTimeField(auto_now_add=True)
    edited_by = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-edited_at']
        indexes = [
            models.Index(fields=['message', '-edited_at']),
        ]

    def __str__(self):
        return f"Edit of {self.message.id} at {self.edited_at}"


class Reaction(models.Model):
    """
    Message reactions (emoji)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reactions')
    emoji = models.CharField(max_length=10)  # Emoji unicode
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['message', 'user', 'emoji']
        indexes = [
            models.Index(fields=['message', 'emoji']),
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} reacted {self.emoji} to message {self.message.id}"


class Attachment(models.Model):
    """
    File attachments for messages
    """
    FILE_TYPES = [
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('document', 'Document'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(
        upload_to='attachments/%Y/%m/%d/',
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'pdf', 'doc', 'docx',
                                   'xls', 'xlsx', 'mp4', 'mp3', 'zip', 'txt']
            )
        ]
    )
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=20, choices=FILE_TYPES)
    file_size = models.PositiveIntegerField()  # in bytes
    mime_type = models.CharField(max_length=100)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    # Image-specific fields
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    thumbnail = models.ImageField(upload_to='thumbnails/', null=True, blank=True)

    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['message', '-uploaded_at']),
            models.Index(fields=['file_type', '-uploaded_at']),
        ]

    def __str__(self):
        return f"{self.file_name} ({self.get_file_type_display()})"


class ReadReceipt(models.Model):
    """
    Message read receipts
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='read_receipts')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='read_receipts')
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['message', 'user']
        indexes = [
            models.Index(fields=['message', '-read_at']),
            models.Index(fields=['user', '-read_at']),
        ]

    def __str__(self):
        return f"{self.user.username} read message {self.message.id}"


class Notification(models.Model):
    """
    User notifications
    """
    NOTIFICATION_TYPES = [
        ('message', 'New Message'),
        ('mention', 'Mentioned'),
        ('reaction', 'Reaction'),
        ('room_invite', 'Room Invitation'),
        ('dm', 'Direct Message'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.CharField(max_length=500, blank=True)  # URL to navigate to
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    # Related objects (optional)
    related_message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    related_room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', '-created_at']),
            models.Index(fields=['notification_type', '-created_at']),
        ]

    def __str__(self):
        return f"{self.notification_type} for {self.user.username}"

    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=['is_read', 'read_at'])


class TypingIndicator(models.Model):
    """
    Temporary typing indicators (Redis is better, but this is for persistence)
    """
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='typing_users')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['room', 'user']
        indexes = [
            models.Index(fields=['room', '-started_at']),
        ]

    def __str__(self):
        return f"{self.user.username} typing in {self.room.name}"
