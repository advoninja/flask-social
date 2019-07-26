# -*- coding: utf-8 -*-
"""
    flask.ext.social.views
    ~~~~~~~~~~~~~~~~~~~~~~

    This module contains the Flask-Social views

    :copyright: (c) 2012 by Matt Wright.
    :license: MIT, see LICENSE for more details.
"""
from importlib import import_module

from flask import (Blueprint, current_app, redirect, request, session,
                   after_this_request, abort, url_for)
from flask.ext.security import current_user, login_required
from flask.ext.security.utils import (get_post_login_redirect, login_user,
                                      logout_user, get_url, do_flash)
from flask.ext.security.decorators import anonymous_user_required
from werkzeug.local import LocalProxy

from .signals import (connection_removed, connection_created,
                      connection_failed, login_completed, login_failed)
from .utils import (config_value, get_provider_or_404, get_authorize_callback,
                    get_connection_values_from_oauth_response,
                    get_token_pair_from_oauth_response)


# Convenient references
_security = LocalProxy(lambda: current_app.extensions['security'])

_social = LocalProxy(lambda: current_app.extensions['social'])

_datastore = LocalProxy(lambda: _social.datastore)

_logger = LocalProxy(lambda: current_app.logger)


def _commit(response=None):
    _datastore.commit()
    return response


@anonymous_user_required
def login(provider_id):
    """Starts the provider login OAuth flow"""
    print "Enter @anonymous_user_required login "
    provider = get_provider_or_404(provider_id)
    callback_url = get_authorize_callback('login', provider_id)
    post_login = request.form.get('next', get_post_login_redirect())
    session[config_value('POST_OAUTH_LOGIN_SESSION_KEY')] = post_login
    return provider.authorize(callback_url)


@login_required
def connect(provider_id):
    """Starts the provider connection OAuth flow"""
    print "Enter @login_required connect "
    provider = get_provider_or_404(provider_id)
    print "provider in connect {}".format(provider)
    callback_url = get_authorize_callback('connect', provider_id)
    print "callback_url in connect {}".format(callback_url)
    allow_view = get_url(config_value('CONNECT_ALLOW_VIEW'))
    print "allow_view in connect {}".format(allow_view)
    pc = request.form.get('next', allow_view)
    print "pc in connect {}".format(pc)
    session[config_value('POST_OAUTH_CONNECT_SESSION_KEY')] = pc
    print "session in connect {}".format(session)
    return provider.authorize(callback_url)


@login_required
def reconnect(provider_id):
    """Tokens automatically refresh with login.
    Logs user out and starts provider login OAuth flow
    """
    logout_user()
    return login(provider_id)

@login_required
def remove_all_connections(provider_id):
    """Remove all connections for the authenticated user to the
    specified provider
    """
    provider = get_provider_or_404(provider_id)

    ctx = dict(provider=provider.name, user=current_user)

    deleted = _datastore.delete_connections(user_id=current_user.get_id(),
                                            provider_id=provider_id)
    if deleted:
        after_this_request(_commit)
        msg = ('All connections to %s removed' % provider.name, 'info')
        connection_removed.send(current_app._get_current_object(),
                                user=current_user._get_current_object(),
                                provider_id=provider_id)
    else:
        msg = ('Unable to remove connection to %(provider)s' % ctx, 'error')

    do_flash(*msg)
    return redirect(request.referrer)


@login_required
def remove_connection(provider_id, provider_user_id):
    """Remove a specific connection for the authenticated user to the
    specified provider
    """
    provider = get_provider_or_404(provider_id)

    ctx = dict(provider=provider.name, user=current_user,
               provider_user_id=provider_user_id)

    deleted = _datastore.delete_connection(user_id=current_user.get_id(),
                                           provider_id=provider_id,
                                           provider_user_id=provider_user_id)

    if deleted:
        after_this_request(_commit)
        msg = ('Connection to %(provider)s removed' % ctx, 'info')
        connection_removed.send(current_app._get_current_object(),
                                user=current_user._get_current_object(),
                                provider_id=provider_id)
    else:
        msg = ('Unabled to remove connection to %(provider)s' % ctx, 'error')

    do_flash(*msg)
    return redirect(request.referrer or get_post_login_redirect())


