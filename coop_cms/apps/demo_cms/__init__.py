# -*- coding: utf-8 -*-
"""Example of CMS app"""

def get_article_templates(article, user):
    """
    example of functions to get custom templates
    It may depend on article or user
    """
    return (
        ('standard.html', 'Standard'),
        ('homepage.html', 'Homepage'),
        ('blog.html', 'Blog'),
        ('standard_en.html', 'English'),
    )

default_app_config = 'coop_cms.apps.demo_cms.apps.DemoCmsAppConfig'
