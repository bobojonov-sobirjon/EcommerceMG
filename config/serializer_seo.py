"""Сериализаторы: SEO-поля из связанной модели seo_record."""

from django.core.exceptions import ObjectDoesNotExist
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers


def _seo_record(obj):
    try:
        return obj.seo_record
    except ObjectDoesNotExist:
        return None


class SlugFromSeoRecordSerializer(serializers.Serializer):
    slug = serializers.SerializerMethodField(read_only=True)

    @extend_schema_field(serializers.CharField(allow_blank=True))
    def get_slug(self, obj):
        record = _seo_record(obj)
        return record.slug if record else ''


class SeoRecordSerializer(serializers.Serializer):
    slug = serializers.SerializerMethodField(read_only=True)
    seo_title = serializers.SerializerMethodField(read_only=True)
    seo_description = serializers.SerializerMethodField(read_only=True)

    @extend_schema_field(serializers.CharField(allow_blank=True))
    def get_slug(self, obj):
        record = _seo_record(obj)
        return record.slug if record else ''

    @extend_schema_field(serializers.CharField(allow_blank=True))
    def get_seo_title(self, obj):
        record = _seo_record(obj)
        return record.seo_title if record else ''

    @extend_schema_field(serializers.CharField(allow_blank=True))
    def get_seo_description(self, obj):
        record = _seo_record(obj)
        return record.seo_description if record else ''


class PageSeoRecordSerializer(serializers.Serializer):
    seo_title = serializers.SerializerMethodField(read_only=True)
    seo_description = serializers.SerializerMethodField(read_only=True)

    @extend_schema_field(serializers.CharField(allow_blank=True))
    def get_seo_title(self, obj):
        record = _seo_record(obj)
        return record.seo_title if record else ''

    @extend_schema_field(serializers.CharField(allow_blank=True))
    def get_seo_description(self, obj):
        record = _seo_record(obj)
        return record.seo_description if record else ''


# Обратная совместимость импортов
SlugFromSeoRecordMixin = SlugFromSeoRecordSerializer
SeoRecordSerializerMixin = SeoRecordSerializer
