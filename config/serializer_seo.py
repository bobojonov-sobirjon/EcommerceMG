"""Сериализаторы: поля SEO из связанной inline-модели."""

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers


class SeoRecordSerializerMixin:
    """slug, seo_title, seo_description из related_name='seo_record'."""

    seo_record_attr = 'seo_record'

    slug = serializers.SerializerMethodField()
    seo_title = serializers.SerializerMethodField()
    seo_description = serializers.SerializerMethodField()

    @extend_schema_field(serializers.CharField(allow_blank=True))
    def get_slug(self, obj):
        record = getattr(obj, self.seo_record_attr, None)
        return record.slug if record else ''

    @extend_schema_field(serializers.CharField(allow_blank=True))
    def get_seo_title(self, obj):
        record = getattr(obj, self.seo_record_attr, None)
        return record.seo_title if record else ''

    @extend_schema_field(serializers.CharField(allow_blank=True))
    def get_seo_description(self, obj):
        record = getattr(obj, self.seo_record_attr, None)
        return record.seo_description if record else ''


class SlugFromSeoRecordMixin:
    seo_record_attr = 'seo_record'

    slug = serializers.SerializerMethodField()

    @extend_schema_field(serializers.CharField(allow_blank=True))
    def get_slug(self, obj):
        record = getattr(obj, self.seo_record_attr, None)
        return record.slug if record else ''
