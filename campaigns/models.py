from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class Campaign(models.Model):
    """
    Represents a single crowdfunding campaign with a funding target.
    `raised_amount` is denormalized onto this model (rather than always
    summed live from Donations) so that read-heavy operations like listing
    campaigns and rendering progress bars stay fast, while writes to it are
    tightly controlled through atomic, row-locked updates in the pledge flow.
    """

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    target_amount = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(1)]
    )
    raised_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    @property
    def progress_percentage(self) -> float:
        if self.target_amount <= 0:
            return 0.0
        percentage = (float(self.raised_amount) / float(self.target_amount)) * 100
        return min(percentage, 100.0)

    @property
    def is_fully_funded(self) -> bool:
        return self.raised_amount >= self.target_amount


class Donation(models.Model):
    """
    Represents a single pledge/donation made toward a campaign.
    Kept as an immutable ledger entry: created once and never edited, so the
    sum of all Donation.amount for a campaign can always be reconciled
    against Campaign.raised_amount if ever needed for auditing.
    """

    campaign = models.ForeignKey(
        Campaign, related_name="donations", on_delete=models.CASCADE
    )
    donor_name = models.CharField(max_length=150, blank=True, default="Anonymous")
    amount = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.donor_name} -> {self.campaign.title}: {self.amount}"

    def clean(self):
        if not self.campaign_id:
            return
        if not self.campaign.is_active:
            raise ValidationError("Cannot pledge to an inactive campaign.")
        if self.amount is not None and self.amount <= 0:
            raise ValidationError("Donation amount must be greater than zero.")