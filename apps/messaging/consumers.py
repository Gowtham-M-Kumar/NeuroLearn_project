import json
from channels.generic.websocket import AsyncWebsocketConsumer

class VideoCallConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        
        if not self.user.is_authenticated:
            await self.close()
            return
            
        # Get the ID of the user we want to call/chat with
        self.other_user_id = self.scope['url_route']['kwargs']['user_id']
        
        # Create a unique room name based on the two user IDs (sorted)
        # This ensures both users join the same room regardless of who initiated
        user_ids = sorted([self.user.id, int(self.other_user_id)])
        self.room_group_name = f"video_call_{user_ids[0]}_{user_ids[1]}"
        
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

    # Receive message from WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'signal_message',
                'message': data,
                'sender_id': self.user.id
            }
        )

    # Receive message from room group
    async def signal_message(self, event):
        message = event['message']
        sender_id = event['sender_id']
        
        # Do not send the message back to the sender
        if sender_id != self.user.id:
            await self.send(text_data=json.dumps(message))
