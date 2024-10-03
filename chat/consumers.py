from channels.generic.websocket import AsyncWebsocketConsumer
import json
from .models import ChatGroup, Question, Message
from asgiref.sync import sync_to_async

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_id = self.scope['url_route']['kwargs']['group_id']
        self.question_id = self.scope['url_route']['kwargs']['question_id']
        self.room_group_name = f'chat_{self.group_id}_{self.question_id}'

        if self.scope['user'].is_anonymous:
            await self.close()
        else:
            # Join room group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_content = text_data_json['message']

        # Get user role
        sender_role = self.scope['user'].user_type

        # Save message to the database
        message = await self.save_message(self.scope['user'], self.question_id, message_content)

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message_content,
                'sender_role': sender_role,
                'timestamp': message.timestamp.isoformat(),
            }
        )

    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender_role': event['sender_role'],
            'timestamp': event['timestamp'],
        }))

    @sync_to_async
    def save_message(self, user, question_id, content):
        question = Question.objects.get(id=question_id)
        message = Message.objects.create(user=user, question=question, content=content)
        return message
