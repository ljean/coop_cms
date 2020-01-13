# -*- coding: utf-8 -*-

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='RssItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('link', models.URLField(verbose_name='link')),
                ('title', models.CharField(max_length=200, verbose_name='title', blank=True)),
                ('summary', models.TextField(verbose_name='summary', blank=True)),
                ('author', models.CharField(max_length=200, verbose_name='author', blank=True)),
                ('updated', models.DateTimeField(null=True, verbose_name='updated', blank=True)),
                ('processed', models.BooleanField(default=False, verbose_name='processed')),
            ],
            options={
                'verbose_name': 'RSS item',
                'verbose_name_plural': 'RSS items',
            },
        ),
        migrations.CreateModel(
            name='RssSource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.URLField(unique=True, verbose_name='url')),
                ('title', models.CharField(default=b'', max_length=200, verbose_name='title', blank=True)),
                ('last_collect', models.DateTimeField(null=True, verbose_name='last collect', blank=True)),
            ],
            options={
                'verbose_name': 'RSS source',
                'verbose_name_plural': 'RSS sources',
            },
        ),
        migrations.AddField(
            model_name='rssitem',
            name='source',
            field=models.ForeignKey(to='rss_sync.RssSource'),
        ),
    ]
