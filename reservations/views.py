from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.views.generic import TemplateView, CreateView, ListView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from datetime import date, datetime, timedelta
from django.utils import timezone
from django.utils.timezone import localtime
from django.urls import reverse

from .models import Room, Reservation
from .forms import ReservationForm
from accounts.models import Department
from django.views.generic import DetailView


def home(request):
    return HttpResponse("meeting room reservation system")


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

        date_str = self.request.GET.get("date")
        time_str = self.request.GET.get("time")
        if date_str and time_str:
            try:
                start_at = datetime.strptime(
                    date_str + " " + time_str, "%Y-%m-%d %H:%M"
                )
                end_at = start_at + timedelta(minutes=30)
                initial["start_at"] = start_at
                initial["end_at"] = end_at
            except ValueError:
                pass

        return initial

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.reserved_by = self.request.user.name
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