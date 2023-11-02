from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from django.contrib.auth import get_user_model


User = get_user_model()


# class UserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ('username', 'password')
#         extra_kwargs = {'password': {'write_only': True, 'trim_whitespace': False}}

#     def create(self, validated_data):
#         user = User(
#             username=validated_data['username'],
#             email=validated_data['email']
#         )
#         user.set_password(validated_data['password'])
#         user.save()
#         return user


class UserLoginSerializer(serializers.Serializer):
        username = serializers.CharField(max_length=150)
        password = serializers.CharField(max_length=128, write_only=True)
    
        def validate(self, data): 
            username = data.get("username", None)
            password = data.get("password", None)
            if username and password:
                if User.objects.filter(username=username).exists():
                    user = User.objects.get(username=username)
                    if not user.check_password(password):
                        msg = _('Wrong credentials!')
                        raise serializers.ValidationError(msg, code='authorization')
                        # raise serializers.ValidationError()
                    else:
                        return user
                else:
                    msg = _('Unable to log in with provided credentials.')
                    raise serializers.ValidationError(msg, code='authorization')
            else:
                msg = _('Must include "username" and "password".')
                raise serializers.ValidationError(msg, code='authorization')

     
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)


class ResetPasswordEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

