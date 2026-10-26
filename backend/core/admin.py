from django.contrib import admin
from .models import User, Club, Venue, EventRequest, Approval, Notification

admin.site.register(User)
admin.site.register(Club)
admin.site.register(Venue)
admin.site.register(EventRequest)
admin.site.register(Approval)
admin.site.register(Notification)