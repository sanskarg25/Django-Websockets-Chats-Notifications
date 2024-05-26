import datetime, os
from websocket_chats_notifications.settings import (
    media_path,
    media_path_hosted,
    SERVER_HOST,
)
from django.core.files.base import ContentFile
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from itertools import chain
from chats_notifications.models import (
    UserModel,
    ConversationModel,
    ChatModel,
    NotificationsModel,
)


def create_path_new(file_path, sub_path=None, sub_sub_path=None):
    """
    Create default media path and a sub-directory if it doesnt exists
    """
    try:
        if not os.path.exists(os.path.join(os.path.abspath(os.curdir), media_path)):
            os.mkdir(os.path.join(os.path.abspath(os.curdir), media_path))
        if not os.path.exists(
            os.path.join(os.path.abspath(os.curdir), media_path, file_path)
        ):
            os.mkdir(os.path.join(os.path.abspath(os.curdir), media_path, file_path))
        if sub_path:
            if not os.path.exists(
                os.path.join(
                    os.path.abspath(os.curdir), media_path, file_path, sub_path
                )
            ):
                os.mkdir(
                    os.path.join(
                        os.path.abspath(os.curdir), media_path, file_path, sub_path
                    )
                )

            if sub_sub_path and not os.path.exists(
                os.path.join(
                    os.path.abspath(os.curdir),
                    media_path,
                    file_path,
                    sub_path,
                    sub_sub_path,
                )
            ):
                os.mkdir(
                    os.path.join(
                        os.path.abspath(os.curdir),
                        media_path,
                        file_path,
                        sub_path,
                        sub_sub_path,
                    )
                )
    except Exception as e:
        print(f"Error while creating path: {e}")


def save_image(file, path_req=None):
    """
    Save the images on server and return the server hosted link
    """
    if path_req:
        profile_path = path_req
    else:
        profile_path = "ChatFiles/"
    create_path_new(profile_path)
    curr_date = str(datetime.datetime.now().timestamp())
    profile_path_name = profile_path + curr_date + "." + file.name.split(".")[-1]
    file_name = os.path.join(os.path.abspath(os.curdir), media_path) + profile_path_name
    image_url = SERVER_HOST + media_path_hosted + profile_path_name
    file_type = file.name.split(".")[-1]
    name = file.name.split(".")[0]
    fout = open(file_name, "wb+")
    file_content = ContentFile(file.read())
    for chunk in file_content.chunks():
        fout.write(chunk)
    fout.close()
    print(f"Image Saved")
    return image_url, file_type, name, file.size


