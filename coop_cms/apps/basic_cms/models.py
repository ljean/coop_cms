# -*- coding: utf-8 -*-
"""models"""

from __future__ import unicode_literals

from coop_cms.models import BaseArticle, BaseNavTree


class Article(BaseArticle): # pylint: disable=W5101
    """basic_cms.Article is equal to the BaseArticle abstract"""

    pass


class NavTree(BaseNavTree): # pylint: disable=W5101
    """
    basic_cms.NavTree is equal to the BaseNavTree abstract
    DEPRECATED : You should not redefine a NavTree anymore
    """
    pass
