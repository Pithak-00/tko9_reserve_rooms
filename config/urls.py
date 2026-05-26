from django.contrib import admin
from django.urls import path, include
from reservations.views import CalendarView, ReservationTimelineView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", ReservationTimelineView.as_view(), name="home"),
    path("calendar/", CalendarView.as_view(), name="calendar"),
    path("accounts/", include("accounts.urls")),
    path("reservations/", include("reservations.urls")),
    path("admin-panel/", include("admin_panel.urls")),
    path("rooms/", include("rooms.urls")),
]
