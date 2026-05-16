from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from content.models import AboutCompany, Banner, News, NewsImage


class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = ('id', 'title', 'description', 'image')


class AboutCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = AboutCompany
        fields = (
            'description',
            'years_stable',
            'satisfied_clients',
            'parts_in_stock',
            'world_brands',
        )


class NewsListSerializer(serializers.ModelSerializer):
    preview_image = serializers.SerializerMethodField()
    news_type_label = serializers.CharField(source='get_news_type_display', read_only=True)

    class Meta:
        model = News
        fields = (
            'id',
            'title',
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


class NewsDetailSerializer(serializers.ModelSerializer):
    images = NewsImageSerializer(many=True, read_only=True)
    news_type_label = serializers.CharField(source='get_news_type_display', read_only=True)

    class Meta:
        model = News
        fields = (
            'id',
            'title',
            'news_type',
            'news_type_label',
            'description',
            'published_at',
            'images',
        )
