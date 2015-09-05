# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Activity',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('user', models.CharField(max_length=255)),
                ('course', models.URLField(max_length=255, null=True, blank=True)),
                ('type', models.URLField(max_length=255)),
                ('verb', models.URLField(max_length=255)),
                ('activity', models.URLField(max_length=255)),
                ('value', models.FloatField(null=True)),
                ('name', models.CharField(max_length=255)),
                ('description', models.CharField(max_length=255)),
                ('time', models.DateTimeField(null=True)),
            ],
            options={
                'verbose_name_plural': 'activities',
            },
        ),
        migrations.CreateModel(
            name='GroupAssignment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('user', models.CharField(max_length=255)),
                ('group', models.CharField(max_length=1, choices=[(b'A', b'Group A: Dashboard'), (b'B', b'Group B: No Dashboard')])),
            ],
        ),
    ]
