from django.shortcuts import render
from django.utils import timezone
from visits.models import Visit, Client
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
from django.conf import settings
from core.models import Business_Config
import pytz

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        access = response.data["access"]
        refresh = response.data["refresh"]

        response.set_cookie(
            key=settings.SIMPLE_JWT["AUTH_COOKIE"],
            value=access,
            max_age=settings.SIMPLE_JWT["AUTH_COOKIE_MAX_AGE"],
            httponly=settings.SIMPLE_JWT["AUTH_COOKIE_HTTP_ONLY"],
            secure=settings.SIMPLE_JWT["AUTH_COOKIE_SECURE"],
            samesite=settings.SIMPLE_JWT["AUTH_COOKIE_SAMESITE"],
        )

        response.set_cookie(
            key=settings.SIMPLE_JWT["REFRESH_COOKIE"],
            value=refresh,
            max_age=settings.SIMPLE_JWT["REFRESH_COOKIE_MAX_AGE"],
            httponly=settings.SIMPLE_JWT["REFRESH_COOKIE_HTTP_ONLY"],
            secure=settings.SIMPLE_JWT["REFRESH_COOKIE_SECURE"],
            samesite=settings.SIMPLE_JWT["REFRESH_COOKIE_SAMESITE"],
        )

        response.data = {"message": "login ok"}

        return response

