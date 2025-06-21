from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

class EmailOrUsernameBackend(ModelBackend):
    """
    Custom authentication backend.

    Allows users to log in using either their username or email address.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        try:
            # Try to fetch the user by email
            user = UserModel.objects.get(email__iexact=username)
            if user.check_password(password):
                return user
        except UserModel.DoesNotExist:
            # If user with that email does not exist,
            # fall back to the default username authentication.
            # This allows admin users (who might not have an email) to log in.
            return super().authenticate(request, username, password, **kwargs)

    def get_user(self, user_id):
        UserModel = get_user_model()
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None 