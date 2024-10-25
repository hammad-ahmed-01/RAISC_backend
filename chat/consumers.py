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
            # Save the session to ensure it's created
            await sync_to_async(self.scope['session'].save)()
    
        # Assign a session identifier to unauthenticated users
        if not self.scope['user'].is_authenticated:
            self.session_id = self.scope['session'].session_key  # Assign session ID for unauthenticated user
        else:
            self.session_id = None
    
        # Fetch the ChatGroup instance using the group_id
        self.chat_group = await self.get_chat_group(self.group_id)
    
        if not self.chat_group:
            await self.close()
            return
    
        # Join the chat group
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
    
        # Send the chat history to the user upon connecting
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
            # Save the question to the database
            question = await self.save_question(user, message_content, self.chat_group)
            # Broadcast the question to the group
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'chat_message',
                    'message': f"Question: {message_content} (Asked by {user.username if user.is_authenticated else 'Anonymous'})",
                    'question_id': question.id  # Include the question_id in the message
                }
            )
        elif message_type == 'answer':
            # Get the question ID from the message
            question_id = data.get('question_id')

            if question_id is not None:
                # Handle permission check for who can answer the question
                await self.handle_answer_permission(user, message_content, question_id)
            else:
                # Respond with an error if no question_id is provided
                await self.send(text_data=json.dumps({
                    'error': 'No question_id provided for answer.'
                }))

    async def chat_message(self, event):
        """Broadcast the message to WebSocket clients."""
        message = event['message']
        question_id = event.get('question_id')
        await self.send(text_data=json.dumps({
            'message': message,
            'question_id': question_id  # Include the question_id in the broadcast message
        }))

    @sync_to_async
    def get_chat_group(self, group_id):
        """Fetch the ChatGroup instance by ID."""
        try:
            return ChatGroup.objects.get(id=group_id)
        except ChatGroup.DoesNotExist:
            return None

    @sync_to_async
    def save_question(self, user, message_content, chat_group):
        """Save a question to the database and return it."""
        return Question.objects.create(
            group=chat_group,
            asked_by=user if user.is_authenticated else None,
            session_id=self.session_id if not user.is_authenticated else None,
            text=message_content
        )


    @sync_to_async
    def get_question(self, question_id):
        """Fetch a question by its ID."""
        try:
            return Question.objects.get(id=question_id, group=self.chat_group)
        except Question.DoesNotExist:
            return None

    async def handle_answer_permission(self, user, message_content, question_id):
        """Handle permission check for answering a question."""
        question = await self.get_question(question_id)

        if question is None:
            await self.send(text_data=json.dumps({
                'error': 'Invalid question_id. No such question exists.'
            }))
            return

        # Check if the user is a doctor (doctors can answer any question)
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
        """Save the answer and broadcast it to the chat group."""
        # Save the answer
        await sync_to_async(Answer.objects.create)(
            question=question,
            answered_by=user if user.is_authenticated else None,
            text=message_content
        )

        # Broadcast the answer to the group
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'chat_message',
                'message': (
                    f"Answer: {message_content} "
                    f"(Answered by {user.username if user.is_authenticated else f'Anonymous - session - {self.session_id}'})"
                ),
                'question_id': question.id
            }
        )


    @sync_to_async
    def fetch_chat_history(self):
        """Fetch the chat history (questions and answers) for the current chat group."""
        history = []
        questions = Question.objects.filter(group=self.chat_group).prefetch_related('answers')
    
        for question in questions:
            # Include question in history
            asked_by_username = question.asked_by.username if question.asked_by else f"Anonymous - session - {question.session_id}"
            history.append({
                'message': f"Question: {question.text} (Asked by {asked_by_username})",
                'question_id': question.id
            })
    
            # Include all answers for the question
            for answer in question.answers.all():
                answered_by_username = answer.answered_by.username if answer.answered_by else f"Anonymous - session - {question.session_id}"
                history.append({
                    'message': f"Answer: {answer.text} (Answered by {answered_by_username})",
                    'question_id': question.id
                })
    
        return history
    

    async def send_chat_history(self):
        """Send the chat history to the client when they connect."""
        history = await self.fetch_chat_history()

        # Send each message in the history to the client
        for entry in history:
            await self.send(text_data=json.dumps(entry))
