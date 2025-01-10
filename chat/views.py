
from rest_framework import viewsets
from rest_framework.decorators import api_view
from .models import Messages
from .serializers import MessageSerializer,UserSerializer
from django.contrib.auth.models import User

from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status


# Create your views here.
class MessageViewset(viewsets.ModelViewSet):
    queryset =  Messages.objects.all().order_by('-timestamp')
    serializer_class = MessageSerializer  
    permission_classes = [IsAuthenticated]

@api_view(['POST'])
def login(request):
    user = get_object_or_404(User, username=request.data['username'])
    if not user.check_password(request.data['password']):
        return Response({"detail":"Not Found"},status=status.HTTP_404_NOT_FOUND)
    
    refresh = RefreshToken.for_user(user)

 
    friends = User.objects.exclude(id=user.id).exclude(is_superuser=True).values('id','first_name','last_name')

    # serialized_users = UserSerializer(users, many=True).data


    return Response({
        "refresh":str(refresh),
        "access":str(refresh.access_token),
        "firstname":str(user.first_name),  
        "friendList":list(friends)   
  
    })


@api_view(['POST'])
def signup (request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        # user  = User.objects.get(username=request.data['username'])
        user.set_password(request.data['password'])                         #Set a hashed password
        user.save()
        # token = Token.objects.create(user=user)

        refresh = RefreshToken.for_user(user)
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })
    
    return Response({'detail':serializer.errors},status=status.HTTP_400_BAD_REQUEST)


# @api_view(['POST'])
# def friendList(request):