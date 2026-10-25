from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User, Venue, EventRequest, Club
from .notifications import notify


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    club = serializers.PrimaryKeyRelatedField(
        queryset=Club.objects.all(), required=False, write_only=True
    )

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'role', 'department', 'club']

    def validate(self, data):
        role = data.get('role')
        club = data.get('club')

        if role in ['FACULTY_ADVISOR', 'HOD']:
            if not club:
                raise serializers.ValidationError(
                    {"club": "Club is required when registering as Faculty Advisor or HOD."}
                )
            if role == 'FACULTY_ADVISOR' and club.faculty_advisor and club.faculty_advisor.is_active:
                raise serializers.ValidationError(
                    {"club": f"This club already has a Faculty Advisor ({club.faculty_advisor.username}). "
                             "Ask them to deactivate their account, then try registering again."}
                )
            if role == 'HOD' and club.hod and club.hod.is_active:
                raise serializers.ValidationError(
                    {"club": f"This club already has a HOD ({club.hod.username}). "
                             "Ask them to deactivate their account, then try registering again."}
                )
        elif club:
            raise serializers.ValidationError(
                {"club": "Only Faculty Advisor or HOD registration should include a club."}
            )

        return data

    def create(self, validated_data):
        club = validated_data.pop('club', None)
        role = validated_data['role']
        department = club.department if club else validated_data.get('department', '')

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            role=role,
            department=department,
        )

        if club:
            old_holder = club.faculty_advisor if role == 'FACULTY_ADVISOR' else club.hod

            if role == 'FACULTY_ADVISOR':
                club.faculty_advisor = user
            else:
                club.hod = user
            club.save()

            # Hand off any pending approvals stuck on the deactivated predecessor
            if old_holder:
                EventRequest.objects.filter(
                    club=club,
                    current_approver=old_holder,
                    status__in=['PENDING_FACULTY', 'PENDING_HOD'],
                ).update(current_approver=user)

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
        fields = ['id', 'username', 'email', 'role', 'department']


class VenueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Venue
        fields = ['id', 'name', 'capacity', 'location', 'is_active']


class EventRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventRequest
        fields = [
            'id', 'club', 'event_name', 'description', 'venue',
            'event_date', 'start_time', 'end_time',
            'expected_participants', 'additional_requirements',
            'status', 'current_approver', 'created_at',
        ]
        read_only_fields = ['status', 'current_approver', 'created_at']

    def validate(self, data):
        start_time = data['start_time']
        end_time = data['end_time']

        if end_time <= start_time:
            raise serializers.ValidationError("End time must be after start time.")

        conflict_exists = EventRequest.objects.filter(
            venue=data['venue'],
            event_date=data['event_date'],
        ).exclude(
            status__in=['REJECTED', 'CANCELLED']
        ).filter(
            start_time__lt=end_time,
            end_time__gt=start_time
        ).exists()

        if conflict_exists:
            raise serializers.ValidationError(
                "This venue is already booked or requested for an overlapping time slot."
            )

        return data

    def create(self, validated_data):
        club = validated_data['club']
        event_request = EventRequest.objects.create(
            **validated_data,
            requested_by=self.context['request'].user,
            status='PENDING_FACULTY',
            current_approver=club.faculty_advisor,
        )
        notify(
            club.faculty_advisor, event_request,
            f"New event request: {event_request.event_name}",
            f"{event_request.requested_by.username} submitted '{event_request.event_name}' "
            f"for {event_request.venue.name} on {event_request.event_date}. Please review."
        )
        return event_request


class ApprovalActionSerializer(serializers.Serializer):
    comment = serializers.CharField(required=False, allow_blank=True)


class CalendarEventSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    start = serializers.SerializerMethodField()
    end = serializers.SerializerMethodField()

    class Meta:
        model = EventRequest
        fields = ['title', 'start', 'end']

    def get_title(self, obj):
        return f"{obj.event_name} — {obj.venue.name}"

    def get_start(self, obj):
        return f"{obj.event_date}T{obj.start_time}"

    def get_end(self, obj):
        return f"{obj.event_date}T{obj.end_time}"