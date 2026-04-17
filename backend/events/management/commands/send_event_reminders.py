from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand

from events.services import get_due_event_reminder_bookings, send_due_event_reminders


class Command(BaseCommand):
    help = 'Send automatic reminder emails to confirmed attendees before the event starts.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--lead-hours',
            type=int,
            default=int(getattr(settings, 'EVENT_REMINDER_LEAD_HOURS', 12)),
            help='Send reminders for events starting within this many hours.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show how many bookings are due without sending emails.',
        )

    def handle(self, *args, **options):
        lead_hours = max(options['lead_hours'], 0)
        lead_time = timedelta(hours=lead_hours)

        if options['dry_run']:
            due_count = get_due_event_reminder_bookings(lead_time=lead_time).count()
            self.stdout.write(
                self.style.SUCCESS(
                    f'{due_count} booking reminder(s) are due within the next {lead_hours} hour(s).'
                )
            )
            return

        result = send_due_event_reminders(lead_time=lead_time, fail_silently=False)
        if result['sent_count'] == 0 and result['failed_count'] == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'No reminder emails were due within the next {lead_hours} hour(s).'
                )
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"Sent {result['sent_count']} reminder email(s) for {result['processed_count']} due booking(s)."
            )
        )

        if result['failed_count'] > 0:
            self.stdout.write(
                self.style.WARNING(
                    f"Failed to send {result['failed_count']} reminder email(s)."
                )
            )
