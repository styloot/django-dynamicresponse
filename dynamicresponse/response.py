from django.forms import Form, ModelForm
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from dynamicresponse.json_response import JsonResponse

CR_OK = ('OK', 200)
CR_INVALID_DATA = ('INVALID', 400)
CR_NOT_FOUND = ('NOT_FOUND', 404)
CR_CONFIRM = ('CONFIRM', 405)
CR_DELETED = ('DELETED', 204)
CR_REQUIRES_UPGRADE = ('REQUIRES_UPGRADE', 402)

class DynamicResponse(object):
    """
    Base class for dynamic responses.
    """

    def __init__(self, context={}, status=None, **kwargs):

        self.context = context
        if status is None: #Status argument can override context
            self.status = context.get('status', CR_OK)
        else:
            self.status = status
        for arg in kwargs:
            setattr(self, arg, kwargs[arg])

    def serialize(self):
        """
        Serializes the context as JSON, or returns a HTTP response with corresponding status.
        """

        key, status_code = self.status
        if status_code == 200:
            return JsonResponse(self.context)
        else:
            return HttpResponse(status=status_code)

    def full_context(self):
        """
        Returns context and extra context combined into a single dictionary.
        """

        full_context = {}
        full_context.update(self.context)
        if hasattr(self, 'extra'):
            full_context.update(self.extra)
        return full_context

class SerializeOrRender(DynamicResponse):
    """
    For normal requests, the specified template is rendered.
    For API requests, the context is serialized and returned as JSON.
    """

    def __init__(self, template, context={}, **kwargs):

        super(SerializeOrRender, self).__init__(context, **kwargs)
        self.template = template

    def render_response(self, request):
        if request.is_api:
            res = self.serialize()
        else:
            res = render_to_response(self.template, self.full_context(), RequestContext(request))

        if hasattr(self, 'extra_headers'):
            for header in self.extra_headers:
                res[header] = self.extra_headers[header]

        return res

def serialize_or_render(request, template, context={}, **kwargs):
    return SerializeOrRender(template, context, **kwargs).render_response(request)

class SerializeOrRedirect(DynamicResponse):
    """
    For normal requests, the user is redirected to the specified location.
    For API requests, the context is serialized and returned as JSON.
    """

    def __init__(self, url, context={}, **kwargs):

        super(SerializeOrRedirect, self).__init__(context, **kwargs)
        self.url = url

    def render_response(self, request):

        if request.is_api:
            res = self.serialize()
        else:
            res = HttpResponseRedirect(self.url)

        if hasattr(self, 'extra_headers'):
            for header in self.extra_headers:
                res[header] = self.extra_headers[header]

        return res

def serialize_or_redirect(request, url, context={}, **kwargs):
    return SerializeOrRedirect(url, context, **kwargs).render_response(request)

class Serialize(DynamicResponse):
    """
    Serializes the context as JSON for both API and normal requests.
    Useful for AJAX-only type views.
    """

    def __init__(self, context={}, **kwargs):

        super(Serialize, self).__init__(context, **kwargs)

    def render_response(self, request):

        res = self.serialize()

        if hasattr(self, 'extra_headers'):
            for header in self.extra_headers:
                res[header] = self.extra_headers[header]

        return res

def serialize(request, context={}, **kwargs):
    return Serialize(context, **kwargs).render_response(request)

class SerializeObject(Serialize):
    """
    Serializes a single object as JSON for both API and normal requests.
    """

    def __init__(self, context={}, status=CR_OK, **kwargs):
        super(Serialize, self).__init__(context, status=status, **kwargs)

def serialize_object(request, context={}, status=CR_OK, **kwargs):
    return SerializeObject(context, status, **kwargs).render_response(request)
