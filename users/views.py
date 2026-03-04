from django.shortcuts import render
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .serializers import CustomTokenObtainPairSerializer, CustomTokenRefreshSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import User
from .serializers import UserSerializer
from visits.views import StandardPagination
from django.db.models import Q
from rest_framework.exceptions import NotFound, MethodNotAllowed, ValidationError


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class CustomTokenRefreshView(TokenRefreshView):
    serializer_class = CustomTokenRefreshSerializer

@api_view(['GET', 'POST'])
def user_list(request):

 if request.method == "GET":
      users = User.objects.all()

      if request.user.role == 'ADMIN':
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
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
def user_detail(request, pk):   
    try:
        user = User.objects.get(pk=pk, is_deleted=False)
    except User.DoesNotExist:
        raise NotFound("User not found")
    
    if request.method == 'GET':
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    elif request.method == 'PATCH':
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        raise ValidationError(serializer.errors)
    
    elif request.method == 'DELETE':
        user.is_deleted = True
        user.save()
        return Response({'message': 'User marked as deleted'}, status=status.HTTP_204_NO_CONTENT)
    
    raise MethodNotAllowed(request.method)

@api_view(['GET'])
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
def update_user_password(request):
    try:
        user = User.objects.get(pk=request.user.id, is_deleted=False)
    except User.DoesNotExist:
        raise NotFound("User not found")
    
    if request.method == 'POST':
        serializer = UserSerializer(user, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        raise ValidationError(serializer.errors)
    
    raise MethodNotAllowed(request.method)


@api_view(['PATCH'])
def user_restore(request, pk):
    user = request.user
    if user.role != 'ADMIN':
        raise PermissionDenied("You do not have permission to perform this action")

    if request.method == 'PATCH':
        try:
            usersData = User.objects.get(pk=pk, is_deleted=True)
            usersData.is_deleted = False
            usersData.save()
            return Response({'message': 'User restored successfully'}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            raise NotFound("User not found")
    
    raise MethodNotAllowed(request.method)