def direct_chat(user, conversation_id, next=False, l_id=None):
    """
    custom function for response socket of current going on chat
    """
    channel_layer = get_channel_layer()
    conversation_name = f"message_list_{conversation_id}__{user}"

    final_list = []
    all_files = []
    my_files = []
    unread_count = 0
    has_next_messages = False

    if next == False:
        chat_data = (
            ChatModel.objects.filter(
                conversation_id=conversation_id
            )
            .values()
            .order_by("-created_date")[:20]
        )
        if len(chat_data) > 0:
            chat_ids = list(chat_data.values_list("id", flat=True))
            if chat_ids:
                last_id = chat_ids[-1]
            else:
                last_id = None
            if last_id is not None:
                remaining_data = (
                    ChatModel.objects.filter(
                        conversation_id=conversation_id, id__lt=last_id
                    )
                    .exclude(id__in=chat_ids)
                    .order_by("-created_date")
                    .values()
                )
                if len(remaining_data) > 0:
                    has_next_messages = True
    else:
        last_10_messages = (
            ChatModel.objects.filter(
                conversation_id=conversation_id, id__gt=l_id
            )
            .values()
            .order_by("-created_date")
        )[:20]
        last_10_ids = last_10_messages.values_list("id", flat=True)

        chat_data = (
            ChatModel.objects.filter(
                conversation_id=conversation_id, id__lt=l_id
            )
            .exclude(id__in=last_10_ids)
            .order_by("-created_date")
            .values()[:20]
        )
        chat_ids = chat_data.values_list("id", flat=True)
        all_ids = list(chain(last_10_ids, chat_ids))

        remaining_data = (
            ChatModel.objects.filter(
                conversation_id=conversation_id, id__lt=l_id
            )
            .exclude(id__in=all_ids)
            .order_by("-created_date")
            .values()
        )
        if len(remaining_data) > 0:
            has_next_messages = True

    conversation_obj = ConversationModel.objects.get(
        id=conversation_id
    )
    if conversation_obj.self_chat == False:
        conversation_user = UserModel.objects.filter(
            id__in=conversation_obj.conversation_users
        ).exclude(id=user)[0]
    else:
        conversation_user = UserModel.objects.get(id=user)

    user_details = {
        "user_id": str(conversation_user.id),
        "username": conversation_user.user_name,
        "email": conversation_user.email,
        "status": conversation_user.status,
        "last_online": str(conversation_user.last_online),
    }

    if len(chat_data) > 0:
        for each in chat_data:
            user_obj = UserModel.objects.get(id=each["sender_id"])
            user_id = user_obj.id
            name = user_obj.user_name
            user_email = user_obj.email

            val = "receiver"
            is_sender = False
            if str(user) == str(each["sender_id"]):
                val = "sender"
                is_sender = True
                if each["files"] is not None:
                    for file in each["files"]:
                        my_files.append(file)
            obj = {
                "id": each["id"],
                f"{val}_id": str(user_id),
                f"{val}_name": name,
                f"{val}_email": user_email,
                "is_sender": is_sender,
                f"{val}_message": each["message"],
                f"{val}_files": each["files"],
                "read": each["read"],
                "is_edited": each["is_edited"],
                "is_deleted": each["is_deleted"],
                "is_pinned": each["is_pinned"],
                "is_reply": each["is_reply"],
                "reply_id": each["reply_id"],
                "reply_message": each["reply_message"],
                "reply_files": each["reply_files"],
                "created_date": str(each["created_date"]),
                "updated_date": str(each["updated_date"]),
            }

            if each["files"] is not None:
                for file in each["files"]:
                    all_files.append(file)

            if is_sender is False and each["is_deleted"] != True:
                final_list.append(obj)

            if is_sender is True:
                final_list.append(obj)

            if f"{val}_message" == "receiver_message" and each["read"] == False:
                unread_count += 1

    total_count = len(final_list)

    if next == False:
        async_to_sync(channel_layer.group_send)(
            conversation_name,
            {
                "type": "message_list",
                "conversation": conversation_name,
                "data": {
                    "total_count": total_count,
                    "unread_count": unread_count,
                    "conversation_id": str(conversation_id),
                    "username": conversation_user.user_name,
                    "messages": final_list,
                    "has_next_messages": has_next_messages,
                },
                "user_details": user_details,
            },
        )
    else:
        conversation_name = f"next_messages_{conversation_id}__{user}"
        async_to_sync(channel_layer.group_send)(
            conversation_name,
            {
                "type": "next_messages",
                "conversation": conversation_name,
                "data": {
                    "total_count": total_count,
                    "unread_count": unread_count,
                    "conversation_id": str(conversation_id),
                    "username": conversation_user.user_name,
                    "messages": final_list,
                    "has_next_messages": has_next_messages,
                },
                "user_details": user_details,
            },
        )


def notifications(user):
    """
    custom function for response socket of current user status
    """
    channel_layer = get_channel_layer()
    conversation_name = f"notifications_for_{user}"

    user_obj = UserModel.objects.get(id=str(user))
    unread_count = 0
    notifications_list = (
        NotificationsModel.objects.filter(
            receiver_user=user_obj, read=False
        )
        .values()
        .order_by("-created_date")
    )

    final_notifications = []
    if len(notifications_list) > 0:
        for each in notifications_list:
            notification_user_obj = UserModel.objects.get(
                id=each["notification_user_id"]
            )
            direct = False
            if ConversationModel.objects.filter(
                id=each["conversation_id"]
            ).exists():
                convo_obj = ConversationModel.objects.get(
                    id=each["conversation_id"]
                )
                if convo_obj.direct_chat is True:
                    direct = True
            obj = {
                "id": each["id"],
                "conversation_id": str(each["conversation_id"]),
                "user_id": str(notification_user_obj.id),
                "user_name": notification_user_obj.user_name,
                "message": each["message"],
                "read": each["read"],
                "direct": direct,
                "created_date": str(each["created_date"]),
                "updated_date": str(each["updated_date"]),
            }
            final_notifications.append(obj)
            if obj["read"] == False:
                unread_count += 1

    async_to_sync(channel_layer.group_send)(
        conversation_name,
        {
            "type": "notifications_for",
            "conversation": conversation_name,
            "notifications": {
                "unread_notifications": unread_count,
                "notifications": final_notifications,
            }
        },
    )
