from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("alerts", "0002_alter_alert_raw"),
    ]

    operations = [
        migrations.CreateModel(
            name="IngestionState",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("source", models.CharField(max_length=50, unique=True)),
                ("last_success_at", models.DateTimeField(blank=True, null=True)),
            ],
        ),
    ]
