from rest_framework import serializers
from .models import Reservation

class CalendarEventSerializer(serializers.ModelSerializer):
    room_id   = serializers.IntegerField(source='room.id')
    room_name = serializers.CharField(source='room.name')
    color     = serializers.SerializerMethodField()
    is_owner  = serializers.SerializerMethodField()
    editable  = serializers.SerializerMethodField()

    class Meta:
        model = Reservation
        fields = [
            'id', 'title', 'start_at', 'end_at',
            'room_id', 'room_name', 'color',
            'reserved_by', 'is_owner', 'editable',
        ]

    def get_color(self, obj):
        return obj.room.color or '#3182CE'

    def get_is_owner(self, obj):
        req = self.context.get('request')
        return req and obj.user == req.user

    def get_editable(self, obj):
        req = self.context.get('request')
        if not req: return False
        return obj.user == req.user or req.user.is_staff