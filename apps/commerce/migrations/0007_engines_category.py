# Generated manually for engines catalog

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('commerce', '0006_seo_inline_models'),
    ]

    operations = [
        migrations.AddField(
            model_name='manufacturer',
            name='features_heading',
            field=models.CharField(
                blank=True,
                help_text='Например: «Особенности двигателей Caterpillar». Только для страницы двигателей.',
                max_length=255,
                verbose_name='Заголовок блока преимуществ',
            ),
        ),
        migrations.AlterField(
            model_name='manufacturer',
            name='hero_image',
            field=models.ImageField(
                blank=True,
                help_text='Верхний баннер на странице двигателей этого производителя.',
                null=True,
                upload_to='manufacturers/hero/%Y/%m/',
                verbose_name='Баннер (страница двигателей)',
            ),
        ),
        migrations.AlterField(
            model_name='product',
            name='product_type',
            field=models.CharField(
                choices=[
                    ('spare_parts', 'Запчасти'),
                    ('tires', 'Шины для спецтехники'),
                    ('engines', 'Двигатели'),
                ],
                db_index=True,
                max_length=32,
                verbose_name='Тип товара',
            ),
        ),
        migrations.CreateModel(
            name='ManufacturerFeature',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='Заголовок')),
                ('description', models.TextField(blank=True, verbose_name='Описание')),
                ('icon', models.ImageField(blank=True, null=True, upload_to='manufacturers/features/%Y/%m/', verbose_name='Иконка')),
                ('ordering', models.PositiveSmallIntegerField(default=0, verbose_name='Порядок')),
                (
                    'manufacturer',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='features',
                        to='commerce.manufacturer',
                        verbose_name='Производитель',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Преимущество производителя',
                'verbose_name_plural': 'Преимущества производителя',
                'ordering': ('ordering', 'id'),
            },
        ),
    ]
