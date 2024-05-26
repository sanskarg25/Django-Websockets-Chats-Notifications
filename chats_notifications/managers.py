from django.contrib.auth.models import (
    BaseUserManager,
)


class CustomUserManager(BaseUserManager):
    def create_superuser(self, email, password):
        if email == None:
            raise ValueError("email")

        user = self.model(email=email)
        user.full_name = "Admin User"
        user.status = "Online"
        user.set_password(password)
        user.save(using=self._db)
        return user
