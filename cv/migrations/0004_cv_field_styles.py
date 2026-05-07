from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cv', '0003_cv_font_size'),
    ]

    operations = [
        migrations.AddField(
            model_name='cv',
            name='field_styles',
            field=models.JSONField(
                default=dict,
                blank=True,
                help_text=(
                    'Per-field typography overrides. '
                    'Keys are field names (e.g. "full_name", "job_title"). '
                    'Values are dicts: {font_family, font_size, font_weight, font_style, color}.'
                ),
            ),
        ),
    ]
