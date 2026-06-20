from django.contrib.auth.models import User
from django.db.models import Avg, Count
from rest_framework import serializers
from peer_tutor.models import (
    Subject, Tutor, StudentProfile,
    Slot, Booking, Availability, Review, UserProfile,
)


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['id', 'name']


class UserBriefSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'full_name', 'email']

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.email


class ReviewSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ['id', 'student_name', 'rating', 'comment', 'created_at', 'updated_at']
        read_only_fields = ['id', 'student_name', 'created_at', 'updated_at']

    def get_student_name(self, obj):
        return obj.student.get_full_name() or obj.student.email


class ReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['rating', 'comment']

    def validate_rating(self, value):
        if not (1 <= value <= 5):
            raise serializers.ValidationError('Rating must be between 1 and 5.')
        return value


class TutorListSerializer(serializers.ModelSerializer):
    user = UserBriefSerializer(read_only=True)
    subjects = SubjectSerializer(many=True, read_only=True)
    avg_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()

    class Meta:
        model = Tutor
        fields = ['id', 'user', 'subjects', 'bio', 'avg_rating', 'review_count']

    def get_avg_rating(self, obj):
        result = getattr(obj, '_avg_rating', None)
        if result is None:
            result = obj.reviews.aggregate(avg=Avg('rating'))['avg']
        return round(result, 1) if result else None

    def get_review_count(self, obj):
        result = getattr(obj, '_review_count', None)
        if result is None:
            result = obj.reviews.count()
        return result


class TutorDetailSerializer(TutorListSerializer):
    reviews = ReviewSerializer(many=True, read_only=True)

    class Meta(TutorListSerializer.Meta):
        fields = TutorListSerializer.Meta.fields + ['reviews', 'contact_info']


class SlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Slot
        fields = ['id', 'start_time', 'end_time', 'is_booked']


class BookingSerializer(serializers.ModelSerializer):
    slot = SlotSerializer(read_only=True)
    tutor_name = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = ['id', 'slot', 'tutor_name', 'created_at']

    def get_tutor_name(self, obj):
        u = obj.slot.tutor.user
        return u.get_full_name() or u.email


class BookingCreateSerializer(serializers.Serializer):
    slot_id = serializers.IntegerField()

    def validate_slot_id(self, value):
        from django.utils import timezone
        try:
            slot = Slot.objects.get(id=value)
        except Slot.DoesNotExist:
            raise serializers.ValidationError('Slot not found.')
        if slot.is_booked:
            raise serializers.ValidationError('This slot is already booked.')
        if slot.start_time < timezone.now():
            raise serializers.ValidationError('Cannot book a slot in the past.')
        return value


class UserRegistrationSerializer(serializers.Serializer):
    ROLE_CHOICES = ['student', 'tutor', 'both']

    name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    role = serializers.ChoiceField(choices=ROLE_CHOICES)

    def validate_email(self, value):
        email = value.strip().lower()
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError('An account with this email already exists.')
        return email

    def create(self, validated_data):
        email = validated_data['email'].lower()
        user = User.objects.create_user(
            username=email,
            email=email,
            password=validated_data['password'],
            first_name=validated_data['name'].strip(),
        )
        role = validated_data['role']
        UserProfile.objects.create(user=user, role=role)
        if role in ('tutor', 'both'):
            Tutor.objects.get_or_create(user=user)
        if role in ('student', 'both'):
            StudentProfile.objects.get_or_create(user=user)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    is_tutor = serializers.SerializerMethodField()
    is_student = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'role', 'is_tutor', 'is_student']

    def get_role(self, obj):
        try:
            return obj.userprofile.role
        except Exception:
            return None

    def get_is_tutor(self, obj):
        return Tutor.objects.filter(user=obj).exists()

    def get_is_student(self, obj):
        return StudentProfile.objects.filter(user=obj).exists()


class AvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Availability
        fields = ['id', 'date', 'start_time', 'end_time']
