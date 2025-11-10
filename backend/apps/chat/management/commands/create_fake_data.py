from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from chat.models import Room, Message
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Creates fake users, rooms, and messages for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=10,
            help='Number of fake users to create (default: 10)'
        )
        parser.add_argument(
            '--rooms',
            type=int,
            default=5,
            help='Number of fake rooms to create (default: 5)'
        )
        parser.add_argument(
            '--messages',
            type=int,
            default=20,
            help='Number of fake messages per room (default: 20)'
        )

    def handle(self, *args, **options):
        num_users = options['users']
        num_rooms = options['rooms']
        num_messages = options['messages']

        self.stdout.write(self.style.SUCCESS('🎭 Creating fake data...'))

        # Create fake users
        self.stdout.write('Creating fake users...')
        fake_users = []
        for i in range(1, num_users + 1):
            username = f'user{i}'
            email = f'user{i}@relaydesk.com'
            password = 'demo123'

            user, created = User.objects.get_or_create(
                username=username,
                defaults={'email': email}
            )
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(f'  ✓ Created user: {username} (password: {password})')
            else:
                self.stdout.write(f'  ⚠ User {username} already exists')
            fake_users.append(user)

        # Create fake rooms
        self.stdout.write('\nCreating fake rooms...')
        room_names = [
            'General Discussion',
            'Tech Talk',
            'Random',
            'Help & Support',
            'Off Topic',
            'Gaming',
            'News',
            'Projects',
            'Learning',
            'Announcements'
        ]

        fake_rooms = []
        for i in range(num_rooms):
            name = room_names[i] if i < len(room_names) else f'Room {i+1}'
            slug = name.lower().replace(' ', '-').replace('&', 'and')

            room, created = Room.objects.get_or_create(
                slug=slug,
                defaults={'name': name}
            )
            if created:
                self.stdout.write(f'  ✓ Created room: {name} (slug: {slug})')
            else:
                self.stdout.write(f'  ⚠ Room {slug} already exists')
            fake_rooms.append(room)

        # Create fake messages
        self.stdout.write('\nCreating fake messages...')
        sample_messages = [
            "Hello everyone!",
            "How is everyone doing today?",
            "Anyone working on interesting projects?",
            "Just wanted to say hi!",
            "This is a great community!",
            "Has anyone tried the new features?",
            "Looking forward to chatting with you all!",
            "What's everyone up to this weekend?",
            "Great discussion!",
            "Thanks for the help!",
            "I agree with that point",
            "Interesting perspective",
            "Let me know if you need any help",
            "That's a good question",
            "I'll look into that",
            "Keep up the good work!",
            "See you all later!",
            "Have a great day!",
            "Welcome to the channel!",
            "Nice to meet everyone"
        ]

        for room in fake_rooms:
            for _ in range(num_messages):
                user = random.choice(fake_users)
                content = random.choice(sample_messages)

                Message.objects.create(
                    room=room,
                    user=user,
                    content=content
                )
            self.stdout.write(f'  ✓ Created {num_messages} messages in {room.name}')

        self.stdout.write(self.style.SUCCESS(f'\n✅ Successfully created:'))
        self.stdout.write(self.style.SUCCESS(f'   - {num_users} users'))
        self.stdout.write(self.style.SUCCESS(f'   - {num_rooms} rooms'))
        self.stdout.write(self.style.SUCCESS(f'   - {num_rooms * num_messages} messages'))
        self.stdout.write(self.style.SUCCESS(f'\nAll users have password: demo123'))
