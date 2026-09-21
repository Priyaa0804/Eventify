from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (RegisterView, CustomTokenObtainPairView, MeView, VenueListCreateView, EventRequestCreateView, MyEventRequestsView, PendingApprovalsView, ApproveEventView, RejectEventView, CancelEventView, CalendarEventsView)

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/me/', MeView.as_view(), name='me'),
    path('venues/', VenueListCreateView.as_view(), name='venues'),
    path('events/', EventRequestCreateView.as_view(), name='create-event'),
    path('events/my/', MyEventRequestsView.as_view(), name='my-events'),
     path('approvals/pending/', PendingApprovalsView.as_view(), name='pending-approvals'),
    path('events/<int:pk>/approve/', ApproveEventView.as_view(), name='approve-event'),
    path('events/<int:pk>/reject/', RejectEventView.as_view(), name='reject-event'),
    path('events/<int:pk>/cancel/', CancelEventView.as_view(), name='cancel-event'),
     path('calendar/events/', CalendarEventsView.as_view(), name='calendar-events'),
]