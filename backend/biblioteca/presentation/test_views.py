from rest_framework.permissions import (
    AllowAny,
)
from rest_framework.response import Response
from rest_framework.views import APIView

from biblioteca.services.test_service import (
    TestService,
)


class TestStatusView(APIView):

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        status_message = (
            TestService.get_system_status()
        )

        return Response(
            {
                'status': 'success',
                'message': status_message,
            }
        )