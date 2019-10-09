from djoser import signals, utils
from djoser.compat import get_user_email
from djoser.views import UserViewSet, TokenCreateView, TokenDestroyView
from djoser.conf import settings as djconf
from rest_framework import status
from rest_framework.response import Response

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


class LoginView(TokenCreateView):

    def _action(self, serializer):
        token = utils.login_user(self.request, serializer.user)
        token_serializer_class = djconf.SERIALIZERS.token
        return Response(
            data=token_serializer_class(token).data, status=status.HTTP_200_OK
        )


class LogoutView(TokenDestroyView):

    def post(self, request):
        utils.logout_user(request)
        return Response(status=status.HTTP_204_NO_CONTENT)
