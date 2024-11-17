from django.db import models
from django.contrib.auth.models import User

# class Student(models.Model):
#     name = models.CharField(max_length=100)
#     email = models.EmailField()
#     password = models.CharField(max_length=200)

#     def __str__(self):
#         return self.name

class Tutor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    subjects_can_teach = models.TextField(help_text="Subjects you can teach", null=True)
    contact_info = models.CharField(max_length=255, help_text="Your contact information", null=True)

    def __str__(self):
        return f"{self.user.username}'s Tutor Profile"

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    subjects_needed = models.TextField(help_text="Subjects you need help with", null=True)
    contact_info = models.CharField(max_length=255, help_text="Your contact information", null=True)

    def __str__(self):
        return f"{self.user.username}'s Student Profile"
    

class Slot(models.Model):
    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_booked = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.tutor.user.username} - {self.start_time} to {self.end_time}"


class Booking(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    slot = models.ForeignKey(Slot, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f"Booking by {self.student.username} for {self.slot}"


class Event(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    def __str__(self):
        return f"Event for {self.user.username} from {self.start_time} to {self.end_time}"


class Availability(models.Model):
    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE)
    date = models.DateField(null=True) 
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.tutor.user.username} - {self.date}: {self.start_time} to {self.end_time}"