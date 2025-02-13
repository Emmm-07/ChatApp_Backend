
from rest_framework import viewsets
from rest_framework.decorators import api_view
from .models import Messages
from .serializers import MessageSerializer,UserSerializer
from django.contrib.auth.models import User

from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view, authentication_classes, permission_classes, action
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q              # for more complex queries

# Create your views here.
class MessageViewset(viewsets.ModelViewSet):
    queryset =  Messages.objects.all().order_by('-timestamp')
    serializer_class = MessageSerializer  
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['GET'], url_path='personal_message')
    def personal_message(self, request):
        sender = request.user
        # recipient = request.data['recipient']
        recipient = request.query_params.get('recipient')
        # take only the messages between  the sender and recipient
        message = Messages.objects.filter(
            (Q(sender=sender)&Q(recipient=recipient)) |  (Q(sender=recipient)&Q(recipient=sender))
        ).order_by('timestamp')
       
        serializer = self.get_serializer(message, many=True)
        serialized_data = serializer.data
        lastMessage = serialized_data[len(serialized_data)-1]['message']
        # print("lastMessage: ",lastMessage)
        return  Response({
            "messages": serialized_data,
            "lastMessage":{ recipient:lastMessage }
        })

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