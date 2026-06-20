from rest_framework.permissions import BasePermission, SAFE_METHODS
from peer_tutor.models import Tutor, StudentProfile, Booking


class IsTutor(BasePermission):
    """Allow access only to users with a Tutor profile."""
    message = 'You need a tutor profile to perform this action.'

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            Tutor.objects.filter(user=request.user).exists()
        )


class IsStudent(BasePermission):
    """Allow access only to users with a StudentProfile."""
    message = 'You need a student profile to perform this action.'

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            StudentProfile.objects.filter(user=request.user).exists()
        )


class IsOwnerOrReadOnly(BasePermission):
    """Allow read access to everyone; write access only to the object owner."""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        owner = getattr(obj, 'student', None) or getattr(obj, 'user', None)
        return owner == request.user


class IsBookingOwner(BasePermission):
    """Allow access only to the student who made the booking."""
    message = 'You do not own this booking.'

    def has_object_permission(self, request, view, obj):
        return obj.student == request.user


class IsReviewAuthor(BasePermission):
    """Allow write access only to the review author."""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.student == request.user
