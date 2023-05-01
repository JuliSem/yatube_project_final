from django.core.paginator import Paginator
from yatube.settings import POSTS_NUMBER


def short_paginator(request, post_list):
    paginator = Paginator(post_list, POSTS_NUMBER)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
