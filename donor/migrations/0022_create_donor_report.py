# Generated manually for DonorReport model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('donor', '0021_alter_foodlisting_expiry_time'),
    ]

    operations = [
        migrations.CreateModel(
            name='DonorReport',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('report_text', models.TextField(help_text='Details of the report')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('food_request', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='donor_report', to='donor.foodrequest')),
                ('reporter', models.ForeignKey(help_text='The donor reporting the issue', on_delete=django.db.models.deletion.CASCADE, to='auth.user')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
