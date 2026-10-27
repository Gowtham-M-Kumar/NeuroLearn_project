from django.core.management.base import BaseCommand
from django.db import transaction, connection
from apps.users.models import CustomUser, TeacherProfile, ChildProfile


class Command(BaseCommand):
    help = 'Delete all teacher and child profiles and their related data from the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm deletion of all teacher and child data',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING(
                    'This command will delete ALL teacher and child profiles and their related data.\n'
                    'To proceed, run the command with --confirm flag:\n'
                    'python manage.py delete_profiles --confirm'
                )
            )
            return

        # Get users to delete
        teacher_users = CustomUser.objects.filter(role='teacher')
        child_users = CustomUser.objects.filter(role='child')
        
        # Count records before deletion
        teacher_count = TeacherProfile.objects.count()
        child_count = ChildProfile.objects.count()
        teacher_user_count = teacher_users.count()
        child_user_count = child_users.count()

        self.stdout.write(
            self.style.WARNING(
                f'\nAbout to delete:\n'
                f'- {teacher_count} Teacher Profiles\n'
                f'- {child_count} Child Profiles\n'
                f'- {teacher_user_count} Teacher Users\n'
                f'- {child_user_count} Child Users\n'
                f'- All related messages, learning progress, game sessions, routines, and drawings\n'
            )
        )

        try:
            # Disable foreign key constraints for SQLite
            with connection.cursor() as cursor:
                cursor.execute('PRAGMA foreign_keys = OFF;')
            
            with transaction.atomic():
                self.stdout.write('Deleting profiles and all related data...')
                
                # Delete profiles first (they have OneToOne relationships with users)
                deleted_teachers = TeacherProfile.objects.all().delete()
                deleted_children = ChildProfile.objects.all().delete()
                
                # Delete users - this will attempt to CASCADE delete all related objects
                deleted_teacher_users = teacher_users.delete()
                deleted_child_users = child_users.delete()

                # Print summary
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\n✓ Successfully deleted all data:\n'
                        f'  - Teacher Profiles: {deleted_teachers[0]}\n'
                        f'  - Child Profiles: {deleted_children[0]}\n'
                        f'  - Teacher Users: {deleted_teacher_users[0]}\n'
                        f'  - Child Users: {deleted_child_users[0]}\n'
                        f'\nAll related data (messages, progress, games, routines, drawings) has been cascade deleted.\n'
                    )
                )
            
            # Re-enable foreign key constraints
            with connection.cursor() as cursor:
                cursor.execute('PRAGMA foreign_keys = ON;')

        except Exception as e:
            # Re-enable foreign key constraints even on error
            with connection.cursor() as cursor:
                cursor.execute('PRAGMA foreign_keys = ON;')
            
            self.stdout.write(
                self.style.ERROR(f'Error during deletion: {str(e)}')
            )
            raise
