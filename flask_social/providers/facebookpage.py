# -*- coding: utf-8 -*-
"""
    flask.ext.social.providers.facebookpage
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module contains the Flask-Social facebookpage code

    :copyright: (c) 2012 by Ravi Ithal.
    :license: MIT, see LICENSE for more details.
"""

from __future__ import absolute_import


import facebook

config = {
    'id': 'facebookpage',
    'name': 'facebookpage',
    'install': 'pip install facebook-sdk',
    'module': 'flask_social.providers.facebookpage',
    'base_url': 'https://graph.facebook.com/',
    'request_token_url': None,
    'access_token_url': '/oauth/access_token',
    'authorize_url': 'https://www.facebook.com/dialog/oauth',
    'request_token_params': {
        'scope': 'email'
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
    profile_url = "http://facebook.com/profile.php?id=%s" % profile['id']
    image_url = "http://graph.facebook.com/%s/picture" % profile['id']

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
