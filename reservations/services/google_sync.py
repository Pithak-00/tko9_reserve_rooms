from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from accounts.models import UserGoogleToken
import logging
logger = logging.getLogger(__name__)

class GoogleSyncService:
    def __init__(self, user):
        try:
            self.token_obj = user.google_token
            self.no_op = not self.token_obj.sync_enabled
        except UserGoogleToken.DoesNotExist:
            self.no_op = True

    def _get_service(self):
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
        if self.no_op: return
        try:
            svc = self._get_service()
            event = svc.events().insert(
                calendarId='primary', body=self._build_body(reservation)
            ).execute()
            reservation.google_event_id = event['id']
            reservation.save(update_fields=['google_event_id'])
        except Exception as e:
            logger.warning(f'GoogleSync create_event failed: {e}')

    def update_event(self, reservation):
        if self.no_op: return
        if not reservation.google_event_id:
            return self.create_event(reservation)
        try:
            svc = self._get_service()
            svc.events().patch(
                calendarId='primary',
                eventId=reservation.google_event_id,
                body=self._build_body(reservation)
            ).execute()
        except Exception as e:
            logger.warning(f'GoogleSync update_event failed: {e}')

    def delete_event(self, reservation):
        if self.no_op or not reservation.google_event_id: return
        try:
            svc = self._get_service()
            svc.events().delete(
                calendarId='primary',
                eventId=reservation.google_event_id
            ).execute()
        except Exception as e:
            logger.warning(f'GoogleSync delete_event failed: {e}')