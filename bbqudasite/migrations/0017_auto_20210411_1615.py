# Generated by Django 3.1.2 on 2021-04-11 20:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bbqudasite', '0016_auto_20210411_1610'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customtrail',
            name='file',
            field=models.FileField(upload_to='custom_trails/'),
        ),
    ]