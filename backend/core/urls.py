
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    RegisterView,
    CustomTokenObtainPairView,
    MeView,
    DeactivateAccountView,
    ClubListView,
    VenueListCreateView,
    EventRequestCreateView,
    MyEventRequestsView,
    PendingApprovalsView,
    ApproveEventView,
    RejectEventView,
    CancelEventView,
    CalendarEventsView,
    NotificationListView,
    NotificationMarkReadView,
    NotificationMarkAllReadView,
    NotificationUnreadCountView,
)

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/me/', MeView.as_view(), name='me'),
    path('auth/deactivate/', DeactivateAccountView.as_view(), name='deactivate'),

    path('clubs/', ClubListView.as_view(), name='clubs'),
    path('venues/', VenueListCreateView.as_view(), name='venues'),

    path('events/', EventRequestCreateView.as_view(), name='create-event'),
    path('events/my/', MyEventRequestsView.as_view(), name='my-events'),

    path(
        'approvals/pending/',
        PendingApprovalsView.as_view(),
        name='pending-approvals',
    ),
    path(
        'events/<int:pk>/approve/',
        ApproveEventView.as_view(),
        name='approve-event',
    ),
    path(
        'events/<int:pk>/reject/',
        RejectEventView.as_view(),
        name='reject-event',
    ),
    path(
        'events/<int:pk>/cancel/',
        CancelEventView.as_view(),
        name='cancel-event',
    ),

    path(
        'calendar/events/',
        CalendarEventsView.as_view(),
        name='calendar-events',
    ),

    path(
        'notifications/',
        NotificationListView.as_view(),
        name='notifications',
    ),
    path(
        'notifications/read-all/',
        NotificationMarkAllReadView.as_view(),
        name='notifications-read-all',
    ),
    path(
        'notifications/<int:pk>/read/',
        NotificationMarkReadView.as_view(),
        name='notification-mark-read',
    ),
    path(
        'notifications/unread-count/',
        NotificationUnreadCountView.as_view(),
        name='notifications-unread-count',
    ),
]
