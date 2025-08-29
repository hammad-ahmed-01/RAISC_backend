from channels.generic.websocket import AsyncWebsocketConsumer
import json
from .models import Question, Answer, ChatGroup
from asgiref.sync import sync_to_async
from django.contrib.auth.models import AnonymousUser

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_id = self.scope['url_route']['kwargs']['group_id']
        self.group_name = f"chat_{self.group_id}"
    
        # Check if the session exists, if not, create one
        if not self.scope['session'].session_key:
            await sync_to_async(self.scope['session'].save)()
    
        # Assign a session identifier to unauthenticated users
        if not self.scope['user'].is_authenticated:
            self.session_id = self.scope['session'].session_key
        else:
            self.session_id = None
    
        self.chat_group = await self.get_chat_group(self.group_id)
        if not self.chat_group:
            await self.close()
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # Send chat history with explicit "type" fields
        await self.send_chat_history()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')  # 'question' or 'answer'
        message_content = data.get('message')

        user = self.scope['user']
        user_type = user.user_type if user.is_authenticated else 'anonymous'

        if message_type == 'question' and (user_type == 'patient' or user_type == 'anonymous'):
            question = await self.save_question(user, message_content, self.chat_group)
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'chat_message',
                    'message': message_content,
                    'question_id': question.id,
                    'role': 'question'
                }
            )
        elif message_type == 'answer':
            question_id = data.get('question_id')
            if question_id:
                await self.handle_answer_permission(user, message_content, question_id)
            else:
                await self.send(text_data=json.dumps({
                    'error': 'No question_id provided for answer.'
                }))

    async def chat_message(self, event):
        """Broadcast the message to WebSocket clients."""
        await self.send(text_data=json.dumps({
            'type': event['role'],  # 'question' or 'answer'
            'message': event['message'],
            'question_id': event.get('question_id')  # Present for questions
        }))

    @sync_to_async
    def get_chat_group(self, group_id):
        try:
            return ChatGroup.objects.get(id=group_id)
        except ChatGroup.DoesNotExist:
            return None

    @sync_to_async
    def save_question(self, user, message_content, chat_group):
        return Question.objects.create(
            group=chat_group,
            asked_by=user if user.is_authenticated else None,
            session_id=self.session_id if not user.is_authenticated else None,
            text=message_content
        )

    @sync_to_async
    def get_question(self, question_id):
        try:
            return Question.objects.get(id=question_id, group=self.chat_group)
        except Question.DoesNotExist:
            return None

    async def handle_answer_permission(self, user, message_content, question_id):
        question = await self.get_question(question_id)

        if question is None:
            await self.send(text_data=json.dumps({'error': 'Invalid question_id'}))
            return

        if user.is_authenticated and user.user_type == 'doctor':
            await self.save_and_broadcast_answer(user, message_content, question)
        
        # Check if the user is the patient who asked the question (authenticated)
        elif user.is_authenticated:
            question_asked_by = await sync_to_async(lambda: question.asked_by)()
            if question_asked_by == user:
                await self.save_and_broadcast_answer(user, message_content, question)
            else:
                await self.send(text_data=json.dumps({
                    'error': 'You are not authorized to answer this question.'
                }))

        # Check if the user is the unauthenticated session that asked the question
        elif not user.is_authenticated:
            # Check that the session_id matches and that the question wasn't asked by an authenticated user
            question_asked_by = await sync_to_async(lambda: question.asked_by)()  # Ensure ORM call is async
            if question.session_id == self.session_id and not question_asked_by:
                await self.save_and_broadcast_answer(AnonymousUser(), message_content, question)
            else:
                await self.send(text_data=json.dumps({
                    'error': 'You are not authorized to answer this question.'
                }))

        else:
            await self.send(text_data=json.dumps({
                'error': 'You are not authorized to answer this question.'
            }))

    async def save_and_broadcast_answer(self, user, message_content, question):
        await sync_to_async(Answer.objects.create)(
            question=question,
            answered_by=user if user.is_authenticated else None,
            text=message_content
        )
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'chat_message',
                'message': message_content,
                'question_id': question.id,
                'role': 'answer'
            }
        )

    @sync_to_async
    def fetch_chat_history(self):
        history = []
        questions = Question.objects.filter(group=self.chat_group).prefetch_related('answers')
    
        for question in questions:
            asked_by = question.asked_by.username if question.asked_by else f"Anonymous - {question.session_id}"
            history.append({
                'type': 'question',
                'message': f"{question.text} (Asked by {asked_by})",
                'question_id': question.id
            })
            for answer in question.answers.all():
                answered_by = answer.answered_by.username if answer.answered_by else "Anonymous"
                history.append({
                    'type': 'answer',
                    'message': f"{answer.text} (Answered by {answered_by})",
                    'question_id': question.id
                })
        return history

    async def send_chat_history(self):
        history = await self.fetch_chat_history()
        for entry in history:
            await self.send(text_data=json.dumps(entry))
