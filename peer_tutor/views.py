import logging
from functools import wraps

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Avg, Count, Q
from django.utils import timezone
import calendar

from .models import (
    StudentProfile, Tutor, Slot, Booking,
    Availability, Subject, Review, UserProfile,
)
from .forms import SignupForm, LoginForm, SubjectForm, AvailabilityForm, ReviewForm
from .email_utils import send_welcome_email, send_booking_confirmation, send_booking_cancelled

logger = logging.getLogger('peer_tutor')


def _ws_notify(user_id, category, message, data=None):
    """Send a real-time WebSocket notification to a specific user's group."""
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f'notifications_user_{user_id}',
                {'type': 'notify', 'category': category,
                 'message': message, 'data': data or {}},
            )
    except Exception as exc:
        logger.warning('WS notify failed: %s', exc)


# ── Decorators ────────────────────────────────────────────────────────────────

def require_tutor(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not Tutor.objects.filter(user=request.user).exists():
            messages.error(request, 'You need a tutor profile to access this page.')
            return redirect('tutor:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def require_student(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not StudentProfile.objects.filter(user=request.user).exists():
            messages.error(request, 'You need a student profile to access this page.')
            return redirect('tutor:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


# ── Public Views ──────────────────────────────────────────────────────────────

def home(request):
    if request.user.is_authenticated:
        return redirect('tutor:dashboard')
    return render(request, 'peer_tutor/home.html')


def signup(request):
    if request.user.is_authenticated:
        return redirect('tutor:dashboard')

    form = SignupForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        data = form.cleaned_data
        user = User.objects.create_user(
            username=data['email'].lower(),
            email=data['email'].lower(),
            password=data['password'],
            first_name=data['name'].strip(),
        )
        role = data['role']
        UserProfile.objects.create(user=user, role=role)

        if role in ('tutor', 'both'):
            Tutor.objects.get_or_create(user=user)
        if role in ('student', 'both'):
            StudentProfile.objects.get_or_create(user=user)

        logger.info('New user registered: %s as %s', user.email, role)
        send_welcome_email(user)
        messages.success(request, 'Account created! You can now log in.')
        return redirect('tutor:login')

    return render(request, 'peer_tutor/signup.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('tutor:dashboard')

    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email'].strip().lower()
        password = form.cleaned_data['password']
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            logger.info('User logged in: %s', user.email)
            next_url = request.GET.get('next') or 'tutor:dashboard'
            return redirect(next_url)
        messages.error(request, 'Invalid email or password. Please try again.')

    return render(request, 'peer_tutor/login.html', {'form': form})


@login_required
def logout_view(request):
    if request.method == 'POST':
        logger.info('User logged out: %s', request.user.email)
        logout(request)
        messages.success(request, 'You have been logged out.')
    return redirect('tutor:home')


# ── Dashboard ─────────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    user = request.user
    tutor_profile = Tutor.objects.filter(user=user).first()
    student_profile = StudentProfile.objects.filter(user=user).first()

    context = {
        'tutor_profile': tutor_profile,
        'student_profile': student_profile,
    }

    if tutor_profile:
        upcoming_tutor = (
            Slot.objects
            .filter(tutor=tutor_profile, is_booked=True, start_time__gte=timezone.now())
            .select_related('booking__student')
            .order_by('start_time')[:5]
        )
        avg_rating = tutor_profile.reviews.aggregate(avg=Avg('rating'))['avg']
        context.update({
            'upcoming_tutor_bookings': upcoming_tutor,
            'avg_rating': round(avg_rating, 1) if avg_rating else None,
            'review_count': tutor_profile.reviews.count(),
            'tutor_subject_count': tutor_profile.subjects.count(),
        })

    if student_profile:
        upcoming_student = (
            Booking.objects
            .filter(student=user, slot__start_time__gte=timezone.now())
            .select_related('slot__tutor__user')
            .order_by('slot__start_time')[:5]
        )
        context.update({
            'upcoming_student_sessions': upcoming_student,
            'student_subject_count': student_profile.subjects.count(),
        })

    return render(request, 'peer_tutor/dashboard.html', context)


# ── Profile Pages ─────────────────────────────────────────────────────────────

@login_required
def user_profile(request):
    return redirect('tutor:dashboard')


@login_required
def tutor_page(request):
    tutor_profile, _ = Tutor.objects.get_or_create(user=request.user)
    return render(request, 'peer_tutor/tutor_page.html', {
        'tutor_profile': tutor_profile,
        'subjects': tutor_profile.subjects.all(),
        'availabilities': Availability.objects.filter(tutor=tutor_profile).order_by('date', 'start_time')[:5],
    })


@login_required
def student_page(request):
    student_profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    return render(request, 'peer_tutor/student_page.html', {
        'student_profile': student_profile,
        'subjects': student_profile.subjects.all(),
    })


# ── Subject Management ────────────────────────────────────────────────────────

@login_required
def enter_subjects(request):
    student_profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    form = SubjectForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        name = form.cleaned_data['subject_name']
        subject = Subject.objects.filter(name__iexact=name).first()
        if not subject:
            subject = Subject.objects.create(name=name)
        if student_profile.subjects.filter(id=subject.id).exists():
            messages.info(request, f'"{subject.name}" is already in your list.')
        else:
            student_profile.subjects.add(subject)
            messages.success(request, f'"{subject.name}" added to your subjects.')
        return redirect('tutor:enter_subjects')

    return render(request, 'peer_tutor/enter_subjects.html', {
        'student_profile': student_profile,
        'subjects': student_profile.subjects.all(),
        'form': form,
    })


@login_required
def remove_subject(request, subject_id):
    if request.method == 'POST':
        student_profile = get_object_or_404(StudentProfile, user=request.user)
        subject = get_object_or_404(Subject, id=subject_id)
        student_profile.subjects.remove(subject)
        messages.success(request, f'"{subject.name}" removed.')
    return redirect('tutor:enter_subjects')


@login_required
def enter_tutor_subjects(request):
    tutor_profile, _ = Tutor.objects.get_or_create(user=request.user)
    form = SubjectForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        name = form.cleaned_data['subject_name']
        subject = Subject.objects.filter(name__iexact=name).first()
        if not subject:
            subject = Subject.objects.create(name=name)
        if tutor_profile.subjects.filter(id=subject.id).exists():
            messages.info(request, f'"{subject.name}" is already in your list.')
        else:
            tutor_profile.subjects.add(subject)
            messages.success(request, f'"{subject.name}" added to your subjects.')
        return redirect('tutor:enter_tutor_subjects')

    return render(request, 'peer_tutor/enter_tutor_subjects.html', {
        'tutor_profile': tutor_profile,
        'subjects': tutor_profile.subjects.all(),
        'form': form,
    })


@login_required
def remove_tutor_subject(request, subject_id):
    if request.method == 'POST':
        tutor_profile = get_object_or_404(Tutor, user=request.user)
        subject = get_object_or_404(Subject, id=subject_id)
        tutor_profile.subjects.remove(subject)
        messages.success(request, f'"{subject.name}" removed.')
    return redirect('tutor:enter_tutor_subjects')


# ── Matching ──────────────────────────────────────────────────────────────────

@login_required
def matching_tutors(request):
    student_profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    student_subjects = student_profile.subjects.all()

    if not student_subjects.exists():
        messages.info(request, 'Please add subjects you need help with first.')
        return redirect('tutor:enter_subjects')

    search = request.GET.get('search', '').strip()
    subject_filter = request.GET.get('subject', '').strip()
    min_rating = request.GET.get('min_rating', '').strip()
    ordering = request.GET.get('ordering', '')

    matching = (
        Tutor.objects
        .filter(subjects__in=student_subjects)
        .exclude(user=request.user)
        .annotate(
            match_count=Count('subjects', filter=Q(subjects__in=student_subjects), distinct=True),
            avg_rating=Avg('reviews__rating'),
            review_count=Count('reviews', distinct=True),
        )
        .distinct()
        .prefetch_related('subjects')
        .select_related('user')
    )

    if search:
        matching = matching.filter(
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(user__email__icontains=search)
        )

    if subject_filter:
        matching = matching.filter(subjects__name__icontains=subject_filter)

    if min_rating:
        try:
            matching = matching.filter(avg_rating__gte=float(min_rating))
        except ValueError:
            pass

    valid_orderings = {
        'rating': '-avg_rating',
        'reviews': '-review_count',
        'match': '-match_count',
    }
    order_by = valid_orderings.get(ordering, '-match_count')
    matching = matching.order_by(order_by, '-avg_rating')

    return render(request, 'peer_tutor/matching_tutors.html', {
        'student_subjects': student_subjects,
        'matching_tutors': matching,
        'search': search,
        'subject_filter': subject_filter,
        'min_rating': min_rating,
        'ordering': ordering,
        'all_subjects': Subject.objects.order_by('name'),
    })


# ── Availability ──────────────────────────────────────────────────────────────

@login_required
def availability_calendar(request, tutor_id):
    tutor = get_object_or_404(Tutor, id=tutor_id)
    now = timezone.now()
    year, month = now.year, now.month

    availabilities = Availability.objects.filter(tutor=tutor, date__gte=now.date())
    booked_pairs = set(
        Slot.objects.filter(tutor=tutor, is_booked=True).values_list('start_time', 'end_time')
    )

    available_by_date = {}
    for avail in availabilities:
        s = timezone.make_aware(timezone.datetime.combine(avail.date, avail.start_time))
        e = timezone.make_aware(timezone.datetime.combine(avail.date, avail.end_time))
        if not any(bs < e and be > s for bs, be in booked_pairs):
            available_by_date.setdefault(avail.date, []).append(
                {'start_time': s.strftime('%H:%M'), 'end_time': e.strftime('%H:%M')}
            )

    html_cal = calendar.HTMLCalendar(firstweekday=0)
    month_calendar = html_cal.formatmonth(year, month)
    for date, slots in available_by_date.items():
        display = '<br>'.join(f"{s['start_time']}–{s['end_time']}" for s in slots)
        month_calendar = month_calendar.replace(
            f'>{date.day}<',
            f' class="cal-available">{date.day}<br><small>{display}</small><'
        )

    return render(request, 'peer_tutor/availability_calendar.html', {
        'tutor': tutor,
        'calendar': month_calendar,
        'year': year,
        'month': month,
    })


@require_tutor
def set_availability(request):
    tutor = get_object_or_404(Tutor, user=request.user)
    form = AvailabilityForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        avail = form.save(commit=False)
        avail.tutor = tutor

        exists = Availability.objects.filter(
            tutor=tutor,
            date=avail.date,
            start_time=avail.start_time,
            end_time=avail.end_time,
        ).exists()

        if exists:
            messages.warning(request, 'This availability slot already exists.')
        else:
            avail.save()
            start_dt = timezone.make_aware(
                timezone.datetime.combine(avail.date, avail.start_time)
            )
            end_dt = timezone.make_aware(
                timezone.datetime.combine(avail.date, avail.end_time)
            )
            Slot.objects.get_or_create(
                tutor=tutor, start_time=start_dt, end_time=end_dt,
                defaults={'is_booked': False}
            )
            logger.info('Availability set: tutor=%s date=%s', request.user.email, avail.date)
            messages.success(request, 'Availability saved successfully.')
        return redirect('tutor:set_availability')

    availabilities = Availability.objects.filter(tutor=tutor)
    return render(request, 'peer_tutor/set_availability.html', {
        'form': form,
        'availabilities': availabilities,
    })


@login_required
def delete_availability(request, availability_id):
    if request.method == 'POST':
        avail = get_object_or_404(Availability, id=availability_id, tutor__user=request.user)
        start_dt = timezone.make_aware(
            timezone.datetime.combine(avail.date, avail.start_time)
        )
        end_dt = timezone.make_aware(
            timezone.datetime.combine(avail.date, avail.end_time)
        )
        Slot.objects.filter(
            tutor__user=request.user,
            start_time=start_dt,
            end_time=end_dt,
            is_booked=False,
        ).delete()
        avail.delete()
        messages.success(request, 'Availability slot removed.')
    return redirect('tutor:set_availability')


# ── Slots & Booking ───────────────────────────────────────────────────────────

@login_required
def available_slots(request, tutor_id):
    tutor = get_object_or_404(Tutor, id=tutor_id)
    slots = (
        Slot.objects
        .filter(tutor=tutor, is_booked=False, start_time__gte=timezone.now())
        .order_by('start_time')
    )
    return render(request, 'peer_tutor/available_slots.html', {
        'tutor': tutor,
        'available_slots': slots,
    })


@login_required
def book_slot(request):
    if request.method == 'POST':
        slot_id = request.POST.get('slot_id')
        if not slot_id:
            messages.error(request, 'Invalid request.')
            return redirect('tutor:dashboard')

        slot = get_object_or_404(Slot, id=slot_id)

        if slot.tutor.user == request.user:
            messages.error(request, 'You cannot book your own tutoring slot.')
            return redirect('tutor:available_slots', tutor_id=slot.tutor.id)

        if slot.is_booked:
            messages.error(request, 'Sorry, this slot was just booked by someone else.')
            return redirect('tutor:available_slots', tutor_id=slot.tutor.id)

        booking = Booking.objects.create(student=request.user, slot=slot)
        slot.is_booked = True
        slot.save(update_fields=['is_booked'])

        logger.info('Booking: student=%s slot=%d', request.user.email, slot.id)
        send_booking_confirmation(booking)
        _ws_notify(
            slot.tutor.user.id,
            'booking_created',
            f'{request.user.get_full_name() or request.user.email} booked a session with you!',
            {'booking_id': booking.id},
        )
        messages.success(
            request,
            f'Session booked with {slot.tutor.user.first_name or slot.tutor.user.email}!'
        )
        return redirect('tutor:student_calendar')

    return redirect('tutor:dashboard')


@login_required
def cancel_booking(request, booking_id):
    if request.method == 'POST':
        booking = get_object_or_404(Booking, id=booking_id, student=request.user)
        slot = booking.slot
        tutor_user_id = slot.tutor.user.id
        send_booking_cancelled(booking)
        booking.delete()
        slot.is_booked = False
        slot.save(update_fields=['is_booked'])
        _ws_notify(
            tutor_user_id,
            'booking_cancelled',
            f'{request.user.get_full_name() or request.user.email} cancelled their session.',
            {'slot_id': slot.id},
        )
        logger.info('Booking cancelled: student=%s booking=%d', request.user.email, booking_id)
        messages.success(request, 'Booking cancelled successfully.')
    return redirect('tutor:student_calendar')


# ── Calendars ─────────────────────────────────────────────────────────────────

@require_tutor
def tutor_calendar(request):
    tutor = get_object_or_404(Tutor, user=request.user)
    now = timezone.now()
    year, month = now.year, now.month

    booked_slots = (
        Slot.objects
        .filter(tutor=tutor, is_booked=True)
        .select_related('booking__student')
        .order_by('start_time')
    )

    slots_by_date = {}
    for slot in booked_slots:
        date = slot.start_time.date()
        try:
            student_name = slot.booking.student.first_name or slot.booking.student.email
        except Exception:
            student_name = 'Student'
        slots_by_date.setdefault(date, []).append({
            'start_time': slot.start_time.strftime('%H:%M'),
            'end_time': slot.end_time.strftime('%H:%M'),
            'student': student_name,
        })

    html_cal = calendar.HTMLCalendar(firstweekday=0)
    month_calendar = html_cal.formatmonth(year, month)
    for date, slots in slots_by_date.items():
        display = '<br>'.join(f"{s['start_time']}–{s['end_time']}" for s in slots)
        month_calendar = month_calendar.replace(
            f'>{date.day}<',
            f' class="cal-booked">{date.day}<br><small>{display}</small><'
        )

    return render(request, 'peer_tutor/tutor_calendar.html', {
        'tutor': tutor,
        'calendar': month_calendar,
        'upcoming_slots': booked_slots.filter(start_time__gte=now)[:10],
    })


@login_required
def student_calendar(request):
    student = request.user
    now = timezone.now()
    year, month = now.year, now.month

    bookings = (
        Booking.objects
        .filter(student=student)
        .select_related('slot__tutor__user')
        .order_by('slot__start_time')
    )

    slots_by_date = {}
    for booking in bookings:
        date = booking.slot.start_time.date()
        slots_by_date.setdefault(date, []).append({
            'start_time': booking.slot.start_time.strftime('%H:%M'),
            'end_time': booking.slot.end_time.strftime('%H:%M'),
            'tutor_name': (
                booking.slot.tutor.user.first_name or booking.slot.tutor.user.email
            ),
        })

    html_cal = calendar.HTMLCalendar(firstweekday=0)
    month_calendar = html_cal.formatmonth(year, month)
    for date, slots in slots_by_date.items():
        display = '<br>'.join(
            f"{s['start_time']}–{s['end_time']} ({s['tutor_name']})" for s in slots
        )
        month_calendar = month_calendar.replace(
            f'>{date.day}<',
            f' class="cal-booked">{date.day}<br><small>{display}</small><'
        )

    return render(request, 'peer_tutor/student_calendar.html', {
        'student': student,
        'calendar': month_calendar,
        'upcoming_bookings': bookings.filter(slot__start_time__gte=now)[:10],
    })


# ── Tutor Public Profile & Reviews ────────────────────────────────────────────

@login_required
def tutor_profile_view(request, tutor_id):
    tutor = get_object_or_404(
        Tutor.objects.select_related('user').prefetch_related('subjects', 'reviews__student'),
        id=tutor_id,
    )
    reviews = tutor.reviews.all()
    avg_rating = reviews.aggregate(avg=Avg('rating'))['avg']
    has_session = Booking.objects.filter(student=request.user, slot__tutor=tutor).exists()
    has_reviewed = Review.objects.filter(student=request.user, tutor=tutor).exists()

    return render(request, 'peer_tutor/tutor_profile.html', {
        'tutor': tutor,
        'reviews': reviews,
        'avg_rating': round(avg_rating, 1) if avg_rating else None,
        'has_session': has_session,
        'has_reviewed': has_reviewed,
        'star_range': range(1, 6),
    })


@login_required
def add_review(request, tutor_id):
    tutor = get_object_or_404(Tutor, id=tutor_id)

    has_session = Booking.objects.filter(student=request.user, slot__tutor=tutor).exists()
    if not has_session:
        messages.error(request, 'You can only review tutors you have had a session with.')
        return redirect('tutor:tutor_profile', tutor_id=tutor_id)

    existing = Review.objects.filter(student=request.user, tutor=tutor).first()
    form = ReviewForm(request.POST or None, instance=existing)

    if request.method == 'POST' and form.is_valid():
        review = form.save(commit=False)
        review.student = request.user
        review.tutor = tutor
        review.save()
        action = 'updated' if existing else 'submitted'
        messages.success(request, f'Your review has been {action}!')
        return redirect('tutor:tutor_profile', tutor_id=tutor_id)

    return render(request, 'peer_tutor/add_review.html', {
        'tutor': tutor,
        'form': form,
        'existing': existing,
    })
