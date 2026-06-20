from .models import UserProfile, Tutor, StudentProfile


def user_role_context(request):
    if not request.user.is_authenticated:
        return {}
    return {
        'user_profile': UserProfile.objects.filter(user=request.user).first(),
        'is_tutor': Tutor.objects.filter(user=request.user).exists(),
        'is_student': StudentProfile.objects.filter(user=request.user).exists(),
    }
