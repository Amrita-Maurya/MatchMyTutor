import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger('peer_tutor')


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    Per-user WebSocket consumer for real-time notifications.
    Clients connect to ws://.../ws/notifications/
    Each authenticated user joins their own group: notifications_user_{id}
    """

    async def connect(self):
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close(code=4001)
            return

        self.user_id = user.id
        self.group_name = f'notifications_user_{self.user_id}'

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        logger.info('WS connected: user=%s group=%s', self.user_id, self.group_name)

        await self.send(text_data=json.dumps({
            'type': 'connected',
            'message': 'Connected to MatchMyTutor notifications.',
        }))

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
            logger.info('WS disconnected: user=%s code=%s', self.user_id, close_code)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return
        if data.get('type') == 'ping':
            await self.send(text_data=json.dumps({'type': 'pong'}))

    async def notify(self, event):
        """Handler called when group_send is used with type='notify'."""
        await self.send(text_data=json.dumps({
            'type': event.get('category', 'notification'),
            'message': event.get('message', ''),
            'data': event.get('data', {}),
        }))
