__author__ = 'rohe0002'

import json

from urlparse import urlparse

from mechanize import ParseResponse
#from httplib2 import Response

class FlowException(Exception):
    def __init__(self, function="", content="", url=""):
        Exception.__init__(self)
        self.function = function
        self.content = content
        self.url = url

    def __str__(self):
        return json.dumps(self.__dict__)


class DResponse():
    def __init__(self, **kwargs):
        self.status = 200
        self.index = 0
        self._message = ""
        self.url = ""
        if kwargs:
            for key, val in kwargs.items():
                self.__setitem__(key, val)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, item):
        if item == "content-location":
            return self.url
        elif item == "content-length":
            return len(self._message)
        else:
            return getattr(self, item)

    def geturl(self):
        return self.url

    def read(self, size=0):
        if size:
            if self._len < size:
                return self._message
            else:
                if self._len == self.index:
                    part = None
                elif self._len - self.index < size:
                    part = self._message[self.index:]
                    self.index = self._len
                else:
                    part = self._message[self.index:self.index+size]
                    self.index += size
                return part
        else:
            return self._message

    def write(self, message):
        self._message = message
        self._len = len(message)


def do_request(client, url, method, body="", headers=None, trace=False):
    if headers is None:
        headers = {}

    if trace:
        trace.request("URL: %s" % url)
        trace.request("BODY: %s" % body)

    response, content = client.http_request(url, method=method,
                                            body=body, headers=headers,
                                            trace=trace)

    if trace:
        trace.reply("RESPONSE: %s" % response)
        trace.reply("CONTENT: %s" % unicode(content, encoding="utf-8"))

    return response, content

#noinspection PyUnusedLocal
def login_form(client, orig_response, content, **kwargs):
    _url = orig_response["content-location"]
    # content is a form to be filled in and returned
    response = DResponse(status=orig_response["status"], url=_url)
    response.write(content)

    forms = ParseResponse(response)
    try:
        form = forms[0]
    except IndexError: # Wasn't able to parse
        raise FlowException(content=content, url=_url)

    try:
        form[kwargs["user_label"]] = kwargs["user"]
    except KeyError:
        pass

    try:
        form[kwargs["password_label"]] = kwargs["password"]
    except KeyError:
        pass

    request = form.click()

    headers = {}
    for key, val in request.unredirected_hdrs.items():
        headers[key] = val

    url = request._Request__original
    try:
        _trace = kwargs["trace"]
    except KeyError:
        _trace = False

    return do_request(client, url, "POST", request.data, headers, _trace)

#noinspection PyUnusedLocal
def approve_form(client, orig_response, content, **kwargs):
    # content is a form to be filled in and returned
    response = DResponse(status=orig_response["status"],
    )
    if orig_response["status"] == 302:
        response.url = orig_response["content-location"]
    else:
        response.url = client.authorization_endpoint
    response.write(content)

    forms = ParseResponse(response)
    try:
        form = forms[0]
    except IndexError:
        raise FlowException(content=content, url=response.url)

    # do something with args

    request = form.click()

    headers = {}
    for key, val in request.unredirected_hdrs.items():
        headers[key] = val

    try:
        _trace = kwargs["trace"]
    except KeyError:
        _trace = False

    url = request._Request__original
    return do_request(client, url, "POST", request.data, headers, _trace)
#    resp.url = request._Request__original
#    return resp, request.data

#noinspection PyUnusedLocal
def chose(client, orig_response, content, **kwargs):
    _loc = orig_response["content-location"]
    part = urlparse(_loc)
    #resp = Response({"status":"302"})

    try:
        _trace = kwargs["trace"]
    except KeyError:
        _trace = False

    url = "%s://%s%s" %  (part[0], part[1], kwargs["path"])
    return do_request(client, url, "GET", trace=_trace)
    #return resp, ""

# ========================================================================

#FORM_LOGIN = {
#    "function": login_form,
#    "args": {
#        "user_label": "login",
#        "password_label": "password",
#        "user": "username",
#        "password": "hemligt"
#        }
#}

FORM_LOGIN = {
    "id": "login_form",
    "function": login_form,
    }

APPROVE_FORM = {
    "id": "approve_form",
    "function": approve_form,
    }


