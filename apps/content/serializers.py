from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from content.models import AboutCompany, Banner, Certification, News, NewsImage
from config.serializer_seo import SeoRecordSerializerMixin, SlugFromSeoRecordMixin


def _absolute_file_url(serializer, file_field) -> str | None:
    if not file_field or not file_field.name:
        return None
    request = serializer.context.get('request')
    url = file_field.url
    if request:
        return request.build_absolute_uri(url)
    return url


class BannerSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Banner
        fields = ('id', 'title', 'type', 'description', 'image')

    @extend_schema_field(serializers.CharField(allow_null=True, required=False))
    def get_image(self, obj: Banner):
        return _absolute_file_url(self, obj.image)


class CertificationSerializer(serializers.ModelSerializer):
    thumbnail_image = serializers.SerializerMethodField()
    pdf = serializers.SerializerMethodField()
    pdf_size_mb = serializers.SerializerMethodField()

    class Meta:
        model = Certification
        fields = ('id', 'name', 'thumbnail_image', 'pdf', 'pdf_size_mb', 'created_at')

    @extend_schema_field(serializers.CharField(allow_null=True, required=False))
    def get_thumbnail_image(self, obj: Certification):
        return _absolute_file_url(self, obj.thumbnail_image)

    @extend_schema_field(serializers.CharField(allow_null=True, required=False))
    def get_pdf(self, obj: Certification):
        return _absolute_file_url(self, obj.pdf)

    @extend_schema_field(serializers.FloatField(allow_null=True, required=False))
    def get_pdf_size_mb(self, obj: Certification):
        if not obj.pdf or not obj.pdf.name:
            return None
        try:
            size = obj.pdf.size
        except (OSError, ValueError):
            return None
        return round(size / (1024 * 1024), 3)


class AboutCompanySerializer(serializers.ModelSerializer):
    seo_title = serializers.SerializerMethodField()
    seo_description = serializers.SerializerMethodField()

    class Meta:
        model = AboutCompany
        fields = (
            'description',
            'seo_title',
            'seo_description',
            'years_stable',
            'satisfied_clients',
            'parts_in_stock',
            'world_brands',
        )

    @extend_schema_field(serializers.CharField(allow_blank=True))
    def get_seo_title(self, obj: AboutCompany):
        record = getattr(obj, 'seo_record', None)
        return record.seo_title if record else ''

    @extend_schema_field(serializers.CharField(allow_blank=True))
    def get_seo_description(self, obj: AboutCompany):
        record = getattr(obj, 'seo_record', None)
        return record.seo_description if record else ''


class NewsListSerializer(SlugFromSeoRecordMixin, serializers.ModelSerializer):
    preview_image = serializers.SerializerMethodField()
    news_type_label = serializers.CharField(source='get_news_type_display', read_only=True)

    class Meta:
        model = News
        fields = (
            'id',
            'title',
            'slug',
            'news_type',
            'news_type_label',
            'published_at',
            'preview_image',
        )

    @extend_schema_field(serializers.CharField(allow_null=True, required=False))
    def get_preview_image(self, obj: News):
        first = None
        if hasattr(obj, '_prefetched_objects_cache') and 'images' in obj._prefetched_objects_cache:
            imgs = sorted(obj.images.all(), key=lambda i: (i.ordering, i.pk))
            first = imgs[0] if imgs else None
        else:
            first = obj.images.order_by('ordering', 'id').first()
        if not first or not first.image:
            return None
        request = self.context.get('request')
        url = first.image.url
        if request:
            return request.build_absolute_uri(url)
        return url


class NewsImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsImage
        fields = ('id', 'image', 'ordering')


class NewsDetailSerializer(SeoRecordSerializerMixin, serializers.ModelSerializer):
    images = NewsImageSerializer(many=True, read_only=True)
    news_type_label = serializers.CharField(source='get_news_type_display', read_only=True)

    class Meta:
        model = News
        fields = (
            'id',
            'title',
            'slug',
            'news_type',
            'news_type_label',
            'description',
            'seo_title',
            'seo_description',
            'published_at',
            'images',
        )
