from djoser import signals
from djoser.compat import get_user_email
from djoser.views import UserViewSet
from djoser.conf import settings as djconf

from users.utils.views import get_email_context


class RegisterView(UserViewSet):

    def perform_create(self, serializer):
        user = serializer.save()
        signals.user_registered.send(
            sender=self.__class__, user=user, request=self.request
        )

        context = get_email_context(user)
        to = [get_user_email(user)]
        if djconf.SEND_ACTIVATION_EMAIL:
            djconf.EMAIL.activation(self.request, context).send(to)
        elif djconf.SEND_CONFIRMATION_EMAIL:
            djconf.EMAIL.confirmation(self.request, context).send(to)
