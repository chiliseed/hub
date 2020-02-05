from rest_framework import status
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from aws_environments.serializers import CreateEnvironmentSerializer, EnvironmentSerializer


class EnvironmentCreate(CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CreateEnvironmentSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['user'] = self.request.user
        return ctx

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        env = serializer.save()
        return Response(EnvironmentSerializer(env).data, status=status.HTTP_201_CREATED)


class EnvironmentList(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = EnvironmentSerializer
