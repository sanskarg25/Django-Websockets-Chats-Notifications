import json, uuid, datetime
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from urllib.parse import parse_qs
from chats_notifications.models import (
    ConversationModel,
    ChatModel,
    NotificationsModel,
)
from chats_notifications.utils import (
    direct_chat,
    notifications,
)

socket_disconnected = "websocket is disconnected"
MESSAGE_TYPE = {
    "TYPING": 'typing',
    "TEXT_MESSAGE": 'text_message',
    "MESSAGE_READ": 'message_read',
    "FILE_UPLOAD": 'file_upload',
    "EDITED": 'edited',
    "PINNED": 'pinned',
    "DELETED": 'deleted',
    "NEXT_MESSAGES" : 'next_messages',
    "REPLY_MESSAGE" : 'reply_message',
    "USER_TYPE": 'user_type',
    "read" : 'read',
    "delete" : 'delete'
}


class DirectChatConsumer(WebsocketConsumer):
    """
    Direct Chat Application
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.conversation_name = None
        self.recevier_conversation_name = None
        self.user = None
        self.receiver = None
        self.conversation_id = None
        self.next_conversation = None
        self.files = None
        self.token = None
        self.connected_users = []
        self.user_detail = {}

    def connect(self):
        try:
            print("Web Sockets for Chat connected")
            self.accept()

            query_string_bytes = self.scope.get("query_string", b"")
            query_string = parse_qs(query_string_bytes.decode("utf-8"))
            sender = query_string["sender"][0]
            user = query_string["receiver"][0]

            self.user = sender
            self.receiver = user

            receiver_id = user
            print("here")
            self.conversation_id = self.get_or_create_conversation_id(sender,receiver_id)

            self.conversation_name = f'message_list_{self.conversation_id}__{self.user}'
            self.recevier_conversation_name = f'message_list_{self.conversation_id}__{receiver_id}'

            self.next_conversation = f'next_messages_{self.conversation_id}__{self.user}'
            async_to_sync(self.channel_layer.group_add)(
            self.next_conversation, self.channel_name
            )

            async_to_sync(self.channel_layer.group_add)(
                self.conversation_name, self.channel_name
            )
            direct_chat(self.user,self.conversation_id)

            self.connected_users.append(str(self.user))
        except Exception as e:
            self.disconnect(f"Chat socket was disconnected due to {str(e)}")

    """ receive the data from web socket """
    def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data)
            message = data.get("message","")
            files = data.get("files", [])
            message_type = data.get("type")
            user = self.receiver

            if message_type == MESSAGE_TYPE["TEXT_MESSAGE"]:

                async_to_sync(self.channel_layer.group_send)(
                    self.conversation_name,
                    {
                        "type": "text_message",
                        "message": message,
                        "user": user,
                    }
                )
                current_user_id = self.save_text_message(message,user)
                async_to_sync(self.channel_layer.group_send)(
                    f"new_message_for_{current_user_id}",
                    {
                        'type': 'new_message',
                        'user_id' : str(user),
                        'current_user_id' : str(current_user_id),
                        'conversation_id' : self.conversation_id,
                        'message' : message
                    }
                )
                # sender
                direct_chat(self.user,self.conversation_id)
                # receiver
                direct_chat(self.receiver,self.conversation_id)
                # conversation_list(self.receiver)

                if self.receiver_is_not_connected() == False:
                    NotificationsModel.objects.create(
                        notification_user_id=self.user,
                        receiver_user_id=self.receiver,
                        message=message,
                        conversation_id=str(self.conversation_id)
                    )
                    notifications(self.receiver)

            if message_type == MESSAGE_TYPE["FILE_UPLOAD"]:
                async_to_sync(self.channel_layer.group_send)(
                    self.conversation_name,
                    {
                        "type": "file_upload",
                        "message": message,
                        "files": files,
                        "user": user
                    }
                )

                current_user_id = self.save_file_upload(message,user,files)
                # sender
                direct_chat(self.user,self.conversation_id)
                # receiver
                direct_chat(self.receiver,self.conversation_id)
                # conversation_list(self.receiver)

                if self.receiver_is_not_connected() == False:
                    NotificationsModel.objects.create(
                        notification_user_id=self.user,
                        receiver_user_id=self.receiver,
                        message=f"Sent {len(files)} file",
                        conversation_id=str(self.conversation_id)
                    )
                    notifications(self.receiver)

            if message_type == MESSAGE_TYPE["MESSAGE_READ"]:

                self.save_message_read()
                # conversation_list(self.user)
                NotificationsModel.objects.filter(receiver_user_id=self.user,conversation_id=str(self.conversation_id)).update(read=True,updated_date=datetime.datetime.now())
                notifications(self.user)

            if message_type == MESSAGE_TYPE["TYPING"]:
                if str(self.user) != str(self.receiver):
                    async_to_sync(self.channel_layer.group_send)(
                        self.recevier_conversation_name,
                        {
                            "type": "typing",
                            "status": data.get("status")
                        }
                    )

                    async_to_sync(self.channel_layer.group_send)(
                        f'conversation_list_{self.receiver}',
                        {
                            "type": "typing",
                            "conversation_id": str(self.conversation_id),
                            "status": data.get("status"),
                            "user_name": None
                        }
                    )

            if message_type == MESSAGE_TYPE["PINNED"]:
                self.save_pinned_message(data.get("message_id"),data.get("status"))
                async_to_sync(self.channel_layer.group_send)(
                    self.conversation_name,
                    {
                        "type": "pinned",
                        "message_id": data.get("message_id"),
                        "status": data.get("status")
                    }
                )
                """ receiver """
                async_to_sync(self.channel_layer.group_send)(
                    self.recevier_conversation_name,
                    {
                        "type": "pinned",
                        "message_id": data.get("message_id"),
                        "status": data.get("status")
                    }
                )

            if message_type == MESSAGE_TYPE["EDITED"]:
                msg_id = data.get("message_id")
                if data.get("message"):
                    message = data.get("message")
                else:
                    message = ChatModel.objects.get(id=int(msg_id)).message

                if data.get("files"):
                    files = data.get("files")
                else:
                    files = ChatModel.objects.get(id=int(msg_id)).files

                async_to_sync(self.channel_layer.group_send)(
                    self.conversation_name,
                    {
                        "type": "edited",
                        "message_id": data.get("message_id"),
                        "message": message,
                        "files" : files
                    }
                )
                self.save_edited_message(msg_id,message,files)
                # conversation_list(self.user)
                """ receiver """
                async_to_sync(self.channel_layer.group_send)(
                    self.recevier_conversation_name,
                    {
                        "type": "edited",
                        "message_id": data.get("message_id"),
                        "message": message,
                        "files" : files
                    }
                )
                # conversation_list(self.receiver)

            if message_type == MESSAGE_TYPE["DELETED"]:
                msg_id = data.get("message_id")
                status = data.get("status")
                async_to_sync(self.channel_layer.group_send)(
                    self.conversation_name,
                    {
                        "type": "deleted",
                        "message_id": data.get("message_id"),
                        "status": data.get("status"),
                        "is_sender": True
                    }
                )
                self.save_deleted_message(msg_id,status)
                # conversation_list(self.user)
                """ receiver """
                async_to_sync(self.channel_layer.group_send)(
                    self.recevier_conversation_name,
                    {
                        "type": "deleted",
                        "message_id": data.get("message_id"),
                        "status": data.get("status"),
                        "is_sender": False
                    }
                )
                # conversation_list(self.receiver)

            if message_type == MESSAGE_TYPE["NEXT_MESSAGES"]:
                direct_chat(self.user,self.conversation_id,next=True,l_id=data.get("id"))

            if message_type == MESSAGE_TYPE["REPLY_MESSAGE"]:
                reply_id = data.get("reply_id")
                message = data.get("message","")
                files = data.get("files",[])
                async_to_sync(self.channel_layer.group_send)(
                    self.conversation_name,
                    {
                        "type" : "reply_message",
                        "reply_id" : reply_id,
                        "message" : message,
                        "files" : files
                    }
                )
                self.save_reply_message(reply_id,message,files)
                #sender
                direct_chat(self.user,self.conversation_id)
                #receiver
                direct_chat(self.receiver,self.conversation_id)
                # conversation_list(self.receiver)

        except Exception as e:
            self.disconnect(f"Chat socket was disconnected due to {str(e)}")

    def disconnect(self, code):
        print(f"disconnected: {code}")
        self.connected_users.remove(str(self.user))
        async_to_sync(self.channel_layer.group_discard)(
            self.conversation_name, self.channel_name
        )

    def message_list(self, event):
        self.send(text_data=json.dumps(event))

    def new_message_for(self, event):
        self.send(text_data=json.dumps(event))

    def get_or_create_conversation_id(self, sender_id, receiver_id):
        """Check if a conversation exists between sender and receiver """
        if receiver_id != "undefined":
            conversation_obj = ConversationModel.objects.filter(
                conversation_users=sorted([sender_id,receiver_id]),
                direct_chat=True
            ).first()

            if not conversation_obj:
                """Create a new conversation """
                self_chat = False
                if sender_id == receiver_id:
                    self_chat = True
                conversation_id = uuid.uuid4()
                conversation_obj = ConversationModel.objects.create(
                    id=conversation_id,
                    name = f"message_list_{sender_id}__{receiver_id}",
                    conversation_users = sorted([sender_id,receiver_id]),
                    direct_chat = True,
                    self_chat=self_chat,
                    created_date=datetime.datetime.now(),
                    updated_date=datetime.datetime.now()
                )
                # conversation_list(self.user)

            return conversation_obj.id
        return None

    def text_message(self, event):
        self.send(text_data=json.dumps({
            "type" : event["type"],
            "message" : event["message"]
        }))

    def file_upload(self,event):
        self.send(text_data=json.dumps({
            "type" : event["type"],
            "message" : event.get("message",""),
            "files" : event["files"]
        }))

    def message_read(self,event):
        self.send(text_data=json.dumps({
            "type" : event["type"]
        }))

    def typing(self,event):
        self.send(text_data=json.dumps({
            "type" : event["type"],
            "status": event["status"]
        }))

    def pinned(self,event):
        self.send(text_data=json.dumps({
            "type" : event["type"],
            "status": event["status"],
            "message_id": event["message_id"]
        }))

    def edited(self,event):
        self.send(text_data=json.dumps({
            "type" : event["type"],
            "message_id": event["message_id"],
            "message": event.get("message",""),
            "files": event.get("files",[])
        }))

    def deleted(self,event):
        self.send(text_data=json.dumps({
            "type" : event["type"],
            "message_id": event["message_id"],
            "status":  event["status"],
            "is_sender": event["is_sender"]
        }))

    def next_messages(self,event):
        self.send(text_data=json.dumps(event))

    def reply_message(self,event):
        self.send(text_data=json.dumps({
            "type" : event["type"],
            "reply_id" : event["reply_id"],
            "message" : event["message"],
            "files" : event["files"]
        }))

    def receiver_is_not_connected(self):
        if str(self.receiver) in self.connected_users:
            return True
        else:
            return False

    """ saving to database """
    def save_text_message(self,message,user):
        current_user = self.user
        convo_obj = ConversationModel.objects.get(id=self.conversation_id)
        chat_obj = ChatModel.objects.create(
            sender_id=current_user,
            receiver_id=user,
            conversation=convo_obj,
            message=message,
            created_date=datetime.datetime.now(),
            updated_date=datetime.datetime.now()
        )
        convo_obj.updated_date = datetime.datetime.now()
        convo_obj.save()
        return chat_obj.receiver.id if self.user == chat_obj.sender else chat_obj.sender.id

    def save_file_upload(self,message,user,files):
        current_user = self.user
        convo_obj = ConversationModel.objects.get(id=self.conversation_id)

        chat_obj = ChatModel.objects.create(
            sender_id=current_user,
            receiver_id=user,
            conversation=convo_obj,
            message=message,
            files=files,
            created_date=datetime.datetime.now(),
            updated_date=datetime.datetime.now()
        )
        convo_obj.updated_date = datetime.datetime.now()
        convo_obj.save()
        return chat_obj.receiver.id if self.user == chat_obj.sender else chat_obj.sender.id

    def save_message_read(self):
        current_user = self.user
        convo_obj = ConversationModel.objects.get(id=self.conversation_id)

        chat_data = ChatModel.objects.filter(
            conversation_id=convo_obj.id,
            receiver_id=current_user
        ).update(read=True,updated_date=datetime.datetime.now())
        if chat_data:
            return True
        else:
            return False

    def save_pinned_message(self,message_id,status):
        msg_obj = ChatModel.objects.get(id=message_id)
        if msg_obj:
            msg_obj.is_pinned = status
            msg_obj.updated_date = datetime.datetime.now()
            msg_obj.save()
            return True
        else:
            return False

    def save_edited_message(self,message_id,message,files):
        msg_obj = ChatModel.objects.get(id=message_id)
        if msg_obj:
            if message != msg_obj.message and message is not None:
                msg_obj.message = message

            if files is not None and len(files) > 0:
                msg_obj.files = files

            msg_obj.is_edited = True
            msg_obj.updated_date = datetime.datetime.now()
            msg_obj.save()
            return True
        else:
            return False

    def save_deleted_message(self,message_id,status):
        msg_obj = ChatModel.objects.get(id=message_id)
        if msg_obj:
            msg_obj.is_deleted = status
            msg_obj.updated_date = datetime.datetime.now()
            msg_obj.save()
            return True
        else:
            return False

    def save_reply_message(self,reply_id,message,files):
        reply_obj = ChatModel.objects.get(id=reply_id)

        ChatModel.objects.create(
            sender_id=self.user,
            receiver_id=self.receiver,
            conversation_id=self.conversation_id,
            message=message,
            files=files,
            reply_id=reply_obj.id,
            is_reply=True,
            reply_message=reply_obj.message,
            reply_files=reply_obj.files,
            created_date=datetime.datetime.now(),
            updated_date=datetime.datetime.now()
        )
        ConversationModel.objects.filter(id=self.conversation_id).update(
            updated_date=datetime.datetime.now()
        )


class NotificationsConsumer(WebsocketConsumer):
    """
    Chat Notifications consumers
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.conversation_name = None
        self.user = None

    def connect(self):
        try:
            print("Web Sockets for chat notifications connected")
            self.accept()

            query_string_bytes = self.scope.get("query_string", b"")
            query_string = parse_qs(query_string_bytes.decode("utf-8"))
            self.user = query_string["user"][0]

            self.conversation_name = f'notifications_for_{self.user}'

            async_to_sync(self.channel_layer.group_add)(
                self.conversation_name, self.channel_name
            )
            notifications(self.user)

        except Exception as e:
            self.disconnect(f"Chat Notifications socket was disconnected due to {str(e)}")

    def notifications_for(self,event):
        self.send(text_data=json.dumps(event))

    def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data)
            message_type = data.get("type")

            if message_type == MESSAGE_TYPE[f"{message_type}"]:
                ids = ids = data.get("ids",[])
                read = data.get("read",None)
                self.save_changed_status(status=message_type,read=read,ids=ids)
                notifications(self.user)

        except Exception as e:
            self.disconnect(f"Chat Notifications socket was disconnected due to {str(e)}")

    def disconnect(self, code):
        print(f"disconnected: {code}")
        async_to_sync(self.channel_layer.group_discard)(
            self.conversation_name, self.channel_name
        )

    def read(self,event):
        self.send(text_data=json.dumps({
            "type" : event["type"]
        }))

    def delete(self,event):
        self.send(text_data=json.dumps({
            "type" : event["type"]
        }))

    """ saving to database """
    def save_changed_status(self,status,read,ids):
        if status == "read":
            try:
                for each in ids:
                    notification_obj = NotificationsModel.objects.get(id=int(each))
                    if notification_obj:
                        notification_obj.read = read
                        notification_obj.updated_date = datetime.datetime.now()
                        notification_obj.save()
                return True
            except:
                return False

        if status == "delete":
            try:
                for each in ids:
                    NotificationsModel.objects.filter(id=int(each)).delete()
                return True
            except:
                return False
