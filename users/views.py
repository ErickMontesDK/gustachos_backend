from django.shortcuts import render
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .serializers import CustomTokenObtainPairSerializer, CustomTokenRefreshSerializer
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import User
from .serializers import UserSerializer
from visits.views import StandardPagination
from django.db.models import Q


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class CustomTokenRefreshView(TokenRefreshView):
    serializer_class = CustomTokenRefreshSerializer

@api_view(['GET', 'POST'])
def user_list(request):

 if request.method == "GET":
      users = User.objects.all().filter(is_deleted=False)

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