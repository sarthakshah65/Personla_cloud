from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0002_account_plan_name_account_security_profile_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="upload",
            name="file",
            field=models.FileField(blank=True, null=True, upload_to="uploads/%Y/%m/%d"),
        ),
    ]
