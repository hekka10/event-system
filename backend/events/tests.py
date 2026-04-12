from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from bookings.models import Booking
from events.models import Category, Event
from users.models import StudentVerification


User = get_user_model()


class EventAPITests(APITestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(
            email='organizer@example.com',
            username='organizer',
            password='password123',
        )
        self.other_user = User.objects.create_user(
            email='other@example.com',
            username='other',
            password='password123',
        )
        self.admin = User.objects.create_superuser(
            email='admin@example.com',
            username='admin',
            password='password123',
        )
        self.category = Category.objects.create(name='Conference')

    def test_event_creation_rejects_invalid_values(self):
        self.client.force_authenticate(user=self.organizer)
        response = self.client.post(
            reverse('event-list'),
            {
                'title': '   ',
                'description': 'Test event',
                'date': (timezone.now() - timedelta(days=1)).isoformat(),
                'location': '   ',
                'category': str(self.category.id),
                'price': '-1.00',
                'capacity': 0,
            },
            format='multipart',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('title', response.data)
        self.assertIn('date', response.data)
        self.assertIn('location', response.data)
        self.assertIn('price', response.data)
        self.assertIn('capacity', response.data)

    def test_event_creation_starts_as_pending_even_if_payload_requests_approval(self):
        self.client.force_authenticate(user=self.organizer)
        response = self.client.post(
            reverse('event-list'),
            {
                'title': 'Fresh Event',
                'description': 'Needs review',
                'date': (timezone.now() + timedelta(days=5)).isoformat(),
                'location': 'Conference Hall',
                'category': str(self.category.id),
                'price': '10.00',
                'capacity': 50,
                'is_approved': True,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(response.data['is_approved'])

    def test_event_creation_accepts_google_maps_link_alias(self):
        self.client.force_authenticate(user=self.organizer)
        response = self.client.post(
            reverse('event-list'),
            {
                'title': 'Mapped Event',
                'description': 'With navigation info',
                'date': (timezone.now() + timedelta(days=5)).isoformat(),
                'location': 'Conference Hall',
                'category': str(self.category.id),
                'price': '10.00',
                'capacity': 50,
                'google_maps_link': 'https://maps.google.com/?q=27.7172,85.3240',
                'parking_info': 'Use the east gate parking lot.',
                'latitude': '27.717200',
                'longitude': '85.324000',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        event = Event.objects.get(pk=response.data['id'])
        self.assertEqual(
            event.parking_map_url,
            'https://maps.google.com/?q=27.7172,85.3240',
        )
        self.assertEqual(
            response.data['google_maps_link'],
            'https://maps.google.com/?q=27.7172,85.3240',
        )

    def test_public_event_list_only_includes_approved_events(self):
        approved_event = Event.objects.create(
            title='Approved Event',
            description='Visible to everyone',
            date=timezone.now() + timedelta(days=2),
            location='Hall A',
            category=self.category,
            price=Decimal('20.00'),
            capacity=10,
            organizer=self.organizer,
            is_approved=True,
        )
        Event.objects.create(
            title='Pending Event',
            description='Hidden from guests',
            date=timezone.now() + timedelta(days=3),
            location='Hall B',
            category=self.category,
            price=Decimal('25.00'),
            capacity=20,
            organizer=self.organizer,
            is_approved=False,
        )

        response = self.client.get(reverse('event-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_ids = {item['id'] for item in response.data}
        self.assertIn(str(approved_event.id), returned_ids)
        self.assertEqual(len(returned_ids), 1)

    def test_event_list_hides_events_that_have_already_ended(self):
        upcoming_event = Event.objects.create(
            title='Upcoming Event',
            description='Visible on events page',
            date=timezone.now() + timedelta(days=2),
            location='Hall A',
            category=self.category,
            price=Decimal('20.00'),
            capacity=10,
            organizer=self.organizer,
            is_approved=True,
        )
        past_event = Event.objects.create(
            title='Past Event',
            description='Should be hidden from events page',
            date=timezone.now() + timedelta(days=5),
            location='Hall B',
            category=self.category,
            price=Decimal('25.00'),
            capacity=20,
            organizer=self.organizer,
            is_approved=True,
        )
        Event.objects.filter(pk=past_event.pk).update(date=timezone.now() - timedelta(days=2))

        response = self.client.get(reverse('event-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_ids = {item['id'] for item in response.data}
        self.assertIn(str(upcoming_event.id), returned_ids)
        self.assertNotIn(str(past_event.id), returned_ids)

    def test_organizer_can_view_unapproved_own_event(self):
        event = Event.objects.create(
            title='Private Draft',
            description='Draft',
            date=timezone.now() + timedelta(days=2),
            location='Hall A',
            category=self.category,
            price=Decimal('20.00'),
            capacity=10,
            organizer=self.organizer,
            is_approved=False,
        )

        self.client.force_authenticate(user=self.organizer)
        response = self.client.get(reverse('event-detail', args=[event.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(response.data['id']), str(event.id))

    def test_recommended_events_prioritize_categories_from_past_confirmed_bookings(self):
        music_category = Category.objects.create(name='Music')
        past_attended_event = Event.objects.create(
            title='Past Workshop',
            description='Already attended',
            date=timezone.now() + timedelta(days=4),
            location='Hall A',
            category=self.category,
            price=Decimal('20.00'),
            capacity=20,
            organizer=self.organizer,
            is_approved=True,
        )
        Event.objects.filter(pk=past_attended_event.pk).update(date=timezone.now() - timedelta(days=5))
        past_attended_event.refresh_from_db()

        Booking.objects.create(
            user=self.other_user,
            event=past_attended_event,
            status=Booking.STATUS_CONFIRMED,
            booking_source=Booking.SOURCE_ONLINE,
            is_student=False,
            base_price=Decimal('20.00'),
            discount_amount=Decimal('0.00'),
            total_price=Decimal('20.00'),
            confirmed_at=timezone.now() - timedelta(days=5),
        )

        recommended_match = Event.objects.create(
            title='Recommended Match',
            description='Same category as past booking',
            date=timezone.now() + timedelta(days=8),
            location='Hall B',
            category=self.category,
            price=Decimal('25.00'),
            capacity=50,
            organizer=self.organizer,
            is_approved=True,
        )
        other_category_event = Event.objects.create(
            title='Other Category Event',
            description='Different category',
            date=timezone.now() + timedelta(days=9),
            location='Hall C',
            category=music_category,
            price=Decimal('30.00'),
            capacity=50,
            organizer=self.organizer,
            is_approved=True,
        )
        already_booked_future_event = Event.objects.create(
            title='Already Booked Future Event',
            description='Should be excluded',
            date=timezone.now() + timedelta(days=10),
            location='Hall D',
            category=self.category,
            price=Decimal('15.00'),
            capacity=50,
            organizer=self.organizer,
            is_approved=True,
        )
        sold_out_event = Event.objects.create(
            title='Sold Out Event',
            description='Should be excluded',
            date=timezone.now() + timedelta(days=11),
            location='Hall E',
            category=self.category,
            price=Decimal('15.00'),
            capacity=1,
            organizer=self.organizer,
            is_approved=True,
        )
        Booking.objects.create(
            user=self.other_user,
            event=already_booked_future_event,
            status=Booking.STATUS_PENDING,
            booking_source=Booking.SOURCE_ONLINE,
            is_student=False,
            base_price=Decimal('15.00'),
            discount_amount=Decimal('0.00'),
            total_price=Decimal('15.00'),
        )
        Booking.objects.create(
            user=self.organizer,
            event=sold_out_event,
            status=Booking.STATUS_CONFIRMED,
            booking_source=Booking.SOURCE_ONLINE,
            is_student=False,
            base_price=Decimal('15.00'),
            discount_amount=Decimal('0.00'),
            total_price=Decimal('15.00'),
            confirmed_at=timezone.now(),
        )

        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(reverse('event-recommended'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_ids = [item['id'] for item in response.data]
        self.assertIn(str(recommended_match.id), returned_ids)
        self.assertIn(str(other_category_event.id), returned_ids)
        self.assertNotIn(str(already_booked_future_event.id), returned_ids)
        self.assertNotIn(str(sold_out_event.id), returned_ids)
        self.assertEqual(returned_ids[0], str(recommended_match.id))

    def test_recommended_events_require_authentication(self):
        Event.objects.create(
            title='Protected Recommendation',
            description='Should not be exposed to guests',
            date=timezone.now() + timedelta(days=5),
            location='Members Hall',
            category=self.category,
            price=Decimal('20.00'),
            capacity=50,
            organizer=self.organizer,
            is_approved=True,
        )

        response = self.client.get(reverse('event-recommended'))

        self.assertIn(
            response.status_code,
            {status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN},
        )

    def test_recommended_events_fallback_to_popular_upcoming_events_without_history(self):
        popular_event = Event.objects.create(
            title='Popular Event',
            description='Most booked upcoming event',
            date=timezone.now() + timedelta(days=4),
            location='Main Hall',
            category=self.category,
            price=Decimal('20.00'),
            capacity=100,
            organizer=self.organizer,
            is_approved=True,
        )
        newer_event = Event.objects.create(
            title='New Event',
            description='Fallback option',
            date=timezone.now() + timedelta(days=5),
            location='Side Hall',
            category=self.category,
            price=Decimal('22.00'),
            capacity=100,
            organizer=self.organizer,
            is_approved=True,
        )
        for index in range(3):
            attendee = User.objects.create_user(
                email=f'fallback{index}@example.com',
                username=f'fallback{index}',
                password='password123',
            )
            Booking.objects.create(
                user=attendee,
                event=popular_event,
                status=Booking.STATUS_CONFIRMED,
                booking_source=Booking.SOURCE_ONLINE,
                is_student=False,
                base_price=Decimal('20.00'),
                discount_amount=Decimal('0.00'),
                total_price=Decimal('20.00'),
                confirmed_at=timezone.now(),
            )

        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(reverse('event-recommended'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_ids = [item['id'] for item in response.data]
        self.assertIn(str(popular_event.id), returned_ids)
        self.assertIn(str(newer_event.id), returned_ids)
        self.assertEqual(returned_ids[0], str(popular_event.id))

    def test_only_organizer_or_admin_can_update_event(self):
        event = Event.objects.create(
            title='Team Event',
            description='Desc',
            date=timezone.now() + timedelta(days=3),
            location='Hall B',
            category=self.category,
            price=Decimal('10.00'),
            capacity=25,
            organizer=self.organizer,
            is_approved=True,
        )

        self.client.force_authenticate(user=self.other_user)
        forbidden_response = self.client.patch(
            reverse('event-detail', args=[event.id]),
            {'title': 'Updated by stranger'},
            format='json',
        )
        self.assertEqual(forbidden_response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.admin)
        admin_response = self.client.patch(
            reverse('event-detail', args=[event.id]),
            {'title': 'Updated by admin'},
            format='json',
        )
        self.assertEqual(admin_response.status_code, status.HTTP_200_OK)

    def test_organizer_can_delete_own_event(self):
        event = Event.objects.create(
            title='Delete Me',
            description='Desc',
            date=timezone.now() + timedelta(days=3),
            location='Hall D',
            category=self.category,
            price=Decimal('10.00'),
            capacity=25,
            organizer=self.organizer,
            is_approved=False,
        )

        self.client.force_authenticate(user=self.organizer)
        response = self.client.delete(reverse('event-detail', args=[event.id]))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Event.objects.filter(id=event.id).exists())

    def test_admin_can_approve_pending_event(self):
        event = Event.objects.create(
            title='Approve Me',
            description='Desc',
            date=timezone.now() + timedelta(days=5),
            location='Main Hall',
            category=self.category,
            price=Decimal('30.00'),
            capacity=100,
            organizer=self.organizer,
            is_approved=False,
        )

        self.client.force_authenticate(user=self.admin)
        response = self.client.post(reverse('event-approve', args=[event.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        event.refresh_from_db()
        self.assertTrue(event.is_approved)
        self.assertTrue(response.data['is_approved'])

    def test_non_admin_cannot_approve_event(self):
        event = Event.objects.create(
            title='Approval Lock',
            description='Desc',
            date=timezone.now() + timedelta(days=5),
            location='Main Hall',
            category=self.category,
            price=Decimal('30.00'),
            capacity=100,
            organizer=self.organizer,
            is_approved=False,
        )

        self.client.force_authenticate(user=self.organizer)
        response = self.client.post(reverse('event-approve', args=[event.id]))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        event.refresh_from_db()
        self.assertFalse(event.is_approved)

    def test_only_admin_can_create_categories(self):
        self.client.force_authenticate(user=self.organizer)
        forbidden_response = self.client.post(
            reverse('category-list'),
            {'name': 'Workshop', 'description': 'Hands-on sessions'},
            format='json',
        )
        self.assertEqual(forbidden_response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.admin)
        allowed_response = self.client.post(
            reverse('category-list'),
            {'name': 'Workshop', 'description': 'Hands-on sessions'},
            format='json',
        )
        self.assertEqual(allowed_response.status_code, status.HTTP_201_CREATED)

    def test_event_serializer_includes_live_booking_status(self):
        event = Event.objects.create(
            title='Capacity Test',
            description='Desc',
            date=timezone.now() + timedelta(days=4),
            location='Hall C',
            category=self.category,
            price=Decimal('15.00'),
            capacity=2,
            organizer=self.organizer,
            is_approved=True,
        )
        Booking.objects.create(
            user=self.other_user,
            event=event,
            status='CONFIRMED',
            is_student=False,
            total_price=Decimal('15.00'),
        )

        self.client.force_authenticate(user=self.organizer)
        response = self.client.get(reverse('event-detail', args=[event.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['confirmed_booking_count'], 1)
        self.assertEqual(response.data['remaining_capacity'], 1)
        self.assertFalse(response.data['is_sold_out'])

    def test_event_detail_includes_viewer_student_pricing_preview(self):
        event = Event.objects.create(
            title='Discount Preview',
            description='Desc',
            date=timezone.now() + timedelta(days=6),
            location='Hall E',
            category=self.category,
            price=Decimal('50.00'),
            capacity=40,
            organizer=self.organizer,
            is_approved=True,
        )
        StudentVerification.objects.create(
            user=self.other_user,
            student_email='other@college.edu',
            student_id='STU-123',
            institution_name='Campus College',
            status=StudentVerification.STATUS_APPROVED,
            verified_at=timezone.now(),
            reviewed_at=timezone.now(),
            approved_by=self.admin,
        )

        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(reverse('event-detail', args=[event.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['student_discount_percent'], 20)
        self.assertTrue(response.data['viewer_has_student_discount'])
        self.assertEqual(Decimal(response.data['viewer_discount_amount']), Decimal('10.00'))
        self.assertEqual(Decimal(response.data['viewer_total_price']), Decimal('40.00'))

    def test_event_detail_exposes_google_maps_link_alias(self):
        event = Event.objects.create(
            title='Mapped Detail',
            description='Desc',
            date=timezone.now() + timedelta(days=4),
            location='Hall F',
            category=self.category,
            price=Decimal('15.00'),
            capacity=25,
            organizer=self.organizer,
            is_approved=True,
            parking_info='Park on the north side.',
            parking_map_url='https://maps.google.com/?q=27.7000,85.3333',
            latitude=Decimal('27.700000'),
            longitude=Decimal('85.333300'),
        )

        response = self.client.get(reverse('event-detail', args=[event.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['google_maps_link'],
            'https://maps.google.com/?q=27.7000,85.3333',
        )
        self.assertEqual(response.data['parking_info'], 'Park on the north side.')
