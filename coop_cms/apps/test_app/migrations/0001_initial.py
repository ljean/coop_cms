# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='TestClass',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('field1', models.TextField()),
                ('field2', models.TextField()),
                ('field3', models.CharField(max_length=100, blank=True)),
                ('bool_field', models.BooleanField(default=False)),
                ('int_field', models.IntegerField(default=0)),
                ('float_field', models.FloatField(default=0.0)),
                ('other_field', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='TestTag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.AddField(
            model_name='testclass',
            name='tags',
            field=models.ManyToManyField(to='test_app.TestTag', blank=True),
        ),
    ]
