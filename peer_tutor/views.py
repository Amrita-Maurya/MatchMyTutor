from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib import messages
from .models import StudentProfile, Tutor, Slot, Booking,  Availability
from django.utils import timezone
import calendar


 





def home(request):
    return render(request, 'peer_tutor/home.html')

def signup(request):
    if request.method == 'POST':
        
        name = request.POST['name']
        email = request.POST['email']
        password = request.POST['password']

        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists. Please use a different email.')
            return render(request, 'peer_tutor/signup.html')

        
        user = User.objects.create_user(username=email, email=email, password=password)
        user.first_name=name
        user.save()

        messages.success(request, 'Your account has been created! You can now log in.')
        return redirect('tutor:login')  
    
    return render(request, 'peer_tutor/signup.html')  
    
def login_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            print(f"User {user.username} logged in successfully.")
            return redirect("tutor:user_profile")
              
        else:
            return render(request, 'peer_tutor/login.html', {'messages': ["Invalid credentials"]})
    
    return render(request, 'peer_tutor/login.html')

def user_profile(request):
    return render(request, 'peer_tutor/user_profile.html')

def tutor_page(request):
    return render(request, 'peer_tutor/tutor_page.html')


def student_page(request):
    return render(request, 'peer_tutor/student_page.html')


def enter_subjects(request):
    student_profile, created = StudentProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        new_subject = request.POST.get('new_subject')
        
        if new_subject:
            if student_profile.subjects_needed:
                student_profile.subjects_needed += ',' + new_subject
            else:
                student_profile.subjects_needed = new_subject
            
            student_profile.save()
            return redirect('tutor:enter_subjects')

    subjects_list = student_profile.subjects_needed.split(',') if student_profile.subjects_needed else []
    tutors = Tutor.objects.all()
    return render(request, 'peer_tutor/enter_subjects.html', {
        'student_profile': student_profile,
        'subjects_list': subjects_list,
        'tutors': tutors,
    })


def enter_tutor_subjects(request):
    tutor_profile, created = Tutor.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        new_subject = request.POST.get('new_subject')
        
        if new_subject:
            if tutor_profile.subjects_can_teach:
                tutor_profile.subjects_can_teach += ',' + new_subject
            else:
                tutor_profile.subjects_can_teach = new_subject
            
            tutor_profile.save()
            return redirect('tutor:enter_tutor_subjects')

    subjects_list = tutor_profile.subjects_can_teach.split(',') if tutor_profile.subjects_can_teach else []

    return render(request, 'peer_tutor/enter_tutor_subjects.html', {
        'tutor_profile': tutor_profile,
        'subjects_list': subjects_list,
    })

def matching_tutors(request):
    student_profile, created = StudentProfile.objects.get_or_create(user=request.user)
    
    if not student_profile.subjects_needed:
        return render(request, 'peer_tutor/matching_tutors.html', {
            'student_profile': student_profile,
            'matching_tutors': [],  # No tutors found
            'message': ['Please enter subjects you need help with first.'],
        })

    needed_subjects = [subject.strip() for subject in student_profile.subjects_needed.split(',')]
    
    # Prepare a dictionary to hold subjects and their matching tutors
    subject_tutor_mapping = {}

    # Find matching tutors for each needed subject
    for subject in needed_subjects:
        # Filter tutors who can teach the subject
        tutors = Tutor.objects.filter(subjects_can_teach__icontains=subject).exclude(user=request.user)
        if tutors.exists():
            subject_tutor_mapping[subject] = tutors

    return render(request, 'peer_tutor/matching_tutors.html', {
        'student_profile': student_profile,
        'subject_tutor_mapping': subject_tutor_mapping,
    })
    
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from .models import Tutor, Availability, Slot
import calendar

def availability_calendar(request, tutor_id):
    tutor = get_object_or_404(Tutor, id=tutor_id)
    now = timezone.now()
    year = now.year
    month = now.month

    # Fetch tutor's availability and booked slots
    availabilities = Availability.objects.filter(tutor=tutor)
    booked_slots = Slot.objects.filter(tutor=tutor, is_booked=True)

    # Create a set of booked time ranges for quick lookup
    booked_times = set()
    for slot in booked_slots:
        booked_times.add((slot.start_time, slot.end_time))  # Store full datetime objects

    # Create a dictionary for available slots with times
    available_slots = {}
    
    for availability in availabilities:
        date = availability.date
        
        # Combine date with availability start and end times
        slot_start = timezone.datetime.combine(date, availability.start_time)
        slot_end = timezone.datetime.combine(date, availability.end_time)
        if slot_start.tzinfo is None:
            slot_start = timezone.make_aware(slot_start)
        if slot_end.tzinfo is None:
            slot_end = timezone.make_aware(slot_end)
        # Check if this slot is already booked
        if not any(start < slot_end and end > slot_start for start, end in booked_times):
            if date not in available_slots:
                available_slots[date] = []
            available_slots[date].append({
                'start_time': slot_start.strftime("%H:%M"),  # Format as hr:min
                'end_time': slot_end.strftime("%H:%M"),
            })

    # Create an HTML calendar
    html_calendar = calendar.HTMLCalendar(firstweekday=0)  # Monday as the first day of the week

    # Generate HTML for the current month
    month_calendar = html_calendar.formatmonth(year, month)

    # Highlight available slots in the calendar and show their times
    for date, slots in available_slots.items():
        time_slots_display = '<br> '.join([f"{slot['start_time']} - {slot['end_time']}" for slot in slots])
        month_calendar = month_calendar.replace(
            f'>{date.day}<',
            f' style="background-color: lightgreen;">{date.day}<br>{time_slots_display}<'
        )

    return render(request, 'peer_tutor/availability_calendar.html', {
        'tutor': tutor,
        'calendar': month_calendar,
        'year': year,
        'month': month,
    })


def manage_bookings(request):
    tutor = get_object_or_404(Tutor, user=request.user)
    bookings = Booking.objects.filter(slot__tutor=tutor).order_by('slot__start_time')

    if request.method == 'POST':
        booking_id = request.POST.get('booking_id')
        action = request.POST.get('action')  # Expecting either "confirm" or "reject"
        booking = get_object_or_404(Booking, id=booking_id)

        if action == 'confirm':
            booking.status = 'confirmed'
            booking.slot.is_booked = True  # Mark the slot as booked
            booking.slot.save()
        elif action == 'reject':
            booking.status = 'rejected'

        booking.save()
        
        # Optionally notify student about confirmation/rejection (implement email notification here)

        return redirect('tutor:manage_bookings')  # Redirect back to manage bookings page

    return render(request, 'peer_tutor/manage_bookings.html', {
        'tutor': tutor,
        'bookings': bookings,
    })


def set_availability(request):
    tutor = get_object_or_404(Tutor, user=request.user)

    if request.method == 'POST':
        # Logic to save availability based on form input
        date = request.POST.get('date')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')

        Availability.objects.create(tutor=tutor,date=date,start_time=start_time,end_time=end_time)

        return redirect('tutor:set_availability')  # Redirect after saving

    # Fetch existing availability for display
    availabilities = Availability.objects.filter(tutor=tutor)

    for availability in availabilities:
        slot_start = timezone.datetime.combine(availability.date, availability.start_time)
        slot_end = timezone.datetime.combine(availability.date, availability.end_time)

        # Create a new Slot if it doesn't already exist
        Slot.objects.get_or_create(
            tutor=tutor,
            start_time=slot_start,
            end_time=slot_end,
            defaults={'is_booked': False}  # Default value for is_booked
        )


    
    return render(request, 'peer_tutor/set_availability.html', {
        'availabilities': availabilities,
    })


    


def student_bookings(request):
    # Get bookings for the logged-in student
    bookings = Booking.objects.filter(student=request.user).order_by('slot__start_time')

    return render(request, 'peer_tutor/student_bookings.html', {
        'bookings': bookings,
    })


def available_slots(request, tutor_id):
    tutor = get_object_or_404(Tutor, id=tutor_id)
    
    # Fetch all availability entries for the tutor
    availabilities = Availability.objects.filter(tutor=tutor)

    # Create a list to hold available slots
    available_slots = []

    # Loop through each availability entry and create slots
    for availability in availabilities:
        slot_start = timezone.datetime.combine(availability.date, availability.start_time)
        slot_end = timezone.datetime.combine(availability.date, availability.end_time)

        # Check if this slot is already booked
        if not Slot.objects.filter(start_time=slot_start, end_time=slot_end, is_booked=True).exists():
            # If not booked, add it to the available slots list
            available_slots.append(Slot(tutor=tutor, start_time=slot_start, end_time=slot_end))

    return render(request, 'peer_tutor/available_slots.html', {
        'tutor': tutor,
        'available_slots': available_slots,
    })


from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import Slot, Booking

def book_slot(request):
    if request.method == 'POST':
        start_time_str = request.POST.get('start_time')
        end_time_str = request.POST.get('end_time')

        try:
            start_time = timezone.datetime.fromisoformat(start_time_str)
            end_time = timezone.datetime.fromisoformat(end_time_str)
        except ValueError as e:
            return redirect('tutor:available_slots', tutor_id=request.user.id)  # Handle invalid datetime format

        # Fetch the corresponding slot
        try:
            # Adjust this query to ensure it fetches the correct slot
            slot = get_object_or_404(Slot, start_time=start_time, end_time=end_time)

            # Check if the slot is still available before booking
            if not slot.is_booked:
                booking = Booking(student=request.user, slot=slot)
                booking.save()
                slot.is_booked = True
                slot.save()
                # Optionally redirect to a confirmation page or available slots page
                return redirect('tutor:student_calendar')
            else:
                return redirect('tutor:available_slots', tutor_id=slot.tutor.id)  # Redirect if already booked
        
        except Slot.DoesNotExist:
            return redirect('tutor:available_slots', tutor_id=request.user.id)  # Redirect if slot does not exist

    return redirect('tutor:available_slots', tutor_id=request.user.id)  # Redirect if not POST

def tutor_calendar(request):
    # Get the logged-in user
    user = request.user
    
    # Get or create a Tutor instance for the logged-in user
    tutor = get_object_or_404(Tutor, user=user)  # Assuming Tutor model has a ForeignKey or OneToOneField to User
    
    now = timezone.now()
    year = now.year
    month = now.month

    # Fetch booked slots for the tutor
    booked_slots = Slot.objects.filter(tutor=tutor, is_booked=True)

    # Create a dictionary to hold booked slots by date
    slots_by_date = {}
    for slot in booked_slots:
        date = slot.start_time.date()
        if date not in slots_by_date:
            slots_by_date[date] = []
        slots_by_date[date].append({
            'start_time': slot.start_time.strftime("%H:%M"),
            'end_time': slot.end_time.strftime("%H:%M"),
        })

    # Create an HTML calendar
    html_calendar = calendar.HTMLCalendar(firstweekday=0)  # Monday as the first day of the week

    # Generate HTML for the current month
    month_calendar = html_calendar.formatmonth(year, month)

    # Highlight booked slots in the calendar and show their times
    for date, slots in slots_by_date.items():
        time_slots_display = '<br> '.join([f"{slot['start_time']} - {slot['end_time']}" for slot in slots])
        month_calendar = month_calendar.replace(
            f'>{date.day}<',
            f' style="background-color: lightblue;">{date.day}<br>{time_slots_display}<'
        )

    return render(request, 'peer_tutor/tutor_calendar.html', {
        'tutor': tutor,
        'calendar': month_calendar,
        'year': year,
        'month': month,
    })




def student_calendar(request):
    student = request.user  # Assuming the user is logged in as a student
    now = timezone.now()
    year = now.year
    month = now.month

    # Fetch booked slots for the student
    booked_slots = Booking.objects.filter(student=student).select_related('slot')

    # Create a dictionary to hold booked slots by date
    slots_by_date = {}
    for booking in booked_slots:
        date = booking.slot.start_time.date()
        if date not in slots_by_date:
            slots_by_date[date] = []
        slots_by_date[date].append({
            'start_time': booking.slot.start_time.strftime("%H:%M"),
            'end_time': booking.slot.end_time.strftime("%H:%M"),
            'tutor_name': booking.slot.tutor.user.first_name  # Include tutor information if needed
        })

    # Create an HTML calendar
    html_calendar = calendar.HTMLCalendar(firstweekday=0)  # Monday as the first day of the week

    # Generate HTML for the current month
    month_calendar = html_calendar.formatmonth(year, month)

    # Highlight booked slots in the calendar and show their times
    for date, slots in slots_by_date.items():
        time_slots_display = '<br> '.join([f"{slot['start_time']} - {slot['end_time']} (Tutor: {slot['tutor_name']})" for slot in slots])
        month_calendar = month_calendar.replace(
            f'>{date.day}<',
            f' style="background-color: lightgreen;">{date.day}<br>{time_slots_display}<'
        )

    return render(request, 'peer_tutor/student_calendar.html', {
        'student': student,
        'calendar': month_calendar,
        'year': year,
        'month': month,
    })

