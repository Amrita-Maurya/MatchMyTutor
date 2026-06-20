from django.db import models
from django.contrib.auth.models import User


class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ['name']
        indexes = [models.Index(fields=['name'])]

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('tutor', 'Tutor'),
        ('both', 'Both'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    bio = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

    def is_tutor(self):
        return self.role in ('tutor', 'both')

    def is_student(self):
        return self.role in ('student', 'both')


class Tutor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    subjects_can_teach = models.TextField(
        help_text="Legacy CSV subjects field", null=True, blank=True
    )
    subjects = models.ManyToManyField(Subject, blank=True, related_name='tutors')
    contact_info = models.CharField(max_length=255, null=True, blank=True)
    bio = models.TextField(blank=True)

    class Meta:
        indexes = [models.Index(fields=['user'])]

    def __str__(self):
        return f"{self.user.username}'s Tutor Profile"

    def get_subjects_list(self):
        subject_names = list(self.subjects.values_list('name', flat=True))
        if not subject_names and self.subjects_can_teach:
            subject_names = [s.strip() for s in self.subjects_can_teach.split(',') if s.strip()]
        return subject_names

    def average_rating(self):
        from django.db.models import Avg
        result = self.reviews.aggregate(avg=Avg('rating'))['avg']
        return round(result, 1) if result else None

    def review_count(self):
        return self.reviews.count()


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    subjects_needed = models.TextField(
        help_text="Legacy CSV subjects field", null=True, blank=True
    )
    subjects = models.ManyToManyField(Subject, blank=True, related_name='students')
    contact_info = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=['user'])]

    def __str__(self):
        return f"{self.user.username}'s Student Profile"


class Slot(models.Model):
    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE, related_name='slots')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_booked = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ['start_time']
        indexes = [
            models.Index(fields=['tutor', 'is_booked']),
            models.Index(fields=['start_time']),
        ]

    def __str__(self):
        return f"{self.tutor.user.username} — {self.start_time:%Y-%m-%d %H:%M} to {self.end_time:%H:%M}"


class Booking(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    slot = models.OneToOneField(Slot, on_delete=models.CASCADE, related_name='booking')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['student'])]

    def __str__(self):
        return f"Booking by {self.student.username} for {self.slot}"


class Availability(models.Model):
    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE, related_name='availabilities')
    date = models.DateField(null=True, db_index=True)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ['date', 'start_time']
        unique_together = [('tutor', 'date', 'start_time', 'end_time')]
        indexes = [models.Index(fields=['tutor', 'date'])]

    def __str__(self):
        return f"{self.tutor.user.username} — {self.date}: {self.start_time}–{self.end_time}"


class Review(models.Model):
    RATING_CHOICES = [(i, f'{i} Star{"s" if i > 1 else ""}') for i in range(1, 6)]

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_given')
    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = [('student', 'tutor')]
        indexes = [
            models.Index(fields=['tutor']),
            models.Index(fields=['student']),
        ]

    def __str__(self):
        return f"Review by {self.student.username} for {self.tutor} — {self.rating}★"

    def star_range(self):
        return range(1, 6)
