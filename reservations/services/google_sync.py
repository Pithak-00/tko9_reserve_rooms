import logging
from django.conf import settings
from accounts.models import UserGoogleToken

logger = logging.getLogger(__name__)

try:
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False


class GoogleSyncService:
    def __init__(self, user):
        if not GOOGLE_API_AVAILABLE:
            self.no_op = True
            return
        try:
            self.token_obj = user.google_token
            self.no_op = not self.token_obj.sync_enabled
        except UserGoogleToken.DoesNotExist:
            self.no_op = True

    def _refresh_token(self):
        """期限切れのアクセストークンをリフレッシュトークンで更新する"""
        import requests
        from django.utils import timezone
        from datetime import timedelta
        try:
            resp = requests.post('https://oauth2.googleapis.com/token', data={
                'client_id':     settings.GOOGLE_CLIENT_ID,
                'client_secret': settings.GOOGLE_CLIENT_SECRET,
                'refresh_token': self.token_obj.refresh_token,
                'grant_type':    'refresh_token',
            }, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            self.token_obj.access_token = data['access_token']
            self.token_obj.token_expiry = timezone.now() + timedelta(
                seconds=data.get('expires_in', 3600))
            self.token_obj.save(update_fields=['access_token', 'token_expiry'])
        except Exception as e:
            logger.error(f'Token refresh failed: {e}')
            self.token_obj.sync_enabled = False
            self.token_obj.save(update_fields=['sync_enabled'])
            self.no_op = True

    def _get_service(self):
        from django.utils import timezone
        if self.token_obj.token_expiry and self.token_obj.token_expiry <= timezone.now():
            self._refresh_token()
        if self.no_op:
            return None
        creds = Credentials(
            token=self.token_obj.access_token,
            refresh_token=self.token_obj.refresh_token,
            token_uri='https://oauth2.googleapis.com/token',
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
        )
        return build('calendar', 'v3', credentials=creds)

    def _build_body(self, reservation):
        body = {
            'summary': reservation.title,
            'location': reservation.room.name,
            'description': reservation.notes or '',
            'start': {'dateTime': reservation.start_at.isoformat(),
                      'timeZone': 'Asia/Tokyo'},
            'end':   {'dateTime': reservation.end_at.isoformat(),
                      'timeZone': 'Asia/Tokyo'},
        }
        if reservation.recurrence_rule:
            body['recurrence'] = ['RRULE:' + reservation.recurrence_rule]
        return body

    def create_event(self, reservation):
        if self.no_op:
            return
        try:
            svc = self._get_service()
            if svc is None:
                return
            event = svc.events().insert(
                calendarId='primary', body=self._build_body(reservation)
            ).execute()
            reservation.google_event_id = event['id']
            reservation.save(update_fields=['google_event_id'])
        except Exception as e:
            logger.warning(f'GoogleSync create_event failed: {e}')

    def update_event(self, reservation):
        if self.no_op:
            return
        if not reservation.google_event_id:
            return self.create_event(reservation)
        try:
            svc = self._get_service()
            if svc is None:
                return
            svc.events().patch(
                calendarId='primary',
                eventId=reservation.google_event_id,
                body=self._build_body(reservation)
            ).execute()
        except Exception as e:
            logger.warning(f'GoogleSync update_event failed: {e}')

    def delete_event(self, reservation):
        if self.no_op or not reservation.google_event_id:
            return
        try:
            svc = self._get_service()
            if svc is None:
                return
            svc.events().delete(
                calendarId='primary',
                eventId=reservation.google_event_id
            ).execute()
        except Exception as e:
            logger.warning(f'GoogleSync delete_event failed: {e}')
