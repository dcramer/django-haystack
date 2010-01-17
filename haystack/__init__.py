import inspect
import logging
import os
import sys
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from haystack.sites import autodiscover, site


__author__ = 'Daniel Lindsley'
__version__ = (1, 1, 0, 'alpha')
__all__ = ['backend']


# Setup default logging.
log = logging.getLogger('haystack')
stream = logging.StreamHandler()
stream.setLevel(logging.INFO)
log.addHandler(stream)


if not hasattr(settings, "HAYSTACK_SITECONF"):
    raise ImproperlyConfigured("You must define the HAYSTACK_SITECONF setting before using the search framework.")
if not hasattr(settings, "HAYSTACK_SEARCH_ENGINE"):
    raise ImproperlyConfigured("You must define the HAYSTACK_SEARCH_ENGINE setting before using the search framework.")


# Load the search backend.
def load_backend(backend_name=None):
    if not backend_name:
        backend_name = settings.HAYSTACK_SEARCH_ENGINE
    
    try:
        # Most of the time, the search backend will be one of the  
        # backends that ships with haystack, so look there first.
        return __import__('haystack.backends.%s_backend' % backend_name, {}, {}, [''])
    except ImportError, e:
        # If the import failed, we might be looking for a search backend 
        # distributed external to haystack. So we'll try that next.
        try:
            return __import__('%s_backend' % backend_name, {}, {}, [''])
        except ImportError, e_user:
            # The search backend wasn't found. Display a helpful error message
            # listing all possible (built-in) database backends.
            backend_dir = os.path.join(__path__[0], 'backends')
            available_backends = [
                os.path.splitext(f)[0].split("_backend")[0] for f in os.listdir(backend_dir)
                if f != "base.py"
                and not f.startswith('_') 
                and not f.startswith('.') 
                and not f.endswith('.pyc')
            ]
            available_backends.sort()
            if backend_name not in available_backends:
                raise ImproperlyConfigured, "%r isn't an available search backend. Available options are: %s" % \
                    (backend_name, ", ".join(map(repr, available_backends)))
            else:
                raise # If there's some other error, this must be an error in Django itself.


backend = load_backend(settings.HAYSTACK_SEARCH_ENGINE)


def handle_registrations(*args, **kwargs):
    """
    Ensures that any configuration of the SearchSite(s) are handled when
    importing Haystack.
    
    This makes it possible for scripts/management commands that affect models
    but know nothing of Haystack to keep the index up to date.
    """
    print "In handle_registrations."
    if not getattr(settings, 'HAYSTACK_ENABLE_REGISTRATIONS', True):
        # If the user really wants to disable this, they can, possibly at their
        # own expense. This is generally only required in cases where other
        # apps generate import errors and requires extra work on the user's
        # part to make things work.
        return
    
    found_module = False
    modules = sys.modules.keys()
    siteconf_module = 'haystack.indexes' # settings.HAYSTACK_SITECONF
    
    for mod in modules:
        # Check if siteconf has been loaded.
        if siteconf_module in mod or settings.HAYSTACK_SITECONF in mod:
            found_module = True
            break
    
    if not found_module:
        print "Importing siteconf."
        # Pull in the config file, causing any SearchSite initialization code to
        # execute.
        search_sites_conf = __import__(settings.HAYSTACK_SITECONF)


handle_registrations()
