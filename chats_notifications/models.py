import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from django.dispatch import receiver
from django.db.models.signals import pre_save
from chats_notifications.managers import CustomUserManager
# Create your models here.


class TimeStampedModel(models.Model):
    created_date = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_date = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        abstract = True

class UserModel(AbstractBaseUser):
    id = models.UUIDField(unique=True, max_length=255, primary_key=True, editable=False)
    user_name = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(blank=True, max_length=255, null=True, unique=True)
    status = models.CharField(max_length=100, null=True, blank=True)
    last_online = models.DateTimeField(null=True, blank=True)

    # Default Permissions
    is_staff = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now_add=True, null=True)
    updated_date = models.DateTimeField(auto_now=True, null=True)

    USERNAME_FIELD = "email"

    objects = CustomUserManager()

    def __str__(self):
        return str(self.email)

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True


@receiver(pre_save, sender=UserModel)
def user_model_pre_save_signal(sender, instance, **kwargs):
    """
    primary key generation
    """
    if not instance.id:
        unique_name = str(instance.email)
        instance.id = str(uuid.uuid5(name=unique_name, namespace=uuid.NAMESPACE_X500))


class ConversationModel(TimeStampedModel):
    id = models.UUIDField(unique=True, max_length=255, primary_key=True, editable=False)
    name = models.CharField(max_length=255, null=True, blank=True)
    conversation_users = models.JSONField(
        null=True,
        blank=True,
    )
    hidden_for = models.ManyToManyField(
        UserModel,
        blank=True,
        related_name="ConversationModel_hidden_for",
    )
    direct_chat = models.BooleanField(default=True)
    is_pinned_for = models.JSONField(null=True, blank=True)
    self_chat = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Conversation Model"
        verbose_name_plural = "Conversation Models"


class ChatModel(TimeStampedModel):
    sender = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="ChatModel_sender"
    )
    receiver = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="ChatModel_receiver"
    )
    conversation = models.ForeignKey(
        ConversationModel,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="ChatModel_conversation"
    )
    message = models.CharField(null=True, blank=True)
    files = models.JSONField(null=True, blank=True)
    read = models.BooleanField(default=False)
    is_edited = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False)
    is_reply = models.BooleanField(default=False)
    reply_id = models.CharField(null=True, blank=True)
    reply_message = models.CharField(null=True, blank=True)
    reply_files = models.JSONField(null=True, blank=True)

    class Meta:
        verbose_name = "Chat Model"
        verbose_name_plural = "Chat Models"


class NotificationsModel(TimeStampedModel):
    receiver_user = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="NotificationsModel_receiver_user",
    )
    notification_user = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="NotificationsModel_notification_user",
    )
    message = models.CharField(null=True, blank=True)
    conversation_id = models.CharField(null=True, blank=True)
    read = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Notifications Model"
        verbose_name_plural = "Notifications Models"
