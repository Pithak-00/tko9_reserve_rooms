import os

from django import forms
from accounts.models import Department, User
from reservations.models import Building, Facility, Room, RoomFacility, DepartmentRoom


class RoomForm(forms.ModelForm):
    """会議室登録・編集フォーム（F-18）"""

    # ManyToManyField with through= は ModelForm が自動生成しないため手動定義
    facilities = forms.ModelMultipleChoiceField(
        queryset=Facility.objects.all().order_by("name"),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="設備",
    )

    departments = forms.ModelMultipleChoiceField(
        queryset=Department.objects.all().order_by("name"),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="所属別表示設定",
    )

    class Meta:
        model = Room
        # is_active は一覧の「利用停止/再開」ボタンで管理するためフォームに含めない
        fields = ["name", "capacity", "facilities", "building", "floor", "departments"]
        labels = {
            "name": "室名",
            "capacity": "収容人数",
            "building": "建物",
            "floor": "階数",
        }
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "ex: 104"}),
            "capacity": forms.NumberInput(attrs={"min": 1, "placeholder": "ex: 10"}),
            "building": forms.Select(),
            "floor": forms.NumberInput(attrs={"placeholder": "ex: 3"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["facilities"].initial = self.instance.facilities.all()
            self.fields["departments"].initial = self.instance.departments.all()
        self.fields["building"].empty_label = "---"

    def clean_capacity(self):
        capacity = self.cleaned_data.get("capacity")
        if capacity is not None and capacity < 1:
            raise forms.ValidationError("1以上の整数を入力してください")
        return capacity

    def clean_name(self):
        name = self.cleaned_data.get("name")
        if not name:
            return name
        qs = Room.objects.filter(name=name)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("この室名はすでに使用されています")
        return name

    def save(self, commit=True):
        room = super().save(commit=commit)
        if commit:
            RoomFacility.objects.filter(room=room).delete()
            for facility in self.cleaned_data.get("facilities", []):
                RoomFacility.objects.create(room=room, facility=facility)

            DepartmentRoom.objects.filter(room=room).delete()
            for dept in self.cleaned_data.get("departments", []):
                DepartmentRoom.objects.create(room=room, department=dept)
        return room


# ─────────────────────────────────────────────
# ユーザー管理フォーム（F-14〜F-17）
# ─────────────────────────────────────────────


class UserCreateForm(forms.ModelForm):
    """ユーザー新規作成フォーム（F-15）"""

    department = forms.ModelChoiceField(
        queryset=Department.objects.all().order_by("name"),
        required=False,
        empty_label="（なし）",
        label="所属",
    )

    class Meta:
        model = User
        fields = ["login_id", "name", "role", "department"]
        labels = {
            "login_id": "ユーザーID",
            "name": "氏名",
            "role": "権限",
            "department": "所属",
        }
        widgets = {
            "login_id": forms.TextInput(
                attrs={
                    "placeholder": "半角英数字 50文字以内",
                    "autocomplete": "off",
                }
            ),
            "name": forms.TextInput(
                attrs={
                    "placeholder": "氏名を入力してください。",
                }
            ),
            "role": forms.Select(),
        }

    def clean_login_id(self):
        login_id = self.cleaned_data.get("login_id", "").strip()
        if User.objects.filter(login_id=login_id).exists():
            raise forms.ValidationError("このユーザーIDはすでに使用されています。")
        return login_id


class UserUpdateForm(forms.ModelForm):
    """ユーザー編集フォーム（F-15）"""

    department = forms.ModelChoiceField(
        queryset=Department.objects.all().order_by("name"),
        required=False,
        empty_label="（なし）",
        label="所属",
    )

    class Meta:
        model = User
        fields = ["name", "role", "department"]
        labels = {
            "name": "氏名",
            "role": "権限",
            "department": "所属",
        }
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": "氏名を入力してください。",
                }
            ),
            "role": forms.Select(),
        }


class CSVUploadForm(forms.Form):
    """CSVインポートフォーム（F-17）"""

    CSV_MAX_SIZE = 5 * 1024 * 1024  # 5MB

    csv_file = forms.FileField(
        label="CSVファイル",
        error_messages={
            "required": "CSVファイルを選択してください。",
        },
    )

    def clean_csv_file(self):
        f = self.cleaned_data.get("csv_file")
        if not f:
            return f

        ext = os.path.splitext(f.name)[1].lower()
        if ext != ".csv":
            raise forms.ValidationError(
                "CSVファイル（.csv）をアップロードしてください。"
            )

        allowed_mime = (
            "text/csv",
            "text/plain",
            "application/csv",
            "application/octet-stream",
        )
        if hasattr(f, "content_type") and f.content_type not in allowed_mime:
            raise forms.ValidationError("CSVファイルをアップロードしてください。")

        if f.size > self.CSV_MAX_SIZE:
            raise forms.ValidationError("ファイルサイズが上限（5MB）を超えています。")

        return f


class FacilityForm(forms.ModelForm):
    class Meta:
        model = Facility
        fields = ['name']
        labels = {'name': '設備名称'}
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '設備名称を入力',
                'maxlength': 100,
            })
        }

    def clean_name(self):
        name = self.cleaned_data['name']
        qs = Facility.objects.filter(name=name)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('この設備名称はすでに登録されています')
        return name


class BuildingForm(forms.ModelForm):  # FacilityForm と同パターン
    class Meta:
        model = Building
        fields = ['name']
        labels = {'name': '建物名称'}

    def clean_name(self):
        name = self.cleaned_data['name']
        qs = Building.objects.filter(name=name)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('この建物名称はすでに登録されています')
        return name


class DepartmentForm(forms.ModelForm):  # FacilityForm と同パターン
    class Meta:
        model = Department
        fields = ['name']
        labels = {'name': '所属名称'}

    def clean_name(self):
        name = self.cleaned_data['name']
        qs = Department.objects.filter(name=name)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('この所属名称はすでに登録されています')
        return name