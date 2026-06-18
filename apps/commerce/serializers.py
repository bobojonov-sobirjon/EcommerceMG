from decimal import Decimal

from drf_spectacular.utils import extend_schema_field
from django.db import transaction
from rest_framework import serializers

from commerce.models import (
    Manufacturer,
    Order,
    OrderProduct,
    Product,
    ProductImage,
)
from config.serializer_seo import SeoRecordSerializer, SlugFromSeoRecordSerializer


class ManufacturerListSerializer(SlugFromSeoRecordSerializer, serializers.ModelSerializer):
    class Meta:
        model = Manufacturer
        fields = ('id', 'name', 'slug', 'logo', 'ordering')


class ManufacturerDetailSerializer(SeoRecordSerializer, serializers.ModelSerializer):
    class Meta:
        model = Manufacturer
        fields = (
            'id',
            'name',
            'slug',
            'description',
            'seo_title',
            'seo_description',
            'logo',
            'hero_image',
            'ordering',
        )


class ProductManufacturerMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Manufacturer
        fields = ('id', 'name')


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ('id', 'image', 'ordering')


class ProductListSerializer(SlugFromSeoRecordSerializer, serializers.ModelSerializer):
    manufacturer = ProductManufacturerMiniSerializer(read_only=True)
    thumbnail = serializers.SerializerMethodField()
    product_type_label = serializers.CharField(source='get_product_type_display', read_only=True)

    class Meta:
        model = Product
        fields = (
            'id',
            'product_type',
            'product_type_label',
            'name',
            'slug',
            'artikul',
            'price',
            'is_stock',
            'manufacturer',
            'thumbnail',
        )

    @extend_schema_field(serializers.CharField(allow_null=True, required=False))
    def get_thumbnail(self, obj: Product):
        first = None
        cache = getattr(obj, '_prefetched_objects_cache', None)
        if cache and 'images' in cache:
            imgs = sorted(obj.images.all(), key=lambda i: (i.ordering, i.pk))
            first = imgs[0] if imgs else None
        else:
            first = obj.images.order_by('ordering', 'pk').first()
        if first and first.image:
            request = self.context.get('request')
            url = first.image.url
            if request:
                return request.build_absolute_uri(url)
            return url
        return None


class ProductDetailSerializer(SeoRecordSerializer, serializers.ModelSerializer):
    manufacturer = ProductManufacturerMiniSerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    product_type_label = serializers.CharField(source='get_product_type_display', read_only=True)

    class Meta:
        model = Product
        fields = (
            'id',
            'product_type',
            'product_type_label',
            'manufacturer',
            'name',
            'slug',
            'artikul',
            'description',
            'seo_title',
            'seo_description',
            'price',
            'is_stock',
            'images',
        )


class OrderItemWriteSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1)
    total_price = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal('0'))


class OrderCreateSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=255)
    phone = serializers.CharField(max_length=32)
    total_price = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal('0'))
    items = OrderItemWriteSerializer(many=True, allow_empty=False)

    def create(self, validated_data):
        items = validated_data.pop('items')
        client_total: Decimal = validated_data['total_price']

        computed = Decimal('0')
        with transaction.atomic():
            product_ids = [it['product_id'] for it in items]
            if len(product_ids) != len(set(product_ids)):
                raise serializers.ValidationError(
                    {'items': 'Списки товаров содержит дубликаты product_id'},
                )

            products_map = {
                p.pk: p for p in Product.objects.select_for_update().filter(pk__in=product_ids)
            }
            lines: list[tuple] = []
            for row in items:
                pid = row['product_id']
                if pid not in products_map:
                    raise serializers.ValidationError({'items': f'Товар id={pid} не найден'})
                product = products_map[pid]
                line_total: Decimal = row['total_price']
                qty = row['quantity']
                expected = (product.price * qty).quantize(Decimal('0.01'))
                tolerance = Decimal('0.05') * qty + Decimal('1')
                if abs(line_total - expected) > tolerance:
                    raise serializers.ValidationError(
                        {'items': f'Сумма строки для {pid} не сходится с ценой каталога'},
                    )
                computed += line_total
                lines.append((product, qty, line_total))

            if abs(computed - client_total).quantize(Decimal('0.01')) > Decimal('1'):
                raise serializers.ValidationError(
                    {'total_price': 'Итого не совпадает с суммой строк'},
                )

            order = Order.objects.create(
                full_name=validated_data['full_name'],
                phone=validated_data['phone'],
                total_price=computed,
                is_seen_moderator=True,
            )
            ops = [
                OrderProduct(order=order, product=p, quantity=q, total_price=l)
                for (p, q, l) in lines
            ]
            OrderProduct.objects.bulk_create(ops)
            return order


class OrderCreatedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ('id', 'full_name', 'phone', 'total_price', 'created_at', 'is_seen_moderator')
