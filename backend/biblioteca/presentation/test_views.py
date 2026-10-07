from rest_framework.views import APIView
from rest_framework.response import Response
from biblioteca.services.test_service import TestService

class TestStatusView(APIView):
    def get(self, request):
        # Solo recibe la petición y delega todo al servicio
        status_message = TestService.get_system_status()
        
        return Response({
            "status": "success",
            "message": status_message
        })