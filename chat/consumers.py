import json
from channels.generic.websocket import AsyncWebsocketConsumer
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from .models import Messages
from django.contrib.auth.models import User
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from asgiref.sync import sync_to_async
from urllib.parse import parse_qs
class ChatConsumer(AsyncWebsocketConsumer):
   
    async def connect(self):
        self.user = None
        try:
            token = self.scope['query_string'].decode().split('=')[1]
            validated_token = await sync_to_async(JWTAuthentication().get_validated_token)(token)
            self.user = await sync_to_async(JWTAuthentication().get_user)(validated_token)
            print("User: ",self.user.username,"\nID: ",self.user.id)
        except Exception as e:
            print("Error in connecting: ", e)
            self.user = AnonymousUser()
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        self.room_name  = "chat_room"
        self.room_group_name = f"chat_{self.room_name}_{self.user.id}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )
        
        await self.accept()


    async def disconnect(self,close_code):
        if self.user.is_authenticated:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name,
            )

    async def receive(self, text_data):   
        text_data_json = json.loads(text_data)
        type = text_data_json['type']

        if type == "private_chat_message":
            await self.handle_private_chat_message(text_data_json)
        elif type == "active_status_indicator":
            await self.handle_active_status_indicator(text_data_json)
            print("Hello active status")

 #----- Functions ------------------------------------------------------------------------------------------------------       

    async def handle_private_chat_message(self, text_data_json):
        message = text_data_json['message']
        user = text_data_json['user']
        recipientId =  int(text_data_json['recipientId'])

        sender =await sync_to_async(User.objects.get)(id=self.user.id)
        recipient = await sync_to_async(User.objects.get)(id=recipientId)

        print("Recipient ID: ", recipientId)
        print("Usesr ID: ", self.user.id)

        recipients = [
            f"chat_chat_room_{recipientId}",
            f"chat_chat_room_{self.user.id}"            # send also to self, to reflect what u sent
        ]

        #Save message to database
        await sync_to_async(Messages.objects.create)(
            sender=sender,
            recipient=recipient,
            message=message,
        )
        r_id = recipient.id
        s_id = sender.id
        r_name = recipient.first_name
        s_name=f"{sender.first_name} {sender.last_name}"
        print(sender)
        print(recipient)
        print(message)
        print("rec:",r_id)
        # Send message to room group
        try:
            for rec in recipients:
                await self.channel_layer.group_send(
                rec,                                    # Edit Here to specify to what is the recipient's ID 
                # self.room_group_name,
                {
                    'type':'chat_message',              # calls the function chat_message()
                    'message':message,
                    'user':user,
                    'sender_fname':s_name,
                    'recipient':r_id,
                    'sender':s_id
                }
            )
            print("MESSAGE RECEIVED")
        except Exception as e:
            print("Error:",e)
        
    async def chat_message(self,event):
        print("MESSAGE SENT")
        #Send message to Websocket
        await self.send(text_data=json.dumps(event))


    async def handle_active_status_indicator(self, text_data_json):
        users = await self.handle_active_status_sync(text_data_json)
        await self.send_active_status(users['all_users'], users['active_users'])

    @sync_to_async
    def handle_active_status_sync(self, text_data_json):
        try:
            # Update is_active field in db when logging out, "online" is already handled in login
            user = User.objects.get(id=text_data_json['user_id'])
            print("is_active before update: ", user.is_active)
            if text_data_json['status'] == "offline":
                user.is_active = (False)
                user.save()
            print("is_active after update: ", user.is_active)
            all_users = User.objects.exclude(is_superuser=True)\
                    .values('id', 'first_name', 'last_name', 'is_active')
            active_users = all_users.filter(is_active=True)
            
            return {
                "all_users": list(all_users),
                "active_users": list(active_users),
            }

        except Exception as e:
            print("Error in handling active status: ", e)
            return []


    async def send_active_status(self, all_users, active_users): 
        for friend in active_users:
            await self.channel_layer.group_send(
                f"chat_chat_room_{friend['id']}",
                {
                    'type': 'active_status',       
                    'usersList': all_users     
                }
            )
    async def active_status(self,event):
        #Send message to Websocket
        await self.send(text_data=json.dumps(event))

       
    