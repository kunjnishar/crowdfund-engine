from django.contrib import admin

from campaigns.models import Campaign, Donation


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ("title", "target_amount", "raised_amount", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("title", "description")
    readonly_fields = ("raised_amount", "created_at", "updated_at")


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ("campaign", "donor_name", "amount", "created_at")
    search_fields = ("donor_name", "campaign__title")
    readonly_fields = ("created_at",)