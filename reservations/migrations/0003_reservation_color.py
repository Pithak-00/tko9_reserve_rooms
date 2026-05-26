from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reservations', '0002_operation_log'),
    ]

    operations = [
        # Reservation に color フィールドを追加（デフォルト #3182CE）
        migrations.AddField(
            model_name='reservation',
            name='color',
            field=models.CharField(
                blank=True,
                default='#3182CE',
                max_length=7,
                verbose_name='カラーコード',
            ),
        ),
        # Room から color フィールドを削除
        migrations.RemoveField(
            model_name='room',
            name='color',
        ),
    ]