CHOSE = {
    "id": "chose",
    "function": chose,
    "args": { "path": "/account/fake"}
}

# ========================================================================

RESPOND = {
    "method": "POST",
    }

AUTHZREQ_CODE = {
    "request": "AuthorizationRequest",
    "method": "GET",
    "args": {
        "request": {"response_type": "code"},
        }
}

AUTHZRESP = {
    "response": "AuthorizationResponse",
    "where": "url",
    "type": "urlencoded",
    }

ACCESS_TOKEN_RESPONSE = {
    "response": "AccessTokenResponse",
    "where": "body",
    "type": "json"
}

USER_INFO_RESPONSE = {
    "response": "OpenIDSchema",
    "where": "body",
    "type": "json"
}

ACCESS_TOKEN_REQUEST_PASSWD = {
    "request":"AccessTokenRequest",
    "method": "POST",
    "args": {
        "kw": {"authn_method": "client_secret_basic"}
    },
    }

ACCESS_TOKEN_REQUEST_CLI_SECRET_POST = {
    "request":"AccessTokenRequest",
    "method": "POST",
    "args": {
        "kw": {"authn_method": "client_secret_post"}
    },
    }

ACCESS_TOKEN_REQUEST_CLI_SECRET_GET = {
    "request":"AccessTokenRequest",
    "method": "GET",
    "args": {
        "kw": {"authn_method": "client_secret_post"}
    },
    }

ACCESS_TOKEN_REQUEST_FACEBOOK = {
    "request":("facebook","AccessTokenRequest"),
    "method": "GET",
    "args": {
        "kw": {"authn_method": "client_secret_post"}
    },
    }

ACCESS_TOKEN_RESPONSE_FACEBOOK = {
    "response": ("facebook", "AccessTokenResponse"),
    "where": "body",
    "type": "urlencoded"
}

PHASES= {
    "login": ([AUTHZREQ_CODE], AUTHZRESP),
    "login-form": ([AUTHZREQ_CODE, FORM_LOGIN], AUTHZRESP),
    "login-form-approve": ([AUTHZREQ_CODE, FORM_LOGIN, APPROVE_FORM],
                           AUTHZRESP),
    "access-token-request-post":([ACCESS_TOKEN_REQUEST_CLI_SECRET_POST],
                                 ACCESS_TOKEN_RESPONSE),
    "access-token-request-get":([ACCESS_TOKEN_REQUEST_CLI_SECRET_GET],
                                ACCESS_TOKEN_RESPONSE),
    "facebook-access-token-request-get":([ACCESS_TOKEN_REQUEST_FACEBOOK],
                                         ACCESS_TOKEN_RESPONSE_FACEBOOK),
}


FLOWS = {
    'basic-code-authn': {
        "name": 'Basic Code flow with authentication',
        "descr": ('Very basic test of a Provider using the authorization code ',
                  'flow. The test tool acting as a consumer is very relaxed',
                  'and tries to obtain an ID Token.'),
        "sequence": ["login-form"],
        "endpoints": ["authorization_endpoint"]
    },
    'basic-code-idtoken-post': {
        "name": 'Basic Code flow with ID Token',
        "descr": ('Very basic test of a Provider using the authorization code ',
                  'flow. The test tool acting as a consumer is very relaxed',
                  'and tries to obtain an ID Token.'),
        "depends": ["basic-code-authn"],
        "sequence": ["login-form", "access-token-request-post"],
        "endpoints": ["authorization_endpoint", "token_endpoint"]
    },
    'basic-code-idtoken-get': {
        "name": 'Basic Code flow with ID Token',
        "descr": ('Very basic test of a Provider using the authorization code ',
                  'flow. The test tool acting as a consumer is very relaxed',
                  'and tries to obtain an ID Token.'),
        "depends": ["basic-code-authn"],
        "sequence": ["login-form", "access-token-request-get"],
        "endpoints": ["authorization_endpoint", "token_endpoint"]
    },
    'facebook-idtoken-get': {
        "name": 'Facebook flow with ID Token',
        "descr": ('Facebook specific flow'),
        "depends": ["basic-code-authn"],
        "sequence": ["login-form", "facebook-access-token-request-get"],
        "endpoints": ["authorization_endpoint", "token_endpoint"]
    },
}