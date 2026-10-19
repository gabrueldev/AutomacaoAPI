from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('authjwt', '0002_verification_attempts'),
    ]

    operations = [
        migrations.RenameField(
            model_name='emailverification',
            old_name='code',
            new_name='code_hash',
        ),
    ]
