from django.contrib import admin

from leads.models import Contact, ContactPhone, FeedbackMessage


class PhoneInline(admin.TabularInline):
    model = ContactPhone
    extra = 0
    fields = ('phone', 'telegram', 'max_link', 'label', 'ordering')


@admin.register(FeedbackMessage)
class FeedbackMessageAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'phone', 'created_at')
    readonly_fields = ('created_at',)


@admin.register(Contact)
class SiteContactAdmin(admin.ModelAdmin):
    """Вкладки Jazzmin: основная информация + inline «Телефоны»."""

    inlines = (PhoneInline,)
    readonly_fields = ('updated_at',)
    fieldsets = (
        (
            'Основная информация',
            {
                'fields': ('address', 'email_spare_parts', 'email_tires', 'updated_at'),
                'description': 'Адрес и электронная почта по направлениям (как на странице «Контакты»).',
            },
        ),
    )
    # Порядок вкладок в horizontal_tabs (имена совпадают с fieldset и verbose_name_plural inline)
    jazzmin_section_order = ('Основная информация', 'Телефоны')

    def has_add_permission(self, request):  # type: ignore[override]
        return not Contact.objects.exists()
