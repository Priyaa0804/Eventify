from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('STUDENT', 'Student'),
        ('FACULTY_ADVISOR', 'Faculty Advisor'),
        ('HOD', 'Head of Department'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    department = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.username} ({self.role})"


class Club(models.Model):
    name = models.CharField(max_length=150)
    faculty_advisor = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='advised_clubs'
    )
    hod = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='headed_clubs'
    )
    department = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Venue(models.Model):
    name = models.CharField(max_length=150)
    capacity = models.IntegerField()
    location = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class EventRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING_FACULTY', 'Pending Faculty Advisor'),
        ('PENDING_HOD', 'Pending HOD'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    ]

    club = models.ForeignKey(Club, on_delete=models.CASCADE)
    requested_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='event_requests'
    )
    event_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE)
    event_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    expected_participants = models.IntegerField(null=True, blank=True)
    additional_requirements = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING_FACULTY')
    current_approver = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='pending_approvals'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.event_name} ({self.status})"


class Approval(models.Model):
    STAGE_CHOICES = [('FACULTY', 'Faculty Advisor'), ('HOD', 'HOD')]
    ACTION_CHOICES = [('APPROVED', 'Approved'), ('REJECTED', 'Rejected')]

    event_request = models.ForeignKey(
        EventRequest, on_delete=models.CASCADE, related_name='approvals'
    )
    approver = models.ForeignKey(User, on_delete=models.CASCADE)
    stage = models.CharField(max_length=10, choices=STAGE_CHOICES)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    comment = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.event_request.event_name} - {self.stage} - {self.action}"


class Notification(models.Model):
    STATUS_CHOICES = [('SENT', 'Sent'), ('FAILED', 'Failed')]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event_request = models.ForeignKey(EventRequest, on_delete=models.CASCADE)
    message = models.TextField()
    sent_status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    sent_at = models.DateTimeField(auto_now_add=True)