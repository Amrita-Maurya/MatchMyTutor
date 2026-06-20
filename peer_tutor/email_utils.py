import logging
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger('peer_tutor')


def _send(subject, body, recipient_list):
    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=False,
        )
        logger.info('Email sent: "%s" → %s', subject, recipient_list)
    except Exception as exc:
        logger.warning('Email failed: %s', exc)


def send_welcome_email(user):
    _send(
        subject='Welcome to MatchMyTutor!',
        body=(
            f'Hi {user.first_name or user.email},\n\n'
            'Your MatchMyTutor account has been created successfully.\n'
            'Log in anytime at /tutor/login/ to find tutors or manage your availability.\n\n'
            'Happy learning!\n— The MatchMyTutor Team'
        ),
        recipient_list=[user.email],
    )


def send_booking_confirmation(booking):
    student = booking.student
    slot = booking.slot
    tutor_user = slot.tutor.user
    time_str = slot.start_time.strftime('%A, %d %b %Y at %H:%M')

    _send(
        subject='Session Booked — MatchMyTutor',
        body=(
            f'Hi {student.first_name or student.email},\n\n'
            f'Your tutoring session has been confirmed!\n\n'
            f'  Tutor : {tutor_user.get_full_name() or tutor_user.email}\n'
            f'  When  : {time_str}\n\n'
            'You can manage your bookings at /tutor/student/calendar/\n\n'
            '— MatchMyTutor'
        ),
        recipient_list=[student.email],
    )

    _send(
        subject='New Booking — MatchMyTutor',
        body=(
            f'Hi {tutor_user.first_name or tutor_user.email},\n\n'
            f'{student.get_full_name() or student.email} has booked a session with you.\n\n'
            f'  When : {time_str}\n\n'
            'View your schedule at /tutor/tutor-calendar/\n\n'
            '— MatchMyTutor'
        ),
        recipient_list=[tutor_user.email],
    )


def send_booking_cancelled(booking):
    student = booking.student
    slot = booking.slot
    tutor_user = slot.tutor.user
    time_str = slot.start_time.strftime('%A, %d %b %Y at %H:%M')

    _send(
        subject='Booking Cancelled — MatchMyTutor',
        body=(
            f'Hi {tutor_user.first_name or tutor_user.email},\n\n'
            f'{student.get_full_name() or student.email} has cancelled their session.\n\n'
            f'  When : {time_str}\n\n'
            'The slot is now available again.\n\n'
            '— MatchMyTutor'
        ),
        recipient_list=[tutor_user.email],
    )
