from django.shortcuts import render
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .serializers import CustomTokenObtainPairSerializer, CustomTokenRefreshSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import User
from .serializers import UserSerializer, UserPasswordSerializer
from visits.views import StandardPagination
from django.db.models import Q
from rest_framework.exceptions import NotFound, MethodNotAllowed, ValidationError, PermissionDenied
from utils.permissions import IsAdminUser, IsOperatorUser, IsDeliveryUser

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class CustomTokenRefreshView(TokenRefreshView):
    serializer_class = CustomTokenRefreshSerializer

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def user_list(request):

    if not IsAdminUser().has_permission(request, None) and not IsOperatorUser().has_permission(request, None):
        raise PermissionDenied("You do not have permission to perform this action")

    if request.method == "GET":
        users = User.objects.all()

        if IsAdminUser().has_permission(request, None):
            is_deleted = request.query_params.get('is_deleted', 'False').capitalize()
            users = users.filter(is_deleted=is_deleted)
        else:
            users = users.filter(is_deleted=False)

        sorting = request.query_params.get('sorting')
        role = request.query_params.get('role')

        if sorting:
            users = users.order_by(sorting)
        else:
            users = users.order_by('-id')

        search_term = request.query_params.get('search_term')
        if search_term:
            users = users.filter(
            Q(first_name__icontains=search_term) | 
            Q(last_name__icontains=search_term) | 
            Q(email__icontains=search_term) 
        )

        if role:
            users = users.filter(role=role)

        paginator = StandardPagination()
        result_page = paginator.paginate_queryset(users, request)
        serializer = UserSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)

    if request.method == "POST":
        if not IsAdminUser().has_permission(request, None):
            raise PermissionDenied("You do not have permission to perform this action")
        serializer = UserSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        raise ValidationError(serializer.errors)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def user_detail(request, pk):  
    if not IsAdminUser().has_permission(request, None) and not IsOperatorUser().has_permission(request, None):
        raise PermissionDenied("You do not have permission to perform this action")

    try:
        user = User.objects.get(pk=pk, is_deleted=False)
    except User.DoesNotExist:
        raise NotFound("User not found")
    
    if request.method == 'GET':
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    elif request.method == 'PATCH':
        data = request.data
        if not IsAdminUser().has_permission(request, None):
            raise PermissionDenied("You do not have permission to perform this action")

        requesting_user = request.user
        if requesting_user.id == user.id:
            if 'role' in data:
                del data['role']

        serializer = UserSerializer(user, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        raise ValidationError(serializer.errors)
    
    elif request.method == 'DELETE':
        if not IsAdminUser().has_permission(request, None):
            raise PermissionDenied("You do not have permission to perform this action")

        requesting_user = request.user
        if requesting_user.id == user.id:
            raise PermissionDenied("You cannot delete yourself")

        user.is_deleted = True
        user.save()
        return Response({'message': 'User marked as deleted'}, status=status.HTTP_204_NO_CONTENT)
    
    raise MethodNotAllowed(request.method)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_me(request):
    try:
        user = User.objects.get(pk=request.user.id, is_deleted=False)
    except User.DoesNotExist:
        raise NotFound("User not found")
    
    if request.method == 'GET':
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    raise MethodNotAllowed(request.method)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_user_password(request, pk=None):
    is_me_endpoint = (pk is None or pk == 'me')
    target_user_id = request.user.id if is_me_endpoint else pk
    
    if not is_me_endpoint and int(target_user_id) == request.user.id:
        raise ValidationError("You cannot change your own password using this action")

    if target_user_id != request.user.id and not IsAdminUser().has_permission(request, None):
        raise PermissionDenied("You do not have permission to perform this action")

    try:
        user = User.objects.get(pk=target_user_id, is_deleted=False)
    except User.DoesNotExist:
        raise NotFound("User not found")
    
    serializer = UserPasswordSerializer(user, data=request.data, context={'request': request})
    
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Password updated successfully"}, status=status.HTTP_200_OK)

    raise ValidationError(serializer.errors)
    
    raise MethodNotAllowed(request.method)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def user_restore(request, pk):
    if not IsAdminUser().has_permission(request, None):
        raise PermissionDenied("You do not have permission to perform this action")

    if request.method == 'PATCH':
        try:
            usersData = User.objects.get(pk=pk)
            if usersData.is_deleted == False:
                raise ValidationError("User is already active")
            usersData.is_deleted = False
            usersData.save()
            return Response({'message': 'User restored successfully'}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            raise NotFound("User not found")
    
    raise MethodNotAllowed(request.method)