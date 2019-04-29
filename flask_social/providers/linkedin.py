from __future__ import absolute_import

from linkedin import linkedin
from linkedin.models import AccessToken
import time

config = {
    'id': 'linkedin',
    'name': 'LinkedIn',
    'install': 'pip install -e git+https://github.com/advoninja/python-linkedin@develop#egg=python-linkedin',
    'module': 'flask_social.providers.linkedin',
    'base_url': 'https://api.linkedin.com/',
    'request_token_url': None,
    'access_token_url': 'https://www.linkedin.com/oauth/v2/accessToken',
    'authorize_url': 'https://www.linkedin.com/oauth/v2/authorization',
    'request_token_params': {
        'state': 'HSSRJKL02318akybgj857'
    }
}

selectors = ('id', 'first-name', 'last-name', 'email-address',
             'site-standard-profile-request', 'picture-url')


def get_api(connection, **kwargs):
    auth = linkedin.LinkedInAuthentication(
        kwargs.get('consumer_key'),
        kwargs.get('consumer_secret'),
        None,
        linkedin.PERMISSIONS.enums.values()
    )
    now = int(time.time())
    auth.token = AccessToken(getattr(connection, 'access_token'),
                             getattr(connection, 'expires_at') - now)
    api = linkedin.LinkedInApplication(auth)
    return api


def get_provider_user_id(response, **kwargs):
    if response:
        auth = linkedin.LinkedInAuthentication(None, None, None, None)
        auth.token = AccessToken(response['access_token'], response['expires_in'])
        api = linkedin.LinkedInApplication(auth)

        profile = api.get_profile(selectors=selectors)
        return profile['id']
    return None


def get_connection_values(response, **kwargs):
    if not response:
        return None

    access_token = response['access_token']
    expires_in = response['expires_in']

    expires_at = int(time.time()) + expires_in
    auth = linkedin.LinkedInAuthentication(None, None, None, None)
    auth.token = AccessToken(response['access_token'], response['expires_in'])
    api = linkedin.LinkedInApplication(auth)
    profile = api.get_profile(selectors=selectors)

    # profile_url = profile['siteStandardProfileRequest']['url']
    profile_url = ''
    image_url = profile['pictureUrl'] if 'pictureUrl' in profile else '' 

    return dict(
        provider_id=config['id'],
        provider_user_id=profile['id'],
        access_token=access_token,
        secret=None,
        display_name=profile['firstName'],
        full_name = '%s %s' % (profile['firstName'], profile['lastName']),
        profile_url=profile_url,
        image_url=image_url,
        expires_at=expires_at,
        email=profile.get('emailAddress'),
        version='V2',
    )


def get_token_pair_from_reponse(response):
    return dict(
        access_token=response.get('access_token', None),
        secret=None
    )
