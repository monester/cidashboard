# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cidashboard', '0002_cistatus_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='Jenkins',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('url', models.CharField(max_length=255)),
                ('login', models.CharField(max_length=255, null=True, blank=True)),
                ('api_key', models.CharField(max_length=255, null=True, blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Result',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('type', models.IntegerField()),
                ('result', models.CharField(default=b'SKIPPED', max_length=10)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.RemoveField(
            model_name='cistatus',
            name='jobs_results',
        ),
        migrations.RemoveField(
            model_name='cisystem',
            name='api_key',
        ),
        migrations.RemoveField(
            model_name='cisystem',
            name='login',
        ),
        migrations.RemoveField(
            model_name='cisystem',
            name='url',
        ),
        migrations.RemoveField(
            model_name='job',
            name='ci_system',
        ),
        migrations.RemoveField(
            model_name='product',
            name='jobs',
        ),
        migrations.RemoveField(
            model_name='product',
            name='views',
        ),
        migrations.RemoveField(
            model_name='productstatus',
            name='jobs_results',
        ),
        migrations.RemoveField(
            model_name='view',
            name='ci_system',
        ),
        migrations.AddField(
            model_name='cisystem',
            name='name',
            field=models.CharField(default=None, max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='jenkins',
            name='ci_system',
            field=models.ForeignKey(related_name='jenkinses', to='cidashboard.CISystem'),
        ),
        migrations.AddField(
            model_name='cistatus',
            name='_results',
            field=models.ManyToManyField(to='cidashboard.Result'),
        ),
        migrations.AddField(
            model_name='job',
            name='jenkins',
            field=models.OneToOneField(default=None, to='cidashboard.Jenkins'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='productstatus',
            name='results',
            field=models.ManyToManyField(to='cidashboard.Result'),
        ),
        migrations.AddField(
            model_name='view',
            name='jenkins',
            field=models.OneToOneField(default=None, to='cidashboard.Jenkins'),
            preserve_default=False,
        ),
    ]
