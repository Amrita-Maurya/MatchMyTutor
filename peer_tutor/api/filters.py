import django_filters
from django.db.models import Avg
from peer_tutor.models import Tutor, Slot


class TutorFilter(django_filters.FilterSet):
    subject = django_filters.CharFilter(
        field_name='subjects__name',
        lookup_expr='icontains',
        label='Subject (contains)',
    )
    min_rating = django_filters.NumberFilter(
        method='filter_min_rating',
        label='Minimum average rating (1–5)',
    )
    search = django_filters.CharFilter(
        method='filter_search',
        label='Search by name',
    )

    class Meta:
        model = Tutor
        fields = ['subject', 'min_rating', 'search']

    def filter_min_rating(self, queryset, name, value):
        return queryset.annotate(avg_r=Avg('reviews__rating')).filter(avg_r__gte=value)

    def filter_search(self, queryset, name, value):
        from django.db.models import Q
        return queryset.filter(
            Q(user__first_name__icontains=value) |
            Q(user__last_name__icontains=value) |
            Q(user__email__icontains=value)
        )


class SlotFilter(django_filters.FilterSet):
    date = django_filters.DateFilter(field_name='start_time__date', label='Date (YYYY-MM-DD)')
    from_datetime = django_filters.DateTimeFilter(field_name='start_time', lookup_expr='gte')

    class Meta:
        model = Slot
        fields = ['date', 'from_datetime']
