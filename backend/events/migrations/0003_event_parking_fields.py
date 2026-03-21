from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0002_event_is_approved'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='latitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name='event',
            name='longitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name='event',
            name='parking_info',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='event',
            name='parking_map_url',
            field=models.URLField(blank=True),
        ),
    ]
