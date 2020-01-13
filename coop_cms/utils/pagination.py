# -*- coding: utf-8 -*-
"""utils"""

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def paginate(request, queryset, items_count):
    try:
        page = int(request.GET.get('page', 0) or 0)
    except ValueError:
        page = 1
    paginator = Paginator(queryset, items_count)
    try:
        page_obj = paginator.page(page or 1)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        page_obj = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        page_obj = paginator.page(paginator.num_pages)
    return page_obj
