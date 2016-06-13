from django.core.exceptions import ImproperlyConfigured

__all__ = [
    'FilterMxin',
]

class FilterMixin(object):
    """
    View mixin which provides filtering for ListView.
    """
    filter_url_kwarg = 'filter'
    default_filter_param = None
 
    def get_default_filter_param(self):
        if self.default_filter_param is None:
            raise ImproperlyConfigured(
                "'FilterMixin' requires the 'default_filter_param' attribute "
                "to be set.")
        return self.default_filter_param
 
    def filter_queryset(self, qs, filter_param):
        """
        Filter the queryset `qs`, given the selected `filter_param`. Default
        implementation does no filtering at all.
        """
        return qs
 
    def get_filter_param(self):
        return self.kwargs.get(self.filter_url_kwarg,
                               self.get_default_filter_param())
 
    def get_queryset(self):
        return self.filter_queryset(
            super(FilterMixin, self).get_queryset(),
            self.get_filter_param())
 
    def get_context_data(self, *args, **kwargs):
        context = super(FilterMixin, self).get_context_data(*args, **kwargs)
        context.update({
            'filter': self.get_filter_param(),
        })
        return context