from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from oauthlib.common import generate_token
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework import status
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model

from user.models import PasswordResetToken
from user.serializers import UserLoginSerializer, ChangePasswordSerializer, ForgotPasswordSerializer

User = get_user_model()


# class SignUpView(APIView):
#     def post(self, request, format=None):
#         serializer = UserSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response({'message': 'Success', 'data': serializer.data})
#         return Response({'message': 'Fail', 'error': serializer.errors})


class LoginView(APIView):
    # serializer_class = UserLoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)

        if serializer.is_valid():
            user = authenticate(username=request.data.get("username"), password=request.data.get("password"))
            if user:
                token, _ = Token.objects.get_or_create(user=user)
                return Response({'token': token.key}, status=status.HTTP_200_OK)
        return Response({'ERROR': serializer.errors}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        try:
            # Delete the user's token to logout
            request.user.auth_token.delete()
            return Response({'message': 'Successfully logged out.'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'ERROR': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        



class ForgotPasswordView(generics.GenericAPIView):
    serializer_class = ForgotPasswordSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exeption=True)

        email = serializer.validate_data['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'detail': 'User with this email address does not exist.'},
                status=400
            )

        token = generate_token()
        PasswordResetToken.objects.create(user=user, token=token)
        return Response(
            {'detail': 'Password reset email has been sent. '},
            status=200
        )


class ResetPasswordView(generics.GenericAPIView):
    def post(self, request, token):
        password_reset_token = get_object_or_404(PasswordResetToken, token=token)
        user = password_reset_token.user

        new_password = request.data.get('password')
        user.password = make_password(new_password)
        user.save()
        password_reset_token.delete()
        return Response(
            {'detail': 'Password has been reset successfully.'},
            status=200
        )


class ChangePasswordView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            old_password = serializer.validated_data['old_password']
            new_password = serializer.validated_data['new_password']

            if user.check_password(old_password):
                user.set_password(new_password)
                user.save()
                return Response(
                    {'message': 'Password has changed successfully'},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {'error': 'Incorrect old password'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


