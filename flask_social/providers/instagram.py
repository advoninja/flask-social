# -*- coding: utf-8 -*-
"""
    flask.ext.social.providers.instagram
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module contains the Flask-Social instagram code

    :copyright: (c) 2019 by MSKE(Shameem).
    :license: MIT, see LICENSE for more details.
"""

from __future__ import absolute_import


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
        'scope': 'email, instagram_basic, pages_show_list'
    }
}

def get_api(connection, **kwargs):
    return facebook.GraphAPI(getattr(connection, 'access_token'),version='2.7')


def get_provider_user_id(response, **kwargs):
    if response:
        graph = facebook.GraphAPI(response['access_token'],version='2.7')
        profile = graph.get_object("me")
        return profile['id']
    return None


def get_connection_values(response, **kwargs):
    if not response:
        return None

    try:
        access_token = response['access_token']
    except Exception as e:
        print response
        raise e

    graph = facebook.GraphAPI(access_token,version='2.7')
    profile = graph.get_object("me")
    profilet = graph.get_object("me/accounts")
    print profilet
    page_id = profilet.get('data')[0].get('id')
    profilett = graph.get_object("%s?fields=instagram_business_account" %page_id)
    print profilett
    instagram_id = profilett.get('instagram_business_account').get('id')
    profilettt = graph.get_object("%s?fields=username,name,profile_picture_url" %instagram_id)
    print profilettt
    username = profilettt.get('username')
    profile_url = "http://www.Instagram.com/%s" % username
    image_url = profilettt.get('profile_picture_url')
    print profile

    return dict(
        provider_id=config['id'],
        provider_user_id=profile['id'],
        access_token=access_token,
        secret=None,
        display_name=profile.get('username', None),
        full_name = profile.get('name', None),
        profile_url=profile_url,
        image_url=image_url,
        email=profile.get('email', '')
    )

def get_token_pair_from_response(response):
    return dict(
        access_token = response.get('access_token', None),
        secret = None
    )
