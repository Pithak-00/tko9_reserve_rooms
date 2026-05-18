import uuid
import json
import logging

from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.views import View
from django.views.generic import TemplateView, CreateView, ListView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from datetime import date, datetime, timedelta
from django.utils import timezone
from django.utils.timezone import localtime
from django.urls import reverse
from django.conf import settings

from .models import Room, Reservation
from .forms import ReservationForm
from accounts.models import Department, UserGoogleToken
try:
    from .services.google_sync import GoogleSyncService
    GOOGLE_SYNC_AVAILABLE = True
except ImportError:
    GOOGLE_SYNC_AVAILABLE = False
    class GoogleSyncService:
        """google-api-python-client 未インストール時のダミー"""
        def __init__(self, user): pass
        def create_event(self, r): pass
        def update_event(self, r): pass
        def delete_event(self, r): pass

logger = logging.getLogger(__name__)

# google_auth_oauthlib は F-04-R09 Google 同期機能でのみ使用
# pip install google-auth-oauthlib google-api-python-client python-dateutil が必要
try:
    from google_auth_oauthlib.flow import Flow
    GOOGLE_OAUTH_AVAILABLE = True
except ImportError:
    GOOGLE_OAUTH_AVAILABLE = False

try:
    from dateutil.rrule import rrulestr
    DATEUTIL_AVAILABLE = True
except ImportError:
    DATEUTIL_AVAILABLE = False


def home(request):
    return HttpResponse("meeting room reservation system")


def _generate_recurrence_instances(parent: Reservation, until=None):
    """親予約の recurrence_rule からインスタンス予約を一括生成"""
    if not DATEUTIL_AVAILABLE:
        logger.warning('python-dateutil が未インストールのため繰り返し生成をスキップ')
        return
    duration = parent.end_at - parent.start_at
    rule_str = f'DTSTART:{parent.start_at.strftime("%Y%m%dT%H%M%SZ")}\nRRULE:{parent.recurrence_rule}'
    rule = rrulestr(rule_str)
    instances = []
    for dt in rule:
        if until and dt.date() > until: break
        if dt == parent.start_at: continue  # 親自身をスキップ
        instances.append(Reservation(
            room=parent.room,
            user=parent.user,
            reserved_by=parent.reserved_by,
            title=parent.title,
            start_at=dt,
            end_at=dt + duration,
            parent_reservation=parent,
            recurrence_id=dt,
        ))
    Reservation.objects.bulk_create(instances)


# F-04
class CalendarView(LoginRequiredMixin, TemplateView):
    template_name = 'reservations/calendar.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        view  = self.request.GET.get('view', 'week')  # day/week/month
        date_str = self.request.GET.get('date')
        try:
            target = datetime.strptime(date_str, '%Y-%m-%d').date()
        except (TypeError, ValueError):
            target = date.today()

        # 会議室一覧（JSON として埋め込み）
        rooms = Room.objects.filter(is_active=True).order_by('name')
        rooms_json = json.dumps([
            {'id': r.id, 'name': r.name,
             'color': r.color or '#3182CE',
             'calendar_url': r.calendar_url}
            for r in rooms
        ], ensure_ascii=False)

        ctx.update({
            'rooms_list': list(rooms),
            'view': view,
            'target_date': target.isoformat(),
            'rooms_json': rooms_json,
            'fc_initial_view': {
                'day': 'timeGridDay',
                'week': 'timeGridWeek',
                'month': 'dayGridMonth',
            }.get(view, 'timeGridWeek'),
        })
        return ctx


# F-06
class MyReservationListView(LoginRequiredMixin, ListView):
    model = Reservation
    template_name = "reservations/my_reservations.html"
    context_object_name = "reservations"

    def get_queryset(self):
        tab = self.request.GET.get("tab", "upcoming")
        now = timezone.now()

        if tab == "past":
            return (
                Reservation.objects.filter(user=self.request.user, start_at__lt=now)
                .select_related("room")
                .order_by("-start_at")
            )
        else:
            return (
                Reservation.objects.filter(
                    user=self.request.user, start_at__gte=now, is_cancelled=False
                )
                .select_related("room")
                .order_by("start_at")
            )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tab = self.request.GET.get("tab", "upcoming")
        context["active_tab"] = tab

        now = timezone.now()
        context["upcoming_count"] = Reservation.objects.filter(
            user=self.request.user, start_at__gte=now, is_cancelled=False
        ).count()
        context["past_count"] = Reservation.objects.filter(
            user=self.request.user, start_at__lt=now
        ).count()
        return context


