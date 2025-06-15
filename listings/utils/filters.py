from django.contrib.admin import SimpleListFilter
from django.utils.translation import gettext_lazy as _
from django.contrib.admin.filters import FieldListFilter
from django.utils.html import format_html
from django.utils.http import urlencode
from django import forms


class ActiveListingsFilter(SimpleListFilter):
    title = 'active status'
    parameter_name = 'is_active'
    
    def lookups(self, request, model_admin):
        return (
            ('active', 'Active'),
            ('inactive', 'Inactive'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'active':
            return queryset.filter(is_active=True)
        if self.value() == 'inactive':
            return queryset.filter(is_active=False)



class NumericRangeFilter(FieldListFilter):
    template = 'admin/filter.html'  # Not used unless you override the template

    def __init__(self, field, request, params, model, model_admin, field_path):
        self.field_path = field_path
        self.lookup_kwarg_min = f'{field_path}__gte'
        self.lookup_kwarg_max = f'{field_path}__lte'
        self.val_min = params.get(self.lookup_kwarg_min)
        self.val_max = params.get(self.lookup_kwarg_max)
        super().__init__(field, request, params, model, model_admin, field_path)

    def expected_parameters(self):
        return [self.lookup_kwarg_min, self.lookup_kwarg_max]

    def queryset(self, request, queryset):
        if self.val_min:
            queryset = queryset.filter(**{self.lookup_kwarg_min: self.val_min})
        if self.val_max:
            queryset = queryset.filter(**{self.lookup_kwarg_max: self.val_max})
        return queryset

    def has_output(self):
        return True

    def choices(self, changelist):
        return []

    def render(self, request):
        return format_html(
            '<div style="margin-bottom:1em">'
            'Min: <input type="number" name="{}" value="{}" style="width: 80px;" /> '
            'Max: <input type="number" name="{}" value="{}" style="width: 80px;" />'
            '</div>',
            self.lookup_kwarg_min, self.val_min or '',
            self.lookup_kwarg_max, self.val_max or ''
        )