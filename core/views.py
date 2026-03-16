from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Business_Config
from .serializers import Business_ConfigSerializer, PublicBusiness_ConfigSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from utils.permissions import IsAdminUser


@api_view(['GET'])
def PublicBusinessConfigView(request):
    config = Business_Config.objects.first()

    if not config:
        raise NotFound("No configuration found")
    serializer = PublicBusiness_ConfigSerializer(config)
    return Response(serializer.data)

@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def BusinessConfigView(request):

    if request.method == 'GET':
        config = Business_Config.objects.first()

        if not config:
            raise NotFound("No configuration found")
        serializer = Business_ConfigSerializer(config)
        return Response(serializer.data)

    if request.method == 'PATCH':

        if not IsAdminUser().has_permission(request, None):
            raise PermissionDenied("You do not have permission to perform this action")
            
        config = Business_Config.objects.first()

        if not config:
            raise NotFound("No configuration found")

        serializer = Business_ConfigSerializer(config, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        raise ValidationError(f"Invalid data provided: {serializer.errors}")
