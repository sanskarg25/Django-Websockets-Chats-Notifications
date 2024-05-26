from django.urls import path
from chats_notifications.views import (
    ApplicationsChatsGenerateURLAPI,
)

urlpatterns = [
    path(
        "generate-file-url-api/",
        ApplicationsChatsGenerateURLAPI.as_view(),
        name="ApplicationsChatsGenerateURLAPIView",
    )
]
