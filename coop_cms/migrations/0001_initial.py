# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import coop_cms.settings
import coop_cms.models
import django.utils.timezone
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0001_initial'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Alias',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('path', models.CharField(max_length=200)),
                ('redirect_url', models.CharField(default=b'', max_length=200, blank=True)),
            ],
            options={
                'verbose_name': 'Alias',
                'verbose_name_plural': 'Aliases',
            },
        ),
        migrations.CreateModel(
            name='ArticleCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100, verbose_name='name')),
                ('slug', django_extensions.db.fields.AutoSlugField(editable=False, populate_from='name', max_length=100, blank=True, unique=True)),
                ('ordering', models.IntegerField(default=0, verbose_name='ordering')),
                ('in_rss', models.BooleanField(default=False, help_text='The articles of this category will be listed in the main rss feed', verbose_name='in rss')),
                ('sites', models.ManyToManyField(default=[1], to='sites.Site', verbose_name='site')),
            ],
            options={
                'verbose_name': 'article category',
                'verbose_name_plural': 'article categories',
            },
        ),
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('name', models.CharField(default=b'', max_length=200, verbose_name='name', blank=True)),
                ('ordering', models.IntegerField(default=100, verbose_name='ordering')),
                ('file', models.FileField(upload_to=coop_cms.models.get_doc_folder, verbose_name='file')),
                ('is_private', models.BooleanField(default=False, help_text='Check this if you do not want to publish this document to all users', verbose_name='is private')),
                ('category', models.ForeignKey(default=None, blank=True, to='coop_cms.ArticleCategory', null=True, verbose_name='category')),
            ],
            options={
                'verbose_name': 'document',
                'verbose_name_plural': 'documents',
            },
        ),
        migrations.CreateModel(
            name='Fragment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100, verbose_name='name', db_index=True)),
                ('css_class', models.CharField(default='', max_length=100, verbose_name='CSS class', blank=True)),
                ('position', models.IntegerField(default=0, verbose_name='position')),
                ('content', models.TextField(default='', verbose_name='content', blank=True)),
            ],
            options={
                'ordering': ('position', 'id'),
                'verbose_name': 'Fragment',
                'verbose_name_plural': 'Fragment',
            },
        ),
        migrations.CreateModel(
            name='FragmentFilter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('extra_id', models.CharField(max_length=100, verbose_name='extra_id', db_index=True)),
            ],
            options={
                'verbose_name': 'Fragment filter',
                'verbose_name_plural': 'Fragment filters',
            },
        ),
        migrations.CreateModel(
            name='FragmentType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100, verbose_name='name', db_index=True)),
                ('allowed_css_classes', models.CharField(default=b'', help_text='the css classed proposed when editing a fragment. It must be separated by comas', max_length=200, verbose_name='allowed css classes')),
            ],
            options={
                'verbose_name': 'Fragment type',
                'verbose_name_plural': 'Fragment types',
            },
        ),
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('name', models.CharField(default=b'', max_length=200, verbose_name='name', blank=True)),
                ('ordering', models.IntegerField(default=100, verbose_name='ordering')),
                ('file', models.ImageField(upload_to=coop_cms.settings.get_img_folder, verbose_name='file')),
            ],
            options={
                'verbose_name': 'image',
                'verbose_name_plural': 'images',
            },
        ),
        migrations.CreateModel(
            name='ImageSize',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100, verbose_name='name')),
                ('size', models.CharField(max_length=100, verbose_name='size')),
                ('crop', models.CharField(default=b'', max_length=100, verbose_name='crop', blank=True)),
            ],
            options={
                'verbose_name': 'Image size',
                'verbose_name_plural': 'Image sizes',
            },
        ),
        migrations.CreateModel(
            name='Link',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('title', models.CharField(default='title', max_length=200, verbose_name='Title')),
                ('url', models.CharField(max_length=200, verbose_name='URL')),
            ],
            options={
                'verbose_name': 'link',
                'verbose_name_plural': 'links',
            },
        ),
        migrations.CreateModel(
            name='MediaFilter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100, verbose_name='name')),
            ],
            options={
                'verbose_name': 'media filter',
                'verbose_name_plural': 'media filters',
            },
        ),
        migrations.CreateModel(
            name='NavNode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('label', models.CharField(max_length=200, verbose_name='label')),
                ('ordering', models.PositiveIntegerField(default=0, verbose_name='ordering')),
                ('object_id', models.PositiveIntegerField(null=True, verbose_name='object id', blank=True)),
                ('in_navigation', models.BooleanField(default=True, verbose_name='in navigation')),
                ('content_type', models.ForeignKey(verbose_name='content_type', blank=True, to='contenttypes.ContentType', null=True)),
                ('parent', models.ForeignKey(default=0, blank=True, to='coop_cms.NavNode', null=True, verbose_name='parent')),
            ],
            options={
                'verbose_name': 'navigation node',
                'verbose_name_plural': 'navigation nodes',
            },
        ),
        migrations.CreateModel(
            name='NavTree',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('last_update', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(default=b'default', unique=True, max_length=100, verbose_name='name', db_index=True)),
            ],
            options={
                'abstract': False,
                'verbose_name': 'Navigation tree',
                'verbose_name_plural': 'Navigation trees',
            },
        ),
        migrations.CreateModel(
            name='NavType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('search_field', models.CharField(default=b'', max_length=200, verbose_name='search field', blank=True)),
                ('label_rule', models.IntegerField(default=0, verbose_name='How to generate the label', choices=[(0, 'Use object unicode'), (1, 'Use search field'), (2, 'Use get_label')])),
                ('content_type', models.OneToOneField(verbose_name='django model', to='contenttypes.ContentType')),
            ],
            options={
                'verbose_name': 'navigable type',
                'verbose_name_plural': 'navigable types',
            },
        ),
        migrations.CreateModel(
            name='Newsletter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('subject', models.CharField(default=b'', max_length=200, verbose_name='subject', blank=True)),
                ('content', models.TextField(default=b'<br>', verbose_name='content', blank=True)),
                ('template', models.CharField(default=b'', max_length=200, verbose_name='template', blank=True)),
                ('source_url', models.URLField(default=b'', verbose_name='source url', blank=True)),
                ('is_public', models.BooleanField(default=False, verbose_name='is_public')),
            ],
            options={
                'verbose_name': 'newsletter',
                'verbose_name_plural': 'newsletters',
            },
        ),
        migrations.CreateModel(
            name='NewsletterItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField(verbose_name='object id')),
                ('ordering', models.IntegerField(default=0, verbose_name='ordering')),
                ('content_type', models.ForeignKey(verbose_name='content_type', to='contenttypes.ContentType')),
            ],
            options={
                'ordering': ['ordering'],
                'verbose_name': 'newsletter item',
                'verbose_name_plural': 'newsletter items',
            },
        ),
        migrations.CreateModel(
            name='NewsletterSending',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('scheduling_dt', models.DateTimeField(default=None, null=True, verbose_name='scheduling date', blank=True)),
                ('sending_dt', models.DateTimeField(default=None, null=True, verbose_name='sending date', blank=True)),
                ('newsletter', models.ForeignKey(to='coop_cms.Newsletter')),
            ],
            options={
                'verbose_name': 'newsletter sending',
                'verbose_name_plural': 'newsletter sendings',
            },
        ),
        migrations.CreateModel(
            name='PieceOfHtml',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('div_id', models.CharField(max_length=100, verbose_name='identifier', db_index=True)),
                ('content', models.TextField(default=b'', verbose_name='content', blank=True)),
                ('extra_id', models.CharField(default=b'', max_length=100, verbose_name='extra identifier', db_index=True, blank=True)),
            ],
            options={
                'verbose_name': 'piece of HTML',
                'verbose_name_plural': 'pieces of HTML',
            },
        ),
        migrations.CreateModel(
            name='SiteSettings',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('homepage_url', models.CharField(default=b'', help_text='if set, the homepage will be redirected to the given URL', max_length=256, verbose_name='homepage URL', blank=True)),
                ('sitemap_mode', models.IntegerField(default=1, choices=[(1, 'Only site articles'), (2, 'All articles')])),
                ('site', models.OneToOneField(verbose_name='site settings', to='sites.Site')),
            ],
            options={
                'ordering': ('site__id',),
                'verbose_name': 'Sites settings',
                'verbose_name_plural': 'Site settings',
            },
        ),
        migrations.AddField(
            model_name='newsletter',
            name='items',
            field=models.ManyToManyField(to='coop_cms.NewsletterItem', blank=True),
        ),
        migrations.AddField(
            model_name='newsletter',
            name='site',
            field=models.ForeignKey(default=1, verbose_name='site', to='sites.Site'),
        ),
        migrations.AddField(
            model_name='navtree',
            name='types',
            field=models.ManyToManyField(related_name='coop_cms_navtree_set', to='coop_cms.NavType', blank=True),
        ),
        migrations.AddField(
            model_name='navnode',
            name='tree',
            field=models.ForeignKey(verbose_name='tree', to='coop_cms.NavTree'),
        ),
        migrations.AddField(
            model_name='image',
            name='filters',
            field=models.ManyToManyField(default=None, to='coop_cms.MediaFilter', verbose_name='filters', blank=True),
        ),
        migrations.AddField(
            model_name='image',
            name='size',
            field=models.ForeignKey(default=None, blank=True, to='coop_cms.ImageSize', null=True, verbose_name='size'),
        ),
        migrations.AddField(
            model_name='fragment',
            name='filter',
            field=models.ForeignKey(default=None, blank=True, to='coop_cms.FragmentFilter', null=True, verbose_name='fragment filter'),
        ),
        migrations.AddField(
            model_name='fragment',
            name='type',
            field=models.ForeignKey(verbose_name='fragment type', to='coop_cms.FragmentType'),
        ),
        migrations.AddField(
            model_name='document',
            name='filters',
            field=models.ManyToManyField(default=None, to='coop_cms.MediaFilter', verbose_name='filters', blank=True),
        ),
        migrations.AlterUniqueTogether(
            name='newsletteritem',
            unique_together=set([('content_type', 'object_id')]),
        ),
    ]
