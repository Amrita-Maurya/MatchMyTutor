import logging
from django.contrib.auth.models import User
from django.db.models import Avg, Count, Q
from django.utils import timezone
from rest_framework import generics, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from peer_tutor.models import (
    Tutor, StudentProfile, Slot, Booking, Subject, Review
)
from .serializers import (
    TutorListSerializer, TutorDetailSerializer,
    SlotSerializer, BookingSerializer, BookingCreateSerializer,
    ReviewSerializer, ReviewCreateSerializer,
    SubjectSerializer, UserRegistrationSerializer, UserProfileSerializer,
)
from .permissions import IsTutor, IsStudent, IsBookingOwner, IsReviewAuthor
from .filters import TutorFilter, SlotFilter
from .pagination import StandardPagination, SmallPagination
from peer_tutor.email_utils import send_booking_confirmation, send_booking_cancelled, send_welcome_email

logger = logging.getLogger('peer_tutor')


def _ws_notify(user_id, category, message, data=None):
    """Fire-and-forget WebSocket notification to a user's group."""
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        channel_layer = get_channel_layer()
        if channel_layer is None:
            return
        async_to_sync(channel_layer.group_send)(
            f'notifications_user_{user_id}',
            {'type': 'notify', 'category': category, 'message': message, 'data': data or {}},
        )
    except Exception as exc:
        logger.warning('WS notify failed: %s', exc)


# ── Subject ────────────────────────────────────────────────────────────────────

class SubjectListView(generics.ListAPIView):
    """GET /api/subjects/ — list all subjects (public)."""
    queryset = Subject.objects.all().order_by('name')
    serializer_class = SubjectSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']
    pagination_class = SmallPagination


# ── Tutor ──────────────────────────────────────────────────────────────────────

class TutorListView(generics.ListAPIView):
    """
    GET /api/tutors/
    List all tutors with optional filters:
      ?subject=Python   — subject name contains
      ?min_rating=4     — minimum average rating
      ?search=john      — search by tutor name/email
      ?page=2           — paginate (10 per page)
    """
    serializer_class = TutorListSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = TutorFilter
    ordering_fields = ['avg_rating', 'review_count']
    ordering = ['-avg_rating']
    pagination_class = StandardPagination

    def get_queryset(self):
        return (
            Tutor.objects
            .select_related('user')
            .prefetch_related('subjects')
            .annotate(
                _avg_rating=Avg('reviews__rating'),
                _review_count=Count('reviews', distinct=True),
            )
            .order_by('-_avg_rating')
        )


class TutorDetailView(generics.RetrieveAPIView):
    """GET /api/tutors/{id}/ — full tutor profile."""
    serializer_class = TutorDetailSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return (
            Tutor.objects
            .select_related('user')
            .prefetch_related('subjects', 'reviews__student')
            .annotate(
                _avg_rating=Avg('reviews__rating'),
                _review_count=Count('reviews', distinct=True),
            )
        )


class TutorReviewListView(generics.ListAPIView):
    """GET /api/tutors/{tutor_id}/reviews/ — paginated reviews for a tutor."""
    serializer_class = ReviewSerializer
    permission_classes = [AllowAny]
    pagination_class = SmallPagination

    def get_queryset(self):
        return (
            Review.objects
            .filter(tutor_id=self.kwargs['tutor_id'])
            .select_related('student')
            .order_by('-created_at')
        )


class TutorSlotListView(generics.ListAPIView):
    """GET /api/tutors/{tutor_id}/slots/ — available (unbooked) future slots."""
    serializer_class = SlotSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_class = SlotFilter

    def get_queryset(self):
        return (
            Slot.objects
            .filter(
                tutor_id=self.kwargs['tutor_id'],
                is_booked=False,
                start_time__gte=timezone.now(),
            )
            .order_by('start_time')
        )


# ── Booking ────────────────────────────────────────────────────────────────────

class BookingListCreateView(APIView):
    """
    GET  /api/bookings/ — list my bookings
    POST /api/bookings/ — create a new booking
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        bookings = (
            Booking.objects
            .filter(student=request.user)
            .select_related('slot__tutor__user')
            .order_by('slot__start_time')
        )
        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = BookingCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        slot_id = serializer.validated_data['slot_id']
        slot = Slot.objects.select_related('tutor__user').get(id=slot_id)

        if slot.tutor.user == request.user:
            return Response(
                {'detail': 'You cannot book your own tutoring slot.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        booking = Booking.objects.create(student=request.user, slot=slot)
        slot.is_booked = True
        slot.save(update_fields=['is_booked'])

        logger.info('API booking: student=%s slot=%d', request.user.email, slot.id)

        send_booking_confirmation(booking)
        _ws_notify(
            slot.tutor.user.id,
            'booking_created',
            f'{request.user.get_full_name() or request.user.email} booked a session with you!',
            {'booking_id': booking.id},
        )

        return Response(BookingSerializer(booking).data, status=status.HTTP_201_CREATED)


class BookingCancelView(APIView):
    """DELETE /api/bookings/{id}/ — cancel a booking (owner only)."""
    permission_classes = [IsAuthenticated, IsBookingOwner]

    def delete(self, request, pk):
        try:
            booking = Booking.objects.select_related('slot__tutor__user').get(
                id=pk, student=request.user
            )
        except Booking.DoesNotExist:
            return Response({'detail': 'Booking not found.'}, status=status.HTTP_404_NOT_FOUND)

        slot = booking.slot
        tutor_user_id = slot.tutor.user.id
        booking.delete()
        slot.is_booked = False
        slot.save(update_fields=['is_booked'])

        logger.info('API cancel: student=%s booking=%d', request.user.email, pk)

        send_booking_cancelled(booking)
        _ws_notify(
            tutor_user_id,
            'booking_cancelled',
            f'{request.user.get_full_name() or request.user.email} cancelled their session.',
            {'slot_id': slot.id},
        )

        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Reviews ────────────────────────────────────────────────────────────────────

class ReviewCreateView(APIView):
    """
    POST /api/tutors/{tutor_id}/reviews/create/
    Create or update a review. Requires a confirmed booking.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, tutor_id):
        tutor = Tutor.objects.filter(id=tutor_id).first()
        if not tutor:
            return Response({'detail': 'Tutor not found.'}, status=status.HTTP_404_NOT_FOUND)

        has_session = Booking.objects.filter(
            student=request.user, slot__tutor=tutor
        ).exists()
        if not has_session:
            return Response(
                {'detail': 'You can only review tutors you have had a session with.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        existing = Review.objects.filter(student=request.user, tutor=tutor).first()
        serializer = ReviewCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if existing:
            existing.rating = serializer.validated_data['rating']
            existing.comment = serializer.validated_data.get('comment', existing.comment)
            existing.save()
            return Response(ReviewSerializer(existing).data, status=status.HTTP_200_OK)

        review = Review.objects.create(
            student=request.user,
            tutor=tutor,
            **serializer.validated_data,
        )
        return Response(ReviewSerializer(review).data, status=status.HTTP_201_CREATED)


# ── Auth ───────────────────────────────────────────────────────────────────────

class RegisterView(APIView):
    """POST /api/auth/register/ — create a new account."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        user = serializer.save()
        send_welcome_email(user)
        logger.info('API register: %s', user.email)
        return Response(
            {'detail': 'Account created successfully.', 'email': user.email},
            status=status.HTTP_201_CREATED,
        )


class MeView(APIView):
    """GET /api/auth/me/ — current user profile."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserProfileSerializer(request.user).data)
