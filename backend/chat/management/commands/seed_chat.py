"""
Django Management Command: Seed Chat Data
Creates demo users, rooms, and messages for testing
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from chat.models import Room, Message
from django.utils import timezone
import random


class Command(BaseCommand):
    help = 'Seeds the database with demo chat data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=5,
            help='Number of users to create'
        )
        parser.add_argument(
            '--rooms',
            type=int,
            default=3,
            help='Number of rooms to create'
        )
        parser.add_argument(
            '--messages',
            type=int,
            default=20,
            help='Number of messages per room'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🌱 Starting database seeding...'))

        # Clear existing data
        if self.confirm_clear():
            Message.objects.all().delete()
            Room.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write(self.style.WARNING('🗑️  Cleared existing data'))

        # Create users
        users = self.create_users(options['users'])
        self.stdout.write(self.style.SUCCESS(f'✅ Created {len(users)} users'))

        # Create rooms
        rooms = self.create_rooms(users, options['rooms'])
        self.stdout.write(self.style.SUCCESS(f'✅ Created {len(rooms)} rooms'))

        # Create messages
        message_count = self.create_messages(users, rooms, options['messages'])
        self.stdout.write(self.style.SUCCESS(f'✅ Created {message_count} messages'))

        self.stdout.write(self.style.SUCCESS('\n🎉 Database seeded successfully!'))
        self.print_summary(users, rooms)

    def confirm_clear(self):
        """Ask user to confirm clearing existing data"""
        response = input('⚠️  Clear existing data? (yes/no): ')
        return response.lower() == 'yes'

    def create_users(self, count):
        """Create demo users"""
        usernames = [
            'alice_dev', 'bob_designer', 'charlie_pm', 'diana_qa',
            'eve_backend', 'frank_frontend', 'grace_devops', 'henry_mobile'
        ]
        users = []

        for i in range(min(count, len(usernames))):
            username = usernames[i]
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@relaydesk.com',
                    'first_name': username.split('_')[0].capitalize(),
                    'last_name': username.split('_')[1].capitalize()
                }
            )
            if created:
                user.set_password('demo123')
                user.save()
            users.append(user)

        return users

    def create_rooms(self, users, count):
        """Create demo chat rooms"""
        room_data = [
            {
                'name': 'General Discussion',
                'description': 'General chat for everyone'
            },
            {
                'name': 'Development Team',
                'description': 'For dev team coordination'
            },
            {
                'name': 'Design Feedback',
                'description': 'Share and discuss designs'
            },
            {
                'name': 'Product Updates',
                'description': 'Product announcements and updates'
            },
            {
                'name': 'Random',
                'description': 'Off-topic conversations'
            }
        ]

        rooms = []
        for i in range(min(count, len(room_data))):
            data = room_data[i]
            room, created = Room.objects.get_or_create(
                name=data['name'],
                defaults={
                    'description': data['description'],
                    'created_by': random.choice(users)
                }
            )
            rooms.append(room)

        return rooms

    def create_messages(self, users, rooms, per_room):
        """Create demo messages"""
        message_templates = [
            "Hey everyone! 👋",
            "Has anyone seen the latest updates?",
            "I'm working on the new feature",
            "Great work on the last sprint!",
            "Can someone review my PR?",
            "Meeting in 10 minutes",
            "Just deployed to staging 🚀",
            "Found a bug in production 🐛",
            "Documentation updated",
            "Let's discuss this tomorrow",
            "Thanks for the help!",
            "Working from home today",
            "Code review completed ✅",
            "New design looks amazing!",
            "Performance improvements deployed",
            "Testing the new build now",
            "All tests passing! 🎉",
            "Quick question about the API",
            "Lunch break, back in 30",
            "End of day update: everything on track"
        ]

        total_messages = 0
        for room in rooms:
            for i in range(per_room):
                Message.objects.create(
                    room=room,
                    user=random.choice(users),
                    content=random.choice(message_templates)
                )
                total_messages += 1

        return total_messages

    def print_summary(self, users, rooms):
        """Print summary of seeded data"""
        self.stdout.write('\n📊 Summary:')
        self.stdout.write('─' * 50)
        self.stdout.write(f'Users: {len(users)}')
        for user in users:
            self.stdout.write(f'  • {user.username} (password: demo123)')
        
        self.stdout.write(f'\nRooms: {len(rooms)}')
        for room in rooms:
            msg_count = room.messages.count()
            self.stdout.write(f'  • {room.name} ({msg_count} messages)')
        
        self.stdout.write('\n💡 Tips:')
        self.stdout.write('  • Login credentials: username / demo123')
        self.stdout.write('  • Admin panel: http://localhost:8000/admin/')
        self.stdout.write('  • API health: http://localhost:8000/api/health/')
        self.stdout.write('─' * 50)