def connect_handler(cv, provider):
    """Shared method to handle the connection process

    :param connection_values: A dictionary containing the connection values
    :param provider_id: The provider ID the connection shoudl be made to
    """
    print "Enter connect_handler"
    cv.setdefault('user_id', current_user.get_id())
    connection = _datastore.find_connection(
        provider_id=cv['provider_id'], provider_user_id=cv['provider_user_id'])

    if connection is None:
        after_this_request(_commit)
        connection = _datastore.create_connection(**cv)
        msg = ('Connection established to %s' % provider.name, 'success')
        connection_created.send(current_app._get_current_object(),
                                user=current_user._get_current_object(),
                                connection=connection)
    else:
        msg = ('A connection is already established with %s '
               'to your account' % provider.name, 'notice')
        connection_failed.send(current_app._get_current_object(),
                               user=current_user._get_current_object())

    redirect_url = session.pop(config_value('POST_OAUTH_CONNECT_SESSION_KEY'),
                               get_url(config_value('CONNECT_ALLOW_VIEW')))

    do_flash(*msg)
    response = redirect(redirect_url)
    response.set_cookie('custom_message', msg[0])
    return response
    # return redirect(redirect_url) 


def connect_callback(provider_id):
    print "Enter connect_callback"
    print "session {}".format(session)
    print "provider_id"
    print provider_id
    provider = get_provider_or_404(provider_id)
    print "provider"
    print provider


    def connect(response):
        print "connect_callback inner response"
        print response
        cv = get_connection_values_from_oauth_response(provider, response)
        print "connect cv"
        print cv
        return cv

    cv = provider.authorized_handler(connect)()
    print "connect_callback authorized_handler"
    print cv

    if cv is None:
        msg = ('Marketbeam was not able to add this %s account.  Please try again' % provider.name, 'error')
        do_flash(*msg)
        response = redirect(get_url(config_value('CONNECT_DENY_VIEW')))
        response.set_cookie('custom_message', msg[0])
        return response
        # return redirect(get_url(config_value('CONNECT_DENY_VIEW')))

    return connect_handler(cv, provider)


@anonymous_user_required
def login_handler(response, provider, query):
    """Shared method to handle the signin process"""
    print "Enter @anonymous_user_required login_handler"

    connection = _datastore.find_connection(**query)

    if connection:
        after_this_request(_commit)
        token_pair = get_token_pair_from_oauth_response(provider, response)
        if (token_pair['access_token'] != connection.access_token or
            token_pair['secret'] != connection.secret):
            connection.access_token = token_pair['access_token']
            connection.secret = token_pair['secret']
            _datastore.put(connection)
        user = connection.user
        login_user(user)
        key = _social.post_oauth_login_session_key
        redirect_url = session.pop(key, get_post_login_redirect())

        login_completed.send(current_app._get_current_object(),
                             provider=provider, user=user)

        return redirect(redirect_url)

    login_failed.send(current_app._get_current_object(),
                      provider=provider,
                      oauth_response=response)

    next = get_url(_security.login_manager.login_view)
    msg = '%s account not associated with an existing user' % provider.name
    do_flash(msg, 'error')
    return redirect(next)


def login_callback(provider_id):
    print "Enter login_callback"
    try:
        provider = _social.providers[provider_id]
        module = import_module(provider.module)
    except KeyError:
        abort(404)

    def login(response):
        print "Enter login inner"
        _logger.debug('Received login response from '
                      '%s: %s' % (provider.name, response))

        if response is None:
            do_flash('Access was denied to your %s '
                     'account' % provider.name, 'error')
            return _security.login_manager.unauthorized(), None

        query = dict(provider_user_id=module.get_provider_user_id(response),
                     provider_id=provider_id)

        return response, query

    response, query = provider.authorized_handler(login)()
    if query is None:
        return response
    return login_handler(response, provider, query)


def create_blueprint(state, import_name):
    print "Enter create_blueprint"
    bp = Blueprint(state.blueprint_name, import_name,
                   url_prefix=state.url_prefix,
                   template_folder='templates')

    bp.route('/login/<provider_id>')(login_callback)

    bp.route('/login/<provider_id>',
             methods=['POST'])(login)

    bp.route('/connect/<provider_id>')(connect_callback)

    bp.route('/connect/<provider_id>',
             methods=['POST'])(connect)

    bp.route('/connect/<provider_id>',
             methods=['DELETE'])(remove_all_connections)

    bp.route('/connect/<provider_id>/<provider_user_id>',
             methods=['DELETE'])(remove_connection)

    bp.route('/reconnect/<provider_id>',
             methods=['POST'])(reconnect)

    return bp
