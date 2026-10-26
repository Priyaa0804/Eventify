
from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User, Venue, EventRequest, Club, Notification
from .notifications import notify


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8,
    )

    club = serializers.PrimaryKeyRelatedField(
        queryset=Club.objects.all(),
        required=True,
        write_only=True,
    )

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'password',
            'department',
            'club',
        ]
        read_only_fields = ['id']

    def validate(self, data):
        club = data.get('club')

        if not club:
            raise serializers.ValidationError({
                'club': 'Please select a club.'
            })

        # Public registrations can only create Student accounts.
        data['role'] = 'STUDENT'
        data['department'] = club.department

        return data

    @transaction.atomic
    def create(self, validated_data):
        validated_data.pop('club')

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            role='STUDENT',
            department=validated_data['department'],
        )

        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = user.role
        token['department'] = user.department
        return token


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'role',
            'department',
        ]


class ClubSerializer(serializers.ModelSerializer):
    class Meta:
        model = Club
        fields = ['id', 'name', 'department']


class VenueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Venue
        fields = [
            'id',
            'name',
            'capacity',
            'location',
            'is_active',
        ]


class EventRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventRequest
        fields = [
            'id',
            'club',
            'event_name',
            'description',
            'venue',
            'event_date',
            'start_time',
            'end_time',
            'expected_participants',
            'additional_requirements',
            'status',
            'current_approver',
            'created_at',
        ]
        read_only_fields = [
            'status',
            'current_approver',
            'created_at',
        ]

    def validate(self, data):
        venue = data.get('venue')
        event_date = data.get('event_date')
        start_time = data.get('start_time')
        end_time = data.get('end_time')

        if start_time is not None and end_time is not None:
            if end_time <= start_time:
                raise serializers.ValidationError({
                    'end_time': 'End time must be after start time.'
                })

        if venue is not None and not venue.is_active:
            raise serializers.ValidationError({
                'venue': 'This venue is inactive and cannot be booked.'
            })

        if (
            venue is not None
            and event_date is not None
            and start_time is not None
            and end_time is not None
        ):
            conflict_exists = EventRequest.objects.filter(
                venue=venue,
                event_date=event_date,
                start_time__lt=end_time,
                end_time__gt=start_time,
            ).exclude(
                status__in=['REJECTED', 'CANCELLED']
            ).exists()

            if conflict_exists:
                raise serializers.ValidationError({
                    'non_field_errors': [
                        'This venue is already booked or requested '
                        'for an overlapping time slot.'
                    ]
                })

        return data

    def create(self, validated_data):
        club = validated_data['club']

        event_request = EventRequest.objects.create(
            **validated_data,
            requested_by=self.context['request'].user,
            status='PENDING_FACULTY',
            current_approver=club.faculty_advisor,
        )

        if club.faculty_advisor:
            notify(
                club.faculty_advisor,
                event_request,
                f'New event request: {event_request.event_name}',
                f'{event_request.requested_by.username} submitted '
                f"'{event_request.event_name}' for "
                f'{event_request.venue.name} on '
                f'{event_request.event_date}. Please review.',
            )

        return event_request


class ApprovalActionSerializer(serializers.Serializer):
    comment = serializers.CharField(
        required=False,
        allow_blank=True,
    )


class CalendarEventSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    start = serializers.SerializerMethodField()
    end = serializers.SerializerMethodField()

    class Meta:
        model = EventRequest
        fields = [
            'title',
            'start',
            'end',
        ]

    def get_title(self, obj):
        return f'{obj.event_name} — {obj.venue.name}'

    def get_start(self, obj):
        return f'{obj.event_date}T{obj.start_time}'

    def get_end(self, obj):
        return f'{obj.event_date}T{obj.end_time}'


class NotificationSerializer(serializers.ModelSerializer):
    event_name = serializers.CharField(
        source='event_request.event_name',
        read_only=True,
    )

    class Meta:
        model = Notification
        fields = [
            'id',
            'event_request',
            'event_name',
            'message',
            'sent_status',
            'is_read',
            'sent_at',
        ]
        read_only_fields = fields
