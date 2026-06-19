from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commerce', '0007_engines_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='price_on_request',
            field=models.BooleanField(
                db_index=True,
                default=False,
                help_text='Если включено — на сайте показывается «Цена по запросу», а не сумма.',
                verbose_name='Цена по запросу',
            ),
        ),
    ]