class CustomTokenRefreshView(TokenRefreshView):
    serializer_class = CustomTokenRefreshSerializer

    def post(self, request, *args, **kwargs):

        refresh = request.COOKIES.get("refresh")

        serializer = self.get_serializer(data={"refresh": refresh})
        serializer.is_valid(raise_exception=True)

        access = serializer.validated_data["access"]
        refresh = serializer.validated_data["refresh"]

        response = Response({"message": "token refreshed"})

        response.set_cookie(
            key=settings.SIMPLE_JWT["AUTH_COOKIE"],
            value=access,
            max_age=settings.SIMPLE_JWT["AUTH_COOKIE_MAX_AGE"],
            httponly=settings.SIMPLE_JWT["AUTH_COOKIE_HTTP_ONLY"],
            secure=settings.SIMPLE_JWT["AUTH_COOKIE_SECURE"],
            samesite=settings.SIMPLE_JWT["AUTH_COOKIE_SAMESITE"],
        )

        response.set_cookie(
            key=settings.SIMPLE_JWT["REFRESH_COOKIE"],
            value=refresh,
            max_age=settings.SIMPLE_JWT["REFRESH_COOKIE_MAX_AGE"],
            httponly=settings.SIMPLE_JWT["REFRESH_COOKIE_HTTP_ONLY"],
            secure=settings.SIMPLE_JWT["REFRESH_COOKIE_SECURE"],
            samesite=settings.SIMPLE_JWT["REFRESH_COOKIE_SAMESITE"],
        )

        return response

    

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
            Q(email__icontains=search_term) | 
            Q(username__icontains=search_term)
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
        return Response({'message': 'User marked as deleted'}, status=status.HTTP_200_OK)
    
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_dashboard(request):
    try:
        user = request.user
        business_config = Business_Config.objects.first()
        
        if not business_config or not business_config.time_zone:
            raise ValidationError("Business configuration is incomplete (missing timezone).")

        time_zone = business_config.time_zone
        timezone.activate(pytz.timezone(time_zone))
        LIST_SIZE = 5

        today = timezone.localtime(timezone.now()).date()
        
        visited_clients_today = Visit.objects.filter(
            deliverer=user,
            visited_at__date=today,
            is_deleted=False
        ).values('client').count()
        print("visited_clients_today:",visited_clients_today)

        productive_visits_today = Visit.objects.filter(
            deliverer=user,
            visited_at__date=today,
            is_deleted=False,
            is_productive=True
        ).count()
        
        registered_clients_today = Client.objects.filter(
            created_by=user,
            created_at__date=today,
            is_deleted=False
        ).count()
        
        recent_visits = Visit.objects.filter(
            deliverer=user,
            is_deleted=False
        ).select_related('client', 'deliverer').order_by('-visited_at')[:LIST_SIZE]
        
        recent_clients = Client.objects.filter(
            created_by=user,
            is_deleted=False
        ).select_related('created_by').order_by('-created_at')[:LIST_SIZE]
        
        activity = []

        for v in recent_visits:
            deliverer_name = f"{v.deliverer.first_name} {v.deliverer.last_name}" if v.deliverer else "Unknown"
            activity.append({
                "id": v.id,
                "type": "visit",
                "title": v.client.name if v.client else "Unknown",
                "timestamp": v.visited_at,
                "description": f"Visit registered.",
                "metadata": {
                    "is_productive": v.is_productive,
                    "user_name": deliverer_name
                }
            })
            
        for c in recent_clients:
            if c.created_at:
                creator_name = f"{c.created_by.first_name} {c.created_by.last_name}" if c.created_by else "Unknown"
                activity.append({
                    "id": c.id,
                    "type": "client",
                    "title": c.name,
                    "timestamp": c.created_at,
                    "description": f"New client registered.",
                    "metadata": {
                        "client_code": c.code,
                        "user_name": creator_name
                    }
                })
                
        activity.sort(key=lambda x: x["timestamp"], reverse=True)
        recent_activity = activity[:LIST_SIZE]
        
        return Response({
            "recent_activity": recent_activity,
            "visited_clients_today": visited_clients_today,
            "productive_visits_today": productive_visits_today,
            "registered_clients_today": registered_clients_today,
        }, status=status.HTTP_200_OK)

    except ValidationError as e:
        raise e
    except Exception as e:
        return Response({
            "error": "Dashboard Error",
            "message": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    if not IsAdminUser().has_permission(request, None) and not IsOperatorUser().has_permission(request, None):
        raise PermissionDenied("You do not have permission to perform this action")

    try:
        user = request.user
        business_config = Business_Config.objects.first()
        
        if not business_config or not business_config.time_zone:
            raise ValidationError("Business configuration is incomplete (missing timezone).")

        time_zone = business_config.time_zone
        timezone.activate(pytz.timezone(time_zone))
        LIST_SIZE = 5

        today = timezone.localtime(timezone.now()).date()
        
        visited_clients_today = Visit.objects.filter(
            visited_at__date=today,
            is_deleted=False
        ).values('client').distinct().count()

        productive_visits_today = Visit.objects.filter(
            visited_at__date=today,
            is_deleted=False,
            is_productive=True
        ).count()

        validated_visits_today = Visit.objects.filter(
            visited_at__date=today,
            is_deleted=False,
            is_valid=True
        ).count()

        active_deliverers = Visit.objects.filter(
            visited_at__date=today,
            is_deleted=False
        ).values('deliverer').distinct().count()
        
        registered_clients_today = Client.objects.filter(
            created_at__date=today,
            is_deleted=False
        ).count()

        unvalidated_visits_today = visited_clients_today - validated_visits_today
        productive_percentage = (productive_visits_today / visited_clients_today) * 100 if visited_clients_today > 0 else 0
        valid_visits_percentage = (validated_visits_today / visited_clients_today) * 100 if visited_clients_today > 0 else 0
        
        recent_visits = Visit.objects.filter(
            is_deleted=False
        ).select_related('client', 'deliverer').order_by('-visited_at')[:LIST_SIZE]
        
        recent_clients = Client.objects.filter(
            is_deleted=False
        ).select_related('created_by').order_by('-created_at')[:LIST_SIZE]
        
        activity = []

        for v in recent_visits:
            deliverer_name = f"{v.deliverer.first_name} {v.deliverer.last_name}" if v.deliverer else "Unknown"
            data = {
                "id": v.id,
                "type": "visit",
                "title": v.client.name if v.client else "Unknown",
                "timestamp": v.visited_at,
                "metadata": {
                    "is_productive": v.is_productive,
                    "is_valid": v.is_valid,
                    "user_name": deliverer_name
                }
            }
            description = v.notes if v.notes else None
            if description and description.strip():
                data["description"] = description
            activity.append(data)
            
        for c in recent_clients:

            if c.created_at:
                creator_name = f"{c.created_by.first_name} {c.created_by.last_name}" if c.created_by else "Unknown"
                activity.append({
                    "id": c.id,
                    "type": "client",
                    "title": c.name,
                    "timestamp": c.created_at,
                    "metadata": {
                        "client_code": c.code,
                        "user_name": creator_name
                    }
                })
                
        activity.sort(key=lambda x: x["timestamp"], reverse=True)
        recent_activity = activity[:LIST_SIZE]
        
        return Response({
            "recent_activity": recent_activity,
            "visits_today": visited_clients_today,
            "productive_percentage": productive_percentage,
            "valid_visits_percentage": valid_visits_percentage,
            "active_deliverers": active_deliverers,
            "registered_clients_today": registered_clients_today,
            "unvalidated_visits_today": unvalidated_visits_today
        }, status=status.HTTP_200_OK)

    except ValidationError as e:
        raise e
    except Exception as e:
        return Response({
            "error": "Dashboard Error",
            "message": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    