from django.urls import path
from . import views

app_name = "tutor"

urlpatterns = [
    path("", views.home, name="home"),
    path("signup/", views.signup, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),

    path("user/profile", views.user_profile, name="user_profile"),
    path("user/tutor", views.tutor_page, name="tutor_page"),
    path("user/student", views.student_page, name="student_page"),

    path("user/profile/enter_subjects", views.enter_subjects, name="enter_subjects"),
    path("user/profile/remove_subject/<int:subject_id>/", views.remove_subject, name="remove_subject"),
    path("user/profile/enter_tutor_subjects", views.enter_tutor_subjects, name="enter_tutor_subjects"),
    path("user/profile/remove_tutor_subject/<int:subject_id>/", views.remove_tutor_subject, name="remove_tutor_subject"),

    path("user/profile/matching_tutors", views.matching_tutors, name="matching_tutors"),

    path("availability-calendar/<int:tutor_id>/", views.availability_calendar, name="availablility_calendar"),
    path("tutor/set-availability/", views.set_availability, name="set_availability"),
    path("availability/delete/<int:availability_id>/", views.delete_availability, name="delete_availability"),

    path("availability/<int:tutor_id>/", views.available_slots, name="available_slots"),
    path("book_slot/", views.book_slot, name="book_slot"),
    path("booking/cancel/<int:booking_id>/", views.cancel_booking, name="cancel_booking"),

    path("tutor-calendar/", views.tutor_calendar, name="tutor_calendar"),
    path("student/calendar/", views.student_calendar, name="student_calendar"),

    path("tutor/<int:tutor_id>/profile/", views.tutor_profile_view, name="tutor_profile"),
    path("tutor/<int:tutor_id>/review/", views.add_review, name="add_review"),
]
