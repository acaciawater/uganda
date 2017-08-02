# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    replaces = [(b'uganda', '0001_initial'), (b'uganda', '0002_auto_20170802_2024'), (b'uganda', '0003_auto_20170802_2025')]

    dependencies = [
        ('data', '0023_auto_20170727_2302'),
    ]

    operations = [
        migrations.CreateModel(
            name='Sequence',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField(default=1)),
                ('location', models.OneToOneField(to='data.ProjectLocatie')),
            ],
            options={
                'ordering': ('order', 'location'),
            },
        ),
    ]
