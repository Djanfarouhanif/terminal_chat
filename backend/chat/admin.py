from django.contrib import admin

from .models import Channel, DirectMessage, Message

admin.site.register(Channel)
admin.site.register(Message)
admin.site.register(DirectMessage)
