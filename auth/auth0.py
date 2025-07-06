# auth/auth0.py

from flask import redirect, url_for
from flask_oauthlib.client import OAuth

oauth = OAuth()

def setup_auth(app):
    auth0 = oauth.remote_app(
        'auth0',
        consumer_key='YOUR_CLIENT_ID',
        consumer_secret='YOUR_CLIENT_SECRET',
        request_token_params={
            'scope': 'openid',
        },
        base_url='https://YOUR_DOMAIN.auth0.com',
        request_token_url=None,
        access_token_method='POST',
        access_token_url='https://YOUR_DOMAIN.auth0.com/oauth/token',
        refresh_token_url=None,
    )

    @app.route('/login')
    def login():
        return auth0.authorize(callback=url_for('authorized', _external=True))

    @app.route('/logout')
    def logout():
        session.pop('auth_token')
        return redirect(url_for('index'))

    @app.route('/login/callback')
    def authorized():
        response = auth0.authorized_response()
        if response is None or response.get('access_token') is None:
            return 'Access denied: reason={} error={}'.format(
                request.args['error_reason'],
                request.args['error_description']
            )

        session['auth_token'] = response['access_token']
        return redirect(url_for('index'))
