from django.contrib import admin
from chats_notifications.models import (
    UserModel,
    ConversationModel,
    ChatModel,
)
# Register your models here.


@admin.register(UserModel)
class UserModelAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "user_name")
    search_fields = ("id", "email", "user_name")


@admin.register(ConversationModel)
class ConversationModelAdmin(admin.ModelAdmin):
    list_display = ("id", )
    search_fields = ("id",)

@admin.register(ChatModel)
class ChatModelAdmin(admin.ModelAdmin):
    list_display = ("id", "sender", "receiver")
    search_fields = ("id", "sender", "receiver")