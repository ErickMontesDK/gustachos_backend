from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from .models import ClientType, Visit, Client
from .serializers import *
from django.db.models import Q
from rest_framework.exceptions import NotFound, ValidationError, MethodNotAllowed, PermissionDenied
from .selectors import get_filtered_visits, get_filtered_clients, get_client_detail
from utils.excel_generator import ExcelGenerator
from datetime import datetime
from rest_framework.decorators import permission_classes
from utils.permissions import IsAdminUser, IsOperatorUser, IsDeliveryUser
from core.models import Business_Config
import pytz

from rest_framework.permissions import IsAuthenticated


class StandardPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        response = super().get_paginated_response(data)
        response.data['total_pages'] = self.page.paginator.num_pages
        response.data['total_count'] = self.page.paginator.count
        response.data['current_page'] = self.page.number
        response.data['page_size'] = self.page.paginator.per_page
        response.data['has_next'] = self.page.has_next()
        response.data['has_previous'] = self.page.has_previous()
        response.data['next'] = self.get_next_link()
        response.data['previous'] = self.get_previous_link()
        return response


# CLIENT TYPES-------------------------------------------------------
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def client_types_list(request):
    if request.method == 'GET':
        client_types = ClientType.objects.all()
        serializer = ClientTypeSerializer(client_types, many=True)
        return Response(serializer.data)
        
    elif request.method == 'POST':
        if not IsAdminUser().has_permission(request, None):
            raise PermissionDenied("You do not have permission to perform this action")
        serializer = ClientTypeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        raise ValidationError(serializer.errors)


