"""SEO inline для админки (Django TabularInline, без кастомных шаблонов)."""

from django import forms
from django.contrib import admin
from django.core.exceptions import ObjectDoesNotExist
from django.db import models


class SeoTabularInline(admin.TabularInline):
    extra = 0
    max_num = 1
    min_num = 0
    can_delete = False
    classes = ('seo-inline',)
    fields = ('seo_title', 'seo_description', 'slug')
    verbose_name_plural = 'SEO'
    formfield_overrides = {
        models.TextField: {
            'widget': forms.Textarea(attrs={'rows': 3, 'cols': 40}),
        },
    }

    def _has_seo_record(self, obj) -> bool:
        if not obj or not obj.pk:
            return False
        try:
            obj.seo_record
            return True
        except ObjectDoesNotExist:
            return False

    def get_min_num(self, request, obj=None, **kwargs):
        return 0 if self._has_seo_record(obj) else 1

    def get_extra(self, request, obj=None, **kwargs):
        return 0 if self._has_seo_record(obj) else 1


class PageSeoTabularInline(admin.TabularInline):
    extra = 0
    max_num = 1
    min_num = 0
    can_delete = False
    classes = ('seo-inline',)
    fields = ('seo_title', 'seo_description')
    verbose_name_plural = 'SEO'
    formfield_overrides = {
        models.TextField: {
            'widget': forms.Textarea(attrs={'rows': 3, 'cols': 40}),
        },
    }

    def _has_seo_record(self, obj) -> bool:
        if not obj or not obj.pk:
            return False
        try:
            obj.seo_record
            return True
        except ObjectDoesNotExist:
            return False

    def get_min_num(self, request, obj=None, **kwargs):
        return 0 if self._has_seo_record(obj) else 1

    def get_extra(self, request, obj=None, **kwargs):
        return 0 if self._has_seo_record(obj) else 1
