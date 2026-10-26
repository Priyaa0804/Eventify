
from rest_framework import generics, permissions
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status as http_status

from .models import User, Club, Venue, EventRequest, Approval, Notification
from .serializers import (
    RegisterSerializer,
    CustomTokenObtainPairSerializer,
    UserSerializer,
    ClubSerializer,
    VenueSerializer,
    EventRequestSerializer,
    ApprovalActionSerializer,
    CalendarEventSerializer,
    NotificationSerializer,
)
from .permissions import IsStudent, IsFacultyOrHOD
from .notifications import notify


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []


class MeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class DeactivateAccountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        user.is_active = False
        user.save(update_fields=['is_active'])

        return Response(
            {"detail": "Your account has been deactivated."},
            status=http_status.HTTP_200_OK,
        )


class ClubListView(generics.ListAPIView):
    queryset = Club.objects.all().order_by('name')
    serializer_class = ClubSerializer
    authentication_classes = []
    permission_classes = [permissions.AllowAny]


class VenueListCreateView(generics.ListCreateAPIView):
    queryset = Venue.objects.filter(is_active=True)
    serializer_class = VenueSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsFacultyOrHOD()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class EventRequestCreateView(generics.CreateAPIView):
    serializer_class = EventRequestSerializer
    permission_classes = [IsStudent]

    def get_serializer_context(self):
        return {'request': self.request}


class MyEventRequestsView(generics.ListAPIView):
    serializer_class = EventRequestSerializer
    permission_classes = [IsStudent]

    def get_queryset(self):
        return EventRequest.objects.filter(
            requested_by=self.request.user,
        )


class PendingApprovalsView(generics.ListAPIView):
    serializer_class = EventRequestSerializer
    permission_classes = [IsFacultyOrHOD]

    def get_queryset(self):
        return EventRequest.objects.filter(
            current_approver=self.request.user,
        )


class ApproveEventView(APIView):
    permission_classes = [IsFacultyOrHOD]

    def post(self, request, pk):
        try:
            event = EventRequest.objects.get(pk=pk)
        except EventRequest.DoesNotExist:
            return Response(
                {"detail": "Not found."},
                status=http_status.HTTP_404_NOT_FOUND,
            )

        if event.status not in ['PENDING_FACULTY', 'PENDING_HOD']:
            return Response(
                {"detail": "This request is not awaiting approval."},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        if event.current_approver_id != request.user.id:
            return Response(
                {"detail": "You are not authorized to act on this request."},
                status=http_status.HTTP_403_FORBIDDEN,
            )

        if event.status == 'PENDING_FACULTY':
            Approval.objects.create(
                event_request=event,
                approver=request.user,
                stage='FACULTY',
                action='APPROVED',
            )

            hod = event.club.hod
            event.status = 'PENDING_HOD'
            event.current_approver = hod
            event.save(
                update_fields=['status', 'current_approver', 'updated_at']
            )

            notify(
                event.requested_by,
                event,
                f"Update: {event.event_name}",
                "Your request was approved by the Faculty Advisor "
                "and is now with the HOD.",
            )

            if hod:
                notify(
                    hod,
                    event,
                    f"Approval needed: {event.event_name}",
                    f"A new request '{event.event_name}' is awaiting "
                    "your approval.",
                )

        elif event.status == 'PENDING_HOD':
            Approval.objects.create(
                event_request=event,
                approver=request.user,
                stage='HOD',
                action='APPROVED',
            )

            event.status = 'APPROVED'
            event.current_approver = None
            event.save(
                update_fields=['status', 'current_approver', 'updated_at']
            )

            notify(
                event.requested_by,
                event,
                f"Approved: {event.event_name}",
                f"Your event '{event.event_name}' has been fully "
                "approved. The venue is confirmed.",
            )

        return Response(EventRequestSerializer(event).data)


class RejectEventView(APIView):
    permission_classes = [IsFacultyOrHOD]

    def post(self, request, pk):
        serializer = ApprovalActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = serializer.validated_data.get('comment', '')

        if not comment:
            return Response(
                {"detail": "A comment is required when rejecting."},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        try:
            event = EventRequest.objects.get(pk=pk)
        except EventRequest.DoesNotExist:
            return Response(
                {"detail": "Not found."},
                status=http_status.HTTP_404_NOT_FOUND,
            )

        if event.status not in ['PENDING_FACULTY', 'PENDING_HOD']:
            return Response(
                {"detail": "This request is not awaiting approval."},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        if event.current_approver_id != request.user.id:
            return Response(
                {"detail": "You are not authorized to act on this request."},
                status=http_status.HTTP_403_FORBIDDEN,
            )

        stage = (
            'FACULTY'
            if event.status == 'PENDING_FACULTY'
            else 'HOD'
        )

        Approval.objects.create(
            event_request=event,
            approver=request.user,
            stage=stage,
            action='REJECTED',
            comment=comment,
        )

        event.status = 'REJECTED'
        event.current_approver = None
        event.save(
            update_fields=['status', 'current_approver', 'updated_at']
        )

        notify(
            event.requested_by,
            event,
            f"Rejected: {event.event_name}",
            f"Your request '{event.event_name}' was rejected. "
            f"Reason: {comment}",
        )

        return Response(EventRequestSerializer(event).data)


class CancelEventView(APIView):
    permission_classes = [IsStudent]

    def post(self, request, pk):
        try:
            event = EventRequest.objects.get(pk=pk)
        except EventRequest.DoesNotExist:
            return Response(
                {"detail": "Not found."},
                status=http_status.HTTP_404_NOT_FOUND,
            )

        if event.requested_by_id != request.user.id:
            return Response(
                {"detail": "You can only cancel your own requests."},
                status=http_status.HTTP_403_FORBIDDEN,
            )

        if event.status not in ['PENDING_FACULTY', 'PENDING_HOD']:
            return Response(
                {"detail": "Only pending requests can be cancelled."},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        event.status = 'CANCELLED'
        event.current_approver = None
        event.save(
            update_fields=['status', 'current_approver', 'updated_at']
        )

        return Response(EventRequestSerializer(event).data)


class CalendarEventsView(generics.ListAPIView):
    serializer_class = CalendarEventSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return EventRequest.objects.filter(status='APPROVED')


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(
            user=self.request.user
        ).select_related('event_request')


class NotificationMarkReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        notification = Notification.objects.filter(
            pk=pk,
            user=request.user,
        ).first()

        if notification is None:
            return Response(
                {"detail": "Notification not found."},
                status=http_status.HTTP_404_NOT_FOUND,
            )

        if not notification.is_read:
            notification.is_read = True
            notification.save(update_fields=['is_read'])

        return Response({
            "detail": "Notification marked as read.",
            "id": notification.id,
            "is_read": notification.is_read,
        })


class NotificationMarkAllReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        updated_count = Notification.objects.filter(
            user=request.user,
            is_read=False,
        ).update(is_read=True)

        return Response({
            "detail": "All notifications marked as read.",
            "updated_count": updated_count,
        })


class NotificationUnreadCountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        unread_count = Notification.objects.filter(
            user=request.user,
            is_read=False,
        ).count()

        return Response({
            "unread_count": unread_count,
        })
