from django.urls import path
from .views import (
    CalendarView,
    CalendarEventsAPI,
    ReservationCreateView,
    MyReservationListView,
    ReservationDetailView,
    reservation_cancel,
    ReservationUpdateView,
    ReservationMoveView,
    google_oauth_start,
    google_oauth_callback,
    google_oauth_disconnect,
    google_sync_toggle,
)

urlpatterns = [
    path("", CalendarView.as_view(), name="home"),
    # F-06: my reservations list  (/reservations/my/?tab=upcoming or ?tab=past)
    path("my/", MyReservationListView.as_view(), name="my_reservations"),
    # F-09: reservation create
    path("create/", ReservationCreateView.as_view(), name="reservation_create"),
    # F-10: reservation detail
    path("<int:pk>/", ReservationDetailView.as_view(), name="reservation_detail"),
    # F-11: reservation edit
    path("<int:pk>/edit/", ReservationUpdateView.as_view(), name="reservation_edit"),
    # F-12: reservation cancel
    path("<int:pk>/cancel/", reservation_cancel, name="reservation_cancel"),
    path('events/', CalendarEventsAPI.as_view(), name='calendar_events'),
    path('<int:pk>/move/', ReservationMoveView.as_view(), name='reservation_move'),
    path('auth/google/', google_oauth_start, name='google_oauth_start'),
    path('auth/google/callback/', google_oauth_callback, name='google_oauth_callback'),
    path('auth/google/disconnect/', google_oauth_disconnect, name='google_oauth_disconnect'),
    path('auth/google/sync-toggle/', google_sync_toggle, name='google_sync_toggle'),
]