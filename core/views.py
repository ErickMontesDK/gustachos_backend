from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Business_Config
from .serializers import Business_ConfigSerializer
from rest_framework.decorators import api_view

@api_view(['GET', 'PATCH'])
def BusinessConfigView(request):
    if request.method == 'GET':
        config = Business_Config.objects.first()
        if not config:
            return Response({"detail": "No configuration found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = Business_ConfigSerializer(config)
        return Response(serializer.data)

    if request.method == 'PATCH':
        config = Business_Config.objects.first()
        if not config:
            return Response({"detail": "No configuration found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = Business_ConfigSerializer(config, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