# F-09
class ReservationCreateView(CreateView):
    model = Reservation
    form_class = ReservationForm
    template_name = "reservations/create.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        room_id = self.request.GET.get("room")
        selected_room = None
        if room_id:
            try:
                selected_room = Room.objects.get(id=room_id)
            except Room.DoesNotExist:
                selected_room = None
        context["selected_room"] = selected_room
        return context

    def get_initial(self):
        initial = super().get_initial()

        room_id = self.request.GET.get("room")
        if room_id:
            initial["room"] = room_id

        date_str     = self.request.GET.get("date")
        time_str     = self.request.GET.get("time")
        end_time_str = self.request.GET.get("end_time")
        if date_str and time_str:
            try:
                start_at = datetime.strptime(
                    date_str + " " + time_str, "%Y-%m-%d %H:%M"
                )
                # end_time が渡されていればそれを使う。なければ開始+30分
                if end_time_str:
                    end_at = datetime.strptime(
                        date_str + " " + end_time_str, "%Y-%m-%d %H:%M"
                    )
                    # 日をまたぐ場合（例：23:30〜00:00）は翌日に補正
                    if end_at <= start_at:
                        end_at += timedelta(days=1)
                else:
                    end_at = start_at + timedelta(minutes=30)
                initial["start_at"] = start_at
                initial["end_at"] = end_at
            except ValueError:
                pass

        return initial

    def form_valid(self, form):
        reservation = form.save(commit=False)
        reservation.user = self.request.user
        recurrence_rule = form.cleaned_data.get('recurrence_rule', '')
        reservation.recurrence_rule = recurrence_rule
        reservation.save()
        # 繰り返しインスタンスを一括生成
        if recurrence_rule:
            _generate_recurrence_instances(reservation)
        GoogleSyncService(self.request.user).create_event(reservation)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("reservation_detail", kwargs={"pk": self.object.pk})


# F-10
class ReservationDetailView(LoginRequiredMixin, DetailView):
    model = Reservation
    template_name = "reservations/detail.html"
    context_object_name = "reservation"


class ReservationUpdateView(LoginRequiredMixin, UpdateView):
    model = Reservation
    form_class = ReservationForm
    template_name = "reservations/edit.html"
    context_object_name = "reservation"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["room"].disabled = True
        return form

    def get_success_url(self):
        return reverse("reservation_detail", kwargs={"pk": self.object.pk})


@require_POST
@login_required
def reservation_cancel(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)

    if reservation.user != request.user:
        return redirect("calendar")

    reservation.is_cancelled = True
    reservation.save()

    return redirect("calendar")


class CalendarEventsAPI(LoginRequiredMixin, View):
    def get(self, request):
        start_str = request.GET.get('start')
        end_str   = request.GET.get('end')
        room_ids_str = request.GET.get('room_ids', '')

        try:
            start = datetime.fromisoformat(start_str)
            end   = datetime.fromisoformat(end_str)
        except (TypeError, ValueError):
            return JsonResponse({'error': 'invalid params'}, status=400)

        qs = Reservation.objects.filter(
            start_at__lt=end, end_at__gt=start,
            is_cancelled=False
        ).select_related('room', 'user')

        if room_ids_str:
            ids = [int(x) for x in room_ids_str.split(',') if x.strip().isdigit()]
            qs = qs.filter(room_id__in=ids)

        events = []
        for res in qs:
            color = res.room.color or '#3182CE'
            events.append({
                'id': res.id,
                'title': res.title,
                'start': localtime(res.start_at).isoformat(),
                'end':   localtime(res.end_at).isoformat(),
                'room_id': res.room_id,
                'room_name': res.room.name,
                'color': color,
                'reserved_by': res.reserved_by,
                'is_owner': res.user == request.user,
                'editable': res.user == request.user or request.user.is_staff,
            })
        return JsonResponse(events, safe=False)
    

