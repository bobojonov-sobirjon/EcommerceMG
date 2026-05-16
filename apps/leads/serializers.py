from rest_framework import serializers

from leads.models import Contact, ContactPhone, FeedbackMessage


class FeedbackMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedbackMessage
        fields = ('full_name', 'email', 'phone')


class ContactPhoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactPhone
        fields = ('id', 'phone', 'telegram', 'max_link', 'label', 'ordering')


class SiteContactSerializer(serializers.ModelSerializer):
    phones = ContactPhoneSerializer(many=True, read_only=True)

    class Meta:
        model = Contact
        fields = ('address', 'email_spare_parts', 'email_tires', 'phones')
