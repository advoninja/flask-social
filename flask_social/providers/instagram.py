# -*- coding: utf-8 -*-
"""
    flask.ext.social.providers.instagram
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module contains the Flask-Social instagram code

    :copyright: (c) 2019 by MSKE.
    :license: MIT, see LICENSE for more details.
"""

from __future__ import absolute_import
from __future__ import print_function


import facebook

config = {
    'id': 'instagram',
    'name': 'instagram',
    'install': 'pip install facebook-sdk',
    'module': 'flask_social.providers.instagram',
    'base_url': 'https://graph.facebook.com/',
    'request_token_url': None,
    'access_token_url': '/oauth/access_token',
    'authorize_url': 'https://www.facebook.com/dialog/oauth',
    'request_token_params': {
        'scope': 'instagram_basic, pages_show_list'
    }
}

def get_api(connection, **kwargs):
    return facebook.GraphAPI(getattr(connection, 'access_token'),version='2.7')


def get_provider_user_id(response, **kwargs):
    if response:
        graph = facebook.GraphAPI(response['access_token'],version='2.7')
        fbpages = graph.get_object("me/accounts")
        page_id = fbpages.get('data')[0].get('id')
        instagram_business = graph.get_object("%s?fields=instagram_business_account" %page_id)
        if 'instagram_business_account' not in instagram_business:
            return None
        instagram_id = instagram_business.get('instagram_business_account').get('id')
        return instagram_id
    return None


def get_connection_values(response, **kwargs):
    if not response:
        return None

    try:
        access_token = response['access_token']
    except Exception as e:
        print(response)
        raise e

    graph = facebook.GraphAPI(access_token,version='2.7')
    fbpages = graph.get_object("me/accounts")
    page_id = fbpages.get('data')[0].get('id')
    instagram_business = graph.get_object("%s?fields=instagram_business_account" %page_id)
    if 'instagram_business_account' not in instagram_business:
        return None
    instagram_id = instagram_business.get('instagram_business_account').get('id')
    instagram_user = graph.get_object("%s?fields=username,name,profile_picture_url" %instagram_id)
    profile_url = "http://www.Instagram.com/%s" % instagram_user.get('username')
    image_url = instagram_user.get('profile_picture_url')

    return dict(
        provider_id=config['id'],
        provider_user_id=instagram_id,
        access_token=access_token,
        secret=None,
        display_name=instagram_user.get('username'),
        full_name = instagram_user.get('name'),
        profile_url=profile_url,
        image_url=image_url,
        email= ''
    )

def get_token_pair_from_response(response):
    return dict(
        access_token = response.get('access_token', None),
        secret = None
    )
