from django.urls import path
from . import views

urlpatterns = [
    path('subjects/', views.SubjectListView.as_view(), name='api-subject-list'),

    path('tutors/', views.TutorListView.as_view(), name='api-tutor-list'),
    path('tutors/<int:pk>/', views.TutorDetailView.as_view(), name='api-tutor-detail'),
    path('tutors/<int:tutor_id>/reviews/', views.TutorReviewListView.as_view(), name='api-tutor-reviews'),
    path('tutors/<int:tutor_id>/reviews/create/', views.ReviewCreateView.as_view(), name='api-review-create'),
    path('tutors/<int:tutor_id>/slots/', views.TutorSlotListView.as_view(), name='api-tutor-slots'),

    path('bookings/', views.BookingListCreateView.as_view(), name='api-booking-list-create'),
    path('bookings/<int:pk>/', views.BookingCancelView.as_view(), name='api-booking-cancel'),

    path('auth/register/', views.RegisterView.as_view(), name='api-register'),
    path('auth/me/', views.MeView.as_view(), name='api-me'),
]
