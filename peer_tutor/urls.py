from django.urls import path

from . import views


app_name = "tutor"
urlpatterns = [
    path("", views.home, name="home"),
    path("signup/", views.signup, name="signup"),
    path("login/", views.login_view, name="login"),
    path('user/profile', views.user_profile, name='user_profile'), 
    path('user/profile/enter_subjects', views.enter_subjects, name="enter_subjects"),
    path('user/profile/enter_tutor_subjects', views.enter_tutor_subjects, name="enter_tutor_subjects"),
    path('user/profile/matching_tutors', views.matching_tutors, name="matching_tutors"),
    path('availability-calendar/<int:tutor_id>/', views.availability_calendar, name='availablility_calendar'),
    path('tutor/set-availability/', views.set_availability, name='set_availability'),
    path('availability/<int:tutor_id>/', views.available_slots, name='available_slots'),
    path('book_slot/', views.book_slot, name='book_slot'),
    path('student/bookings/', views.student_bookings, name='student_bookings'),
    path('manage-bookings/', views.manage_bookings, name='manage_bookings'),
    path('tutor-calendar/', views.tutor_calendar, name='tutor_calendar'),  # Tutor calendar view
    path('student/calendar/', views.student_calendar, name='student_calendar'),  # Student calendar view
]

