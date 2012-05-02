from django.shortcuts import render_to_response
from django.template import RequestContext
from zdev.settings import JS_DEBUG


def render(template):
    def renderer(func):
        def wrapper(request, *args, **kw):
            output = func(request, *args, **kw)
            if isinstance(output, (list, tuple)):
                return render_to_response(
                    output[1], output[0], RequestContext(request))
            elif isinstance(output, dict):
                return render_to_response(
                    '%s.html' % template, output, RequestContext(request))
            return output
        return wrapper
    return renderer


def my_context(request):
    return {'JS_DEBUG': str(JS_DEBUG).lower()}
