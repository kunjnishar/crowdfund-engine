from rest_framework import serializers

from campaigns.models import Campaign, Donation


class DonationSerializer(serializers.ModelSerializer):
    """
    Handles pledge creation input and read-only display of a donation.
    `campaign` is write-only on input since it's supplied via the URL in
    the pledge endpoint, not the request body.
    """

    class Meta:
        model = Donation
        fields = ["id", "campaign", "donor_name", "amount", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Donation amount must be greater than zero.")
        return value


class CampaignSerializer(serializers.ModelSerializer):
    """
    Full campaign representation including computed progress fields,
    used for both list/detail views and campaign creation.
    """

    progress_percentage = serializers.ReadOnlyField()
    is_fully_funded = serializers.ReadOnlyField()
    donation_count = serializers.SerializerMethodField()

    class Meta:
        model = Campaign
        fields = [
            "id",
            "title",
            "description",
            "target_amount",
            "raised_amount",
            "is_active",
            "progress_percentage",
            "is_fully_funded",
            "donation_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "raised_amount", "created_at", "updated_at"]

    def get_donation_count(self, obj: Campaign) -> int:
        return obj.donations.count()

    def validate_target_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Target amount must be greater than zero.")
        return value