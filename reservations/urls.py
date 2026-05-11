from django.urls import path
from .views import (
    CalendarView,
    ReservationCreateView,
    MyReservationListView,
    ReservationDetailView,
    reservation_cancel,
    ReservationUpdateView,
)

urlpatterns = [
    path("", CalendarView.as_view(), name="home"),
    # F-06: my reservations list
    path("my/", MyReservationListView.as_view(), name="my_reservations"),
    # F-09: reservation create
    path("create/", ReservationCreateView.as_view(), name="reservation_create"),
    # F-10: reservation detail
    path("<int:pk>/", ReservationDetailView.as_view(), name="reservation_detail"),
    # F-11: reservation edit
    path("<int:pk>/edit/", ReservationUpdateView.as_view(), name="reservation_edit"),
    # F-12: reservation cancel
    path("<int:pk>/cancel/", reservation_cancel, name="reservation_cancel"),
]