@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def client_type_detail(request, pk):

    if not IsAdminUser().has_permission(request, None):
        raise PermissionDenied("You do not have permission to perform this action")

    try:
        client_type = ClientType.objects.get(pk=pk)
    except ClientType.DoesNotExist:
        raise NotFound("Client type not found")
    
    if request.method == 'PATCH':
        serializer = ClientTypeSerializer(client_type, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        raise ValidationError(serializer.errors)
    
    elif request.method == 'DELETE':
        client_type.delete()
        return Response({'message': 'Client type deleted successfully'}, status=status.HTTP_200_OK)
    
    raise MethodNotAllowed(request.method)


# VISITS------------------------------------------------------
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def visit_list(request):

    if request.method == 'GET':
        if not IsAdminUser().has_permission(request, None) and not IsOperatorUser().has_permission(request, None):
            raise PermissionDenied("You do not have permission to perform this action")
        
        visits = get_filtered_visits(request)

        paginator = StandardPagination()
        result_page = paginator.paginate_queryset(visits, request)
        serializer = VisitSerializer(result_page, many=True)

        return paginator.get_paginated_response(serializer.data)
    
    elif request.method == 'POST':
        if not IsDeliveryUser().has_permission(request, None):
            raise PermissionDenied("You do not have permission to perform this action")
        
        request.data['deliverer'] = request.user.id
        serializer = VisitSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        raise ValidationError(serializer.errors)

    raise MethodNotAllowed(request.method)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def visit_list_export(request):
    if request.method != 'GET':
        raise MethodNotAllowed(request.method)
    
    if not IsAdminUser().has_permission(request, None) and not IsOperatorUser().has_permission(request, None):
        raise PermissionDenied("You do not have permission to perform this action")
    
    business_config = Business_Config.objects.first()
    if not business_config or not business_config.time_zone:
        raise ValidationError("Business configuration is incomplete (missing timezone).")
    
    tz = pytz.timezone(business_config.time_zone)
    date = datetime.now(tz).strftime("%Y-%m-%d")
    visits = get_filtered_visits(request)

    
    columns = [
        ("ID", "id"),
        ("Client", "client__name"),
        ("Client Code", "client__code"),
        ("Client Type", "client__client_type__name"),
        ("Sector", "client__sector"),
        ("Deliverer", lambda x: f"{x.deliverer.first_name} {x.deliverer.last_name}" if x.deliverer else ""),
        ("Date", lambda x: x.visited_at.astimezone(tz).strftime("%Y-%m-%d") if x.visited_at else ""),
        ("Time", lambda x: x.visited_at.astimezone(tz).strftime("%H:%M") if x.visited_at else ""),
        ("Address", "client__address"),
        ("Municipality", "client__municipality"),
        ("State", "client__state"),
        ("Is productive", "is_productive"),
        ("Is valid", "is_valid"),
        ("Notes", "notes"),
    ]
    
    generator = ExcelGenerator(sheet_name="visits_report")
    return generator.generate_excel(visits, columns, filename=f"visits_report_{date}.xlsx")


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def visit_detail(request, pk):
    if not IsAdminUser().has_permission(request, None) and not IsOperatorUser().has_permission(request, None):
        raise PermissionDenied("You do not have permission to perform this action")
    
    try:
        visit = Visit.objects.get(pk=pk, is_deleted=False)
    except Visit.DoesNotExist:
        raise NotFound("Visit not found")
    
    if request.method == 'GET':
        serializer = VisitSerializer(visit)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    elif request.method == 'PATCH':
        serializer = VisitSerializer(visit, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        raise ValidationError(serializer.errors)
    
    elif request.method == 'DELETE':
        visit.is_deleted = True
        visit.save()
        return Response({'message': 'Visit marked as deleted'}, status=status.HTTP_200_OK)
    
    raise MethodNotAllowed(request.method)

@api_view(['PATCH'])
def visits_restore(request, pk):
    user = request.user
    if user.role != 'ADMIN':
        raise PermissionDenied("You do not have permission to perform this action")

    if request.method == 'PATCH':
        try:
            visit = Visit.objects.get(pk=pk, is_deleted=True)
            visit.is_deleted = False
            visit.save()
            return Response({'message': 'Visit restored successfully'}, status=status.HTTP_200_OK)
        except Visit.DoesNotExist:
            raise NotFound("Visit not found")
    
    raise MethodNotAllowed(request.method)


# CLIENTS------------------------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def client_code_available(request):
    if request.method == 'GET':
        code = request.query_params.get('code', None)
        if code == "" or code is None:
            raise ValidationError("Code is required")

        if Client.objects.filter(code=code).exists():
            return Response({'message': 'Client code already exists', 'available': False}, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'Client code is available', 'available': True}, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def client_list(request):
    
    
    if request.method == 'GET':
        if not IsAdminUser().has_permission(request, None) and not IsOperatorUser().has_permission(request, None):
            raise PermissionDenied("You do not have permission to perform this action")
        
        clients = get_filtered_clients(request)
        
        paginator = StandardPagination()
        result_page = paginator.paginate_queryset(clients, request)
        serializer = ClientSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    elif request.method == 'POST':
        if not IsDeliveryUser().has_permission(request, None):
            raise PermissionDenied("You do not have permission to perform this action")
        
        serializer = ClientSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        raise ValidationError(serializer.errors)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def client_list_for_map(request):
    if not IsAdminUser().has_permission(request, None) and not IsOperatorUser().has_permission(request, None):
        raise PermissionDenied("You do not have permission to perform this action")

    if request.method == 'GET':
        clients = get_filtered_clients(request)
        serializer = ClientForMapSerializer(clients, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    raise MethodNotAllowed(request.method)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def client_by_code(request, code):
    try:
        client = Client.objects.get(code=code, is_deleted=False)
    except Client.DoesNotExist:
        raise NotFound("Client not found")
    
    if request.method == 'GET':
        serializer = ClientSerializer(client)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def client_detail(request, id):
    client = get_client_detail(id)
    if not client:
        raise NotFound("Client not found")
    
    if request.method == 'GET':
        serializer = ClientSerializer(client)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    elif request.method == 'PATCH':
        if not IsAdminUser().has_permission(request, None) and not IsOperatorUser().has_permission(request, None):
            raise PermissionDenied("You do not have permission to perform this action")
        
        serializer = ClientSerializer(client, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
       
        raise ValidationError(serializer.errors)
    
    elif request.method == 'DELETE':
        if not IsAdminUser().has_permission(request, None) and not IsOperatorUser().has_permission(request, None):
            raise PermissionDenied("You do not have permission to perform this action")
        
        client.is_deleted = True
        client.save()
        return Response({'message': 'Client marked as deleted'}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def client_list_export(request):
    if request.method != 'GET':
        raise MethodNotAllowed(request.method)
    
    if not IsAdminUser().has_permission(request, None) and not IsOperatorUser().has_permission(request, None):
        raise PermissionDenied("You do not have permission to perform this action")

    business_config = Business_Config.objects.first()
    if not business_config or not business_config.time_zone:
        raise ValidationError("Business configuration is incomplete (missing timezone).")
    
    tz = pytz.timezone(business_config.time_zone)
    date = datetime.now(tz).strftime("%Y-%m-%d")
    clients = get_filtered_clients(request)

    columns = [
        ("ID", "id"),
        ("Client", "name"),
        ("Client code", "code"),
        ("Client type", "client_type__name"),
        ("Sector", "sector"),
        ("Market", "market"),
        ("Address", "address"),
        ("Municipality", "municipality"),
        ("State", "state"),
        ("Active", "is_active"),
    ]
    
    generator = ExcelGenerator(sheet_name="Clientes")
    return generator.generate_excel(clients, columns, filename=f"clients_report_{date}.xlsx")
    

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def client_restore(request, pk):
    if not IsAdminUser().has_permission(request, None):
        raise PermissionDenied("You do not have permission to perform this action")

    if request.method == 'PATCH':
        try:
            client = Client.objects.get(pk=pk, is_deleted=True)
            client.is_deleted = False
            client.save()
            return Response({'message': 'Client restored successfully'}, status=status.HTTP_200_OK)

        except Client.DoesNotExist:
            raise NotFound("Client not found")
    
    raise MethodNotAllowed(request.method)