class ReservationMoveView(LoginRequiredMixin, View):
    def patch(self, request, pk):
        reservation = get_object_or_404(Reservation, pk=pk, is_cancelled=False)

        # 権限チェック
        if reservation.user != request.user and not request.user.is_staff:
            return JsonResponse({'error': '操作権限がありません'}, status=403)

        data = json.loads(request.body)
        start_at = datetime.fromisoformat(data['start_at'])
        end_at   = datetime.fromisoformat(data['end_at'])
        room_id  = data.get('room_id', reservation.room_id)

        # 重複チェック（自分自身を除く）
        conflict = Reservation.objects.filter(
            room_id=room_id,
            start_at__lt=end_at,
            end_at__gt=start_at,
            is_cancelled=False,
        ).exclude(pk=pk).exists()

        if conflict:
            return JsonResponse({'error': '競合する予約が存在します'}, status=400)

        reservation.start_at = start_at
        reservation.end_at   = end_at
        reservation.room_id  = room_id
        reservation.save(update_fields=['start_at', 'end_at', 'room_id', 'updated_at'])

        # Google カレンダー同期
        try:
            GoogleSyncService(request.user).update_event(reservation)
        except Exception as e:
            logger.warning(f'Google sync failed: {e}')

        color = reservation.room.color or '#3182CE'
        return JsonResponse({'id': reservation.id, 'color': color}, status=200)
    

# ─────────────────────────────────────────────────────────────
# Google OAuth 2.0 ビュー
# ─────────────────────────────────────────────────────────────

@login_required
def google_oauth_start(request):
    """Google OAuth 認証画面へリダイレクト"""
    if not GOOGLE_OAUTH_AVAILABLE:
        return HttpResponse('google-auth-oauthlib が未インストールです。pip install google-auth-oauthlib を実行してください。', status=501)
    flow = Flow.from_client_config(
        {
            'web': {
                'client_id': settings.GOOGLE_CLIENT_ID,
                'client_secret': settings.GOOGLE_CLIENT_SECRET,
                'redirect_uris': [settings.GOOGLE_REDIRECT_URI],
                'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                'token_uri': 'https://oauth2.googleapis.com/token',
            }
        },
        scopes=settings.GOOGLE_CALENDAR_SCOPES,
    )
    flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
    auth_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent',
    )
    request.session['google_oauth_state'] = state
    return redirect(auth_url)


@login_required
def google_oauth_callback(request):
    """Google からのコールバック：トークンを取得して保存"""
    if not GOOGLE_OAUTH_AVAILABLE:
        return HttpResponse('google-auth-oauthlib が未インストールです。', status=501)
    state = request.GET.get('state')
    if state != request.session.get('google_oauth_state'):
        return HttpResponseBadRequest('Invalid state parameter')

    flow = Flow.from_client_config(
        {
            'web': {
                'client_id': settings.GOOGLE_CLIENT_ID,
                'client_secret': settings.GOOGLE_CLIENT_SECRET,
                'redirect_uris': [settings.GOOGLE_REDIRECT_URI],
                'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                'token_uri': 'https://oauth2.googleapis.com/token',
            }
        },
        scopes=settings.GOOGLE_CALENDAR_SCOPES,
        state=state,
    )
    flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
    flow.fetch_token(code=request.GET.get('code'))
    creds = flow.credentials

    # UserGoogleToken に保存（or 更新）
    from django.utils import timezone
    from datetime import datetime, timezone as dt_tz
    expiry = None
    if creds.expiry:
        expiry = creds.expiry.replace(tzinfo=dt_tz.utc)
    UserGoogleToken.objects.update_or_create(
        user=request.user,
        defaults={
            'access_token':  creds.token,
            'refresh_token': creds.refresh_token or '',
            'token_expiry':  expiry,
            'sync_enabled':  True,
        }
    )
    request.session['toast'] = 'Google カレンダーと連携しました'
    return redirect('calendar')


class google_oauth_disconnect(LoginRequiredMixin, View):
    def post(self, request):
        """連携解除：トークンを revoke して削除"""
        import requests as req_lib
        try:
            token_obj = request.user.google_token
            req_lib.post('https://oauth2.googleapis.com/revoke',
                params={'token': token_obj.access_token}, timeout=5)
            token_obj.delete()
        except UserGoogleToken.DoesNotExist:
            pass
        return JsonResponse({'status': 'ok'})


class google_sync_toggle(LoginRequiredMixin, View):
    def patch(self, request):
        """同期 ON/OFF 切り替え"""
        try:
            token_obj = request.user.google_token
            token_obj.sync_enabled = not token_obj.sync_enabled
            token_obj.save(update_fields=['sync_enabled'])
            return JsonResponse({'sync_enabled': token_obj.sync_enabled})
        except UserGoogleToken.DoesNotExist:
            return JsonResponse({'error': 'Not connected'}, status=404)

# ── views.py 先頭 import に以下も追加（未追加の場合）───────────
# from django.contrib.auth.decorators import login_required
# from django.http import HttpResponseBadRequest, JsonResponse
# from django.shortcuts import redirect