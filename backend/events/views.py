from django.db.models import Count, Q
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response

from .models import Category, Event
from .permissions import IsAdminOrReadOnly, IsOrganizerOrAdmin
from .serializers import CategorySerializer, EventSerializer
from .services import get_recommended_events_for_user


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.select_related('category', 'organizer').annotate(
        confirmed_booking_count_value=Count(
            'bookings',
            filter=Q(bookings__status='CONFIRMED'),
            distinct=True,
        )
    ).order_by('date', '-created_at')
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOrganizerOrAdmin]

    def get_permissions(self):
        if self.action == 'approve':
            permission_classes = [permissions.IsAdminUser]
        elif self.action == 'recommended':
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsOrganizerOrAdmin]
        else:
            permission_classes = [permissions.AllowAny]

        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user, is_approved=False)

    def perform_update(self, serializer):
        serializer.save()

    def get_queryset(self):
        queryset = super().get_queryset()

        # The public events page should only surface upcoming events.
        if self.action == 'list':
            queryset = queryset.filter(date__gt=timezone.now())
        
        # Admin can see all, regular users only see approved
        user = self.request.user
        if not (user.is_authenticated and (user.is_staff or user.is_superuser)):
            if user.is_authenticated:
                queryset = queryset.filter(Q(is_approved=True) | Q(organizer=user))
            else:
                queryset = queryset.filter(is_approved=True)

        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return queryset

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def approve(self, request, pk=None):
        event = self.get_object()
        event.is_approved = True
        event.save(update_fields=['is_approved', 'updated_at'])
        serializer = self.get_serializer(event)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def recommended(self, request):
        recommended_events = get_recommended_events_for_user(request.user)
        serializer = self.get_serializer(recommended_events, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
