from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Room, Reservation
from datetime import datetime, timedelta, time as dt_time


def time_choices():
    choices = []
    current = datetime.strptime("00:00", "%H:%M")
    end = datetime.strptime("23:30", "%H:%M")

    while current <= end:
        value = current.strftime("%H:%M")
        label = f"{current.hour}:{current.strftime('%M')}"
        choices.append((value, label))
        current += timedelta(minutes=30)

    return choices


class RoomForm(forms.ModelForm):
    """会議室登録・編集フォーム（F-18）"""

    class Meta:
        model = Room
        fields = ["name", "capacity", "building", "floor", "is_active"]
        labels = {
            "name": "室名",
            "capacity": "収容人数",
            "building": "建物",
            "floor": "階数",
            "is_active": "利用可能",
        }
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "例：第1会議室"}
            ),
            "capacity": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "building": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "例：本館"}
            ),
            "floor": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "例：3"}
            ),
            "is_active": forms.CheckboxInput(
                attrs={"class": "form-check-input", "role": "switch"}
            ),
        }

    def clean_capacity(self):
        capacity = self.cleaned_data.get("capacity")
        if capacity is not None and capacity < 1:
            raise forms.ValidationError("1以上の整数を入力してください")
        return capacity

    def clean_name(self):
        name = self.cleaned_data.get("name")
        if not name:
            return name
        # 編集時は自分自身を除いて重複チェック
        qs = Room.objects.filter(name=name)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("この室名はすでに使用されています")
        return name


class ReservationForm(forms.ModelForm):
    reserve_date = forms.DateField(
        label="日付",
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "form-control",
            }
        ),
    )

    start_time = forms.ChoiceField(
        label="開始時刻",
        choices=time_choices(),
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )

    end_time = forms.ChoiceField(
        label="終了時刻",
        choices=time_choices(),
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )

    is_all_day = forms.BooleanField(
        label="終日",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input", "id": "isAllDay"}),
    )

    class Meta:
        model = Reservation
        fields = [
            "room",
            "title",
            "participants",
            "notes",
            "is_all_day",
        ]

        widgets = {
            "room": forms.Select(
                attrs={
                    "class": "form-select",
                    "id": "roomSelect",
                }
            ),
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "participants": forms.Textarea(
                attrs={
                    "class": "form-control no-resize",
                    "rows": 3,
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control no-resize",
                    "rows": 4,
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["room"].queryset = Room.objects.filter(is_active=True)

        if self.instance and self.instance.pk:
            local_start_at = timezone.localtime(self.instance.start_at)
            local_end_at = timezone.localtime(self.instance.end_at)

            self.fields["reserve_date"].initial = local_start_at.date()
            self.fields["is_all_day"].initial   = self.instance.is_all_day
            if not self.instance.is_all_day:
                self.fields["start_time"].initial = local_start_at.strftime("%H:%M")
                self.fields["end_time"].initial   = local_end_at.strftime("%H:%M")
        else:
            start_at   = self.initial.get("start_at")
            end_at     = self.initial.get("end_at")
            is_all_day = self.initial.get("is_all_day", False)

            self.fields["is_all_day"].initial = is_all_day

            if start_at:
                if timezone.is_aware(start_at):
                    start_at = timezone.localtime(start_at)
                self.fields["reserve_date"].initial = start_at.date()
                if not is_all_day:
                    self.fields["start_time"].initial = start_at.strftime("%H:%M")

            if end_at and not is_all_day:
                if timezone.is_aware(end_at):
                    end_at = timezone.localtime(end_at)
                self.fields["end_time"].initial = end_at.strftime("%H:%M")

    def clean(self):
        cleaned_data = super().clean()

        room = cleaned_data.get("room")
        reserve_date = cleaned_data.get("reserve_date")
        is_all_day = cleaned_data.get("is_all_day", False)

        if not reserve_date:
            return cleaned_data

        tz = timezone.get_current_timezone()

        if is_all_day:
            start = timezone.make_aware(
                datetime.combine(reserve_date, dt_time(0, 0)), tz
            )
            end = start + timedelta(minutes=30)
        else:
            start_time = cleaned_data.get("start_time")
            end_time = cleaned_data.get("end_time")

            if not start_time or not end_time:
                return cleaned_data

            start = timezone.make_aware(
                datetime.strptime(f"{reserve_date} {start_time}", "%Y-%m-%d %H:%M"), tz
            )
            end = timezone.make_aware(
                datetime.strptime(f"{reserve_date} {end_time}", "%Y-%m-%d %H:%M"), tz
            )

            if start >= end:
                raise ValidationError("終了時刻は開始時刻より後にしてください")

        cleaned_data["start_at"] = start
        cleaned_data["end_at"] = end

        if room:
            exists = Reservation.objects.filter(
                room=room,
                is_cancelled=False,
                start_at__lt=end,
                end_at__gt=start,
            )

            if self.instance.pk:
                exists = exists.exclude(pk=self.instance.pk)

            if exists.exists():
                raise ValidationError("その時間帯は既に予約されています")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.start_at = self.cleaned_data["start_at"]
        instance.end_at = self.cleaned_data["end_at"]
        instance.is_all_day = self.cleaned_data.get("is_all_day", False)

        if commit:
            instance.save()

        return instance


class ReservationFilterForm(forms.Form):
    """F-21: filter form for all-reservation list"""

    date_from = forms.DateField(
        label="date_from",
        required=False,
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "form-control",
            }
        ),
    )

    date_to = forms.DateField(
        label="date_to",
        required=False,
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "form-control",
            }
        ),
    )

    room = forms.IntegerField(
        label="room",
        required=False,
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )

    user = forms.CharField(
        label="user",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "",
            }
        ),
    )
