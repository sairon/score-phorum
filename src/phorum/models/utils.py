import os

from django.conf import settings

from ..utils import get_custom_resource_filename


def make_resource_upload_path(resource_type, instance, filename):
    """Get upload path for a resource type and for given instance."""
    return os.path.join("user_customization", get_custom_resource_filename(instance.user.id, resource_type))


def css_upload_path(*args, **kwargs):
    return make_resource_upload_path("css", *args, **kwargs)


def js_upload_path(*args, **kwargs):
    return make_resource_upload_path("js", *args, **kwargs)
