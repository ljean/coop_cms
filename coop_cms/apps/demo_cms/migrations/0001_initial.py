# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
import coop_cms.models
import django.utils.timezone
from django.conf import settings
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('coop_cms', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('sites', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Article',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('slug', models.CharField(unique=True, max_length=100, db_index=True)),
                ('title', models.TextField(default=b'', verbose_name='title', blank=True)),
                ('subtitle', models.TextField(default=b'', verbose_name='subtitle', blank=True)),
                ('content', models.TextField(default=b'', verbose_name='content', blank=True)),
                ('publication', models.IntegerField(default=1, verbose_name='publication', choices=[(0, 'Draft'), (1, 'Published'), (2, 'Archived')])),
                ('template', models.CharField(default=b'', max_length=200, verbose_name='template', blank=True)),
                ('logo', models.ImageField(default=b'', null=True, upload_to=coop_cms.models.get_logo_folder, blank=True)),
                ('temp_logo', models.ImageField(default=b'', null=True, upload_to=coop_cms.models.get_logo_folder, blank=True)),
                ('summary', models.TextField(default=b'', verbose_name='Summary', blank=True)),
                ('in_newsletter', models.BooleanField(default=True, help_text='Make this article available for newsletters.', verbose_name='In newsletter')),
                ('headline', models.BooleanField(default=False, help_text='Make this article appear on the home page', verbose_name='Headline')),
                ('publication_date', models.DateTimeField(default=datetime.datetime.now, verbose_name='Publication date')),
                ('author', models.ForeignKey(default=None, blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('category', models.ForeignKey(related_name='demo_cms_article_rel', default=None, blank=True, to='coop_cms.ArticleCategory', null=True, verbose_name='Category')),
                ('homepage_for_site', models.ForeignKey(related_name='homepage_article', default=None, blank=True, to='sites.Site', null=True, verbose_name='Homepage for site')),
                ('sites', models.ManyToManyField(default=[1], to='sites.Site', verbose_name='site')),
            ],
            options={
                'abstract': False,
                'verbose_name': 'article',
                'verbose_name_plural': 'articles',
            },
        ),
        migrations.CreateModel(
            name='ModeratedArticle',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('demo_cms.article',),
        ),
        migrations.CreateModel(
            name='PrivateArticle',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('demo_cms.article',),
        ),
    ]
