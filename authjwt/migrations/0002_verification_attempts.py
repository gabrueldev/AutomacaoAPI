import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authjwt', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='emailverification',
            name='attempts',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='emailverification',
            name='code',
            field=models.CharField(max_length=64),
        ),
        migrations.AlterField(
            model_name='emailverification',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
