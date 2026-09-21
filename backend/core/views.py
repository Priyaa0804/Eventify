from django.shortcuts import render
from rest_framework import generics, permissions, viewsets
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import User, Venue, EventRequest, Approval
from .serializers import RegisterSerializer, CustomTokenObtainPairSerializer, UserSerializer, VenueSerializer, EventRequestSerializer, ApprovalActionSerializer, CalendarEventSerializer
from .permissions import IsStudent, IsFacultyOrHOD
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status as http_status
from .notifications import notify


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class MeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


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
        return EventRequest.objects.filter(requested_by=self.request.user)


class PendingApprovalsView(generics.ListAPIView):
    serializer_class = EventRequestSerializer
    permission_classes = [IsFacultyOrHOD]

    def get_queryset(self):
        return EventRequest.objects.filter(current_approver=self.request.user)


class ApproveEventView(APIView):
    permission_classes = [IsFacultyOrHOD]

    def post(self, request, pk):
        try:
            event = EventRequest.objects.get(pk=pk)
        except EventRequest.DoesNotExist:
            return Response({"detail": "Not found."}, status=http_status.HTTP_404_NOT_FOUND)

        if event.status not in ['PENDING_FACULTY', 'PENDING_HOD']:
            return Response(
                {"detail": "This request is not awaiting approval."},
                status=http_status.HTTP_400_BAD_REQUEST
            )

        if event.current_approver_id != request.user.id:
            return Response(
                {"detail": "You are not authorized to act on this request."},
                status=http_status.HTTP_403_FORBIDDEN
            )

        if event.status == 'PENDING_FACULTY':
            Approval.objects.create(
                event_request=event, approver=request.user,
                stage='FACULTY', action='APPROVED'
            )
            hod = User.objects.filter(role='HOD', department=event.club.department).first()
            event.status = 'PENDING_HOD'
            event.current_approver = hod
            event.save()

            notify(
                event.requested_by, event,
                f"Update: {event.event_name}",
                "Your request was approved by the Faculty Advisor and is now with the HOD."
            )
            if hod:
                notify(
                    hod, event,
                    f"Approval needed: {event.event_name}",
                    f"A new request '{event.event_name}' is awaiting your approval."
                )

        elif event.status == 'PENDING_HOD':
            Approval.objects.create(
                event_request=event, approver=request.user,
                stage='HOD', action='APPROVED'
            )
            event.status = 'APPROVED'
            event.current_approver = None
            event.save()

            notify(
                event.requested_by, event,
                f"Approved: {event.event_name}",
                f"Your event '{event.event_name}' has been fully approved. The venue is confirmed."
            )

        return Response(EventRequestSerializer(event).data)


class RejectEventView(APIView):
    permission_classes = [IsFacultyOrHOD]

    def post(self, request, pk):
        serializer = ApprovalActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = serializer.validated_data.get('comment', '')

        if not comment:
            return Response({"detail": "A comment is required when rejecting."}, status=http_status.HTTP_400_BAD_REQUEST)

        try:
            event = EventRequest.objects.get(pk=pk)
        except EventRequest.DoesNotExist:
            return Response({"detail": "Not found."}, status=http_status.HTTP_404_NOT_FOUND)

        if event.status not in ['PENDING_FACULTY', 'PENDING_HOD']:
            return Response(
                {"detail": "This request is not awaiting approval."},
                status=http_status.HTTP_400_BAD_REQUEST
            )

        if event.current_approver_id != request.user.id:
            return Response(
                {"detail": "You are not authorized to act on this request."},
                status=http_status.HTTP_403_FORBIDDEN
            )

        stage = 'FACULTY' if event.status == 'PENDING_FACULTY' else 'HOD'
        Approval.objects.create(
            event_request=event, approver=request.user,
            stage=stage, action='REJECTED', comment=comment
        )
        event.status = 'REJECTED'
        event.current_approver = None
        event.save()

        notify(
            event.requested_by, event,
            f"Rejected: {event.event_name}",
            f"Your request '{event.event_name}' was rejected. Reason: {comment}"
        )

        return Response(EventRequestSerializer(event).data)


class CancelEventView(APIView):
    permission_classes = [IsStudent]

    def post(self, request, pk):
        try:
            event = EventRequest.objects.get(pk=pk)
        except EventRequest.DoesNotExist:
            return Response({"detail": "Not found."}, status=http_status.HTTP_404_NOT_FOUND)

        if event.requested_by_id != request.user.id:
            return Response(
                {"detail": "You can only cancel your own requests."},
                status=http_status.HTTP_403_FORBIDDEN
            )

        if event.status not in ['PENDING_FACULTY', 'PENDING_HOD']:
            return Response(
                {"detail": "Only pending requests can be cancelled."},
                status=http_status.HTTP_400_BAD_REQUEST
            )

        event.status = 'CANCELLED'
        event.current_approver = None
        event.save()

        return Response(EventRequestSerializer(event).data)


class CalendarEventsView(generics.ListAPIView):
    serializer_class = CalendarEventSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return EventRequest.objects.filter(status='APPROVED')