from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework import serializers
from .models import User

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token['name'] = f"{user.first_name} {user.last_name}"
        token['role'] = user.role
        token['username'] = user.username

        return token

class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        try:
            data = super().validate(attrs)
            return data
        except Exception as e:
            raise e

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 
            'username', 
            'full_name', 
            'first_name', 
            'last_name', 
            'email', 
            'role',
            'password',
            'is_deleted'
        ]
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate(self, attrs):
        email = attrs.get('email')
        is_deleted = attrs.get('is_deleted')
        request = self.context.get('request')
        instance = self.instance

        if email:
            qs = User.objects.filter(email=email)
            if instance:
                qs = qs.exclude(pk=instance.pk)
            if qs.exists():
                raise serializers.ValidationError({"email": "Email already exists"})

        if is_deleted is True and request and instance:
            user = getattr(request, 'user', None)
            if user and user.id == instance.id:
                raise serializers.ValidationError({"is_deleted": "You cannot delete yourself"})

        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance

class UserPasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=False, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        user = self.instance
        request = self.context.get('request')
        
        if request:
            if request.user.id == user.id:
                old_password = attrs.get('old_password')
                if not old_password:
                    raise serializers.ValidationError({"old_password": "Current password is required."})
                if not user.check_password(old_password):
                    raise serializers.ValidationError({"old_password": "Current password is incorrect."})
            
            elif request.user.role != 'ADMIN':
                raise serializers.PermissionDenied("You do not have permission to change other users' passwords.")
        
        return attrs

    def update(self, instance, validated_data):
        instance.set_password(validated_data['new_password'])
        instance.save()
        return instance