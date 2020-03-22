from rest_framework.generics import RetrieveAPIView

from aws_environments.models import ExecutionLog
from aws_environments.serializers import ExecutionLogSerializer


class ExecutionLogDetailsView(RetrieveAPIView):
    serializer_class = ExecutionLogSerializer
    lookup_url_kwarg = "slug"
    lookup_field = "slug"

    def get_queryset(self):
        return ExecutionLog.objects.filter(organization=self.request.user.organization)
