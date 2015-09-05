# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Assessment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.URLField(max_length=255)),
                ('title', models.CharField(max_length=255)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
            ],
        ),
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.URLField(max_length=255)),
                ('title', models.CharField(max_length=255)),
                ('active', models.BooleanField(default=True)),
                ('start_date', models.DateField()),
                ('last_updated', models.DateTimeField(null=True, blank=True)),
            ],
        ),
        migrations.AddField(
            model_name='assessment',
            name='course',
            field=models.ForeignKey(to='course.Course'),
        ),
    ]
