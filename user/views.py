from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework import status
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from user.models import User
from user.serializers import UserLoginSerializer


# class SignUpView(APIView):
#     def post(self, request, format=None):
#         serializer = UserSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response({'message': 'Success', 'data': serializer.data})
#         return Response({'message': 'Fail', 'error': serializer.errors})


class LoginView(APIView):
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
        