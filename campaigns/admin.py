from django.contrib import admin

from campaigns.models import Campaign, Donation


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "target_amount", "raised_amount", "is_active", "created_at")
    list_filter = ("status", "is_active")
    search_fields = ("title", "description")
    readonly_fields = ("raised_amount", "created_at", "updated_at")
    actions = ["approve_campaigns", "reject_campaigns"]

    @admin.action(description="Approve selected campaigns")
    def approve_campaigns(self, request, queryset):
        queryset.update(status=Campaign.Status.APPROVED)

    @admin.action(description="Reject selected campaigns")
    def reject_campaigns(self, request, queryset):
        queryset.update(status=Campaign.Status.REJECTED)


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ("campaign", "donor_name", "amount", "created_at")
    search_fields = ("donor_name", "campaign__title")
    readonly_fields = ("created_at",)