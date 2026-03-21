from rest_framework import viewsets, permissions
from django.db.models import Q
from .models import Event, Category
from .serializers import EventSerializer, CategorySerializer
from .permissions import IsAdminOrReadOnly, IsOrganizerOrAdmin

from rest_framework.decorators import action
from rest_framework.response import Response

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all().order_by('-date')
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOrganizerOrAdmin]

    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user)

    def perform_update(self, serializer):
        serializer.save()

    def get_queryset(self):
        queryset = super().get_queryset()
        
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
        event.save()
        return Response({'status': 'event approved'})
