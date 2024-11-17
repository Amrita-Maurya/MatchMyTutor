from django.contrib import admin


from .models import  Tutor, StudentProfile, Slot, Booking, Availability, Event


admin.site.register(Tutor)
admin.site.register(Booking)
admin.site.register(StudentProfile)
admin.site.register(Slot)
admin.site.register(Availability)
admin.site.register(Event)
