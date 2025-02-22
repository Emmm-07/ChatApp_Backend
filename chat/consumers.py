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
        r_name = recipient.first_name
        s_name=sender.first_name
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
                    'recipient':r_id
                }
            )
            print("MESSAGE RECEIVED")
        except Exception as e:
            print("Error:",e)
        
    async def chat_message(self,event):
        print("MESSAGE SENT")
        #Send message to Websocket
        await self.send(text_data=json.dumps(event))