from django.contrib import admin
from django.db.models import Avg
from .models import Subject, UserProfile, Tutor, StudentProfile, Slot, Booking, Availability, Review


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'tutor_count', 'student_count')
    search_fields = ('name',)

    def tutor_count(self, obj):
        return obj.tutors.count()
    tutor_count.short_description = 'Tutors'

    def student_count(self, obj):
        return obj.students.count()
    student_count.short_description = 'Students'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    list_filter = ('role',)
    search_fields = ('user__email', 'user__first_name')


@admin.register(Tutor)
class TutorAdmin(admin.ModelAdmin):
    list_display = ('user', 'subject_list', 'avg_rating', 'review_count')
    search_fields = ('user__email', 'user__first_name')
    filter_horizontal = ('subjects',)

    def subject_list(self, obj):
        return ', '.join(obj.subjects.values_list('name', flat=True)) or '—'
    subject_list.short_description = 'Subjects'

    def avg_rating(self, obj):
        avg = obj.reviews.aggregate(a=Avg('rating'))['a']
        return f'{avg:.1f}★' if avg else '—'
    avg_rating.short_description = 'Avg Rating'

    def review_count(self, obj):
        return obj.reviews.count()
    review_count.short_description = 'Reviews'


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'subject_list')
    search_fields = ('user__email', 'user__first_name')
    filter_horizontal = ('subjects',)

    def subject_list(self, obj):
        return ', '.join(obj.subjects.values_list('name', flat=True)) or '—'
    subject_list.short_description = 'Subjects Needed'


@admin.register(Availability)
class AvailabilityAdmin(admin.ModelAdmin):
    list_display = ('tutor', 'date', 'start_time', 'end_time')
    list_filter = ('date',)
    search_fields = ('tutor__user__email',)
    date_hierarchy = 'date'


@admin.register(Slot)
class SlotAdmin(admin.ModelAdmin):
    list_display = ('tutor', 'start_time', 'end_time', 'is_booked')
    list_filter = ('is_booked',)
    search_fields = ('tutor__user__email',)
    date_hierarchy = 'start_time'


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('student', 'tutor_name', 'slot_time', 'created_at')
    search_fields = ('student__email', 'slot__tutor__user__email')
    list_filter = ('created_at',)

    def tutor_name(self, obj):
        return obj.slot.tutor.user.get_full_name() or obj.slot.tutor.user.email
    tutor_name.short_description = 'Tutor'

    def slot_time(self, obj):
        return obj.slot.start_time.strftime('%Y-%m-%d %H:%M')
    slot_time.short_description = 'Session Time'


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('student', 'tutor', 'rating', 'created_at')
    list_filter = ('rating',)
    search_fields = ('student__email', 'tutor__user__email')
    date_hierarchy = 'created_at'
