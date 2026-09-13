from decimal import Decimal

from django.db import transaction
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from campaigns.models import Campaign, Donation
from campaigns.serializers import CampaignSerializer, DonationSerializer


@ensure_csrf_cookie
def index_view(request):
    """
    Serves the single-page interactive dashboard.

    @ensure_csrf_cookie guarantees Django sets the csrftoken cookie on this
    page load, even though this view itself doesn't render a Django form.
    The frontend JavaScript reads that cookie and attaches it as an
    X-CSRFToken header on POST requests to /api/campaigns/, which Django's
    CSRF middleware requires in order to accept the request.
    """
    return render(request, "index.html")


class CampaignListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/campaigns/  -> list only approved campaigns, filterable/searchable/orderable
    POST /api/campaigns/  -> submit a new campaign (defaults to PENDING status,
                              not publicly visible until an admin approves it)
    """

    serializer_class = CampaignSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["is_active"]
    search_fields = ["title", "description"]
    ordering_fields = ["created_at", "target_amount", "raised_amount"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Campaign.objects.filter(status=Campaign.Status.APPROVED)


class CampaignDetailView(generics.RetrieveAPIView):
    """
    GET /api/campaigns/<id>/ -> retrieve a single campaign with full detail.
    """

    queryset = Campaign.objects.all()
    serializer_class = CampaignSerializer


class PledgeView(APIView):
    """
    POST /api/campaigns/<id>/pledge/
    Creates a donation against a campaign and atomically updates the
    campaign's raised_amount.

    Concurrency safety: select_for_update() takes a row-level lock on the
    Campaign row for the duration of the transaction, so concurrent pledge
    requests against the same campaign are serialized at the database level
    rather than racing to read-modify-write raised_amount independently,
    which would otherwise allow lost updates or overshooting the target.
    """

    def post(self, request, pk, *args, **kwargs):
        donor_name = request.data.get("donor_name", "Anonymous")
        amount_raw = request.data.get("amount")

        try:
            amount = Decimal(str(amount_raw))
        except (TypeError, ValueError, ArithmeticError):
            return Response(
                {"detail": "A valid numeric amount is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if amount <= 0:
            return Response(
                {"detail": "Donation amount must be greater than zero."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            try:
                campaign = Campaign.objects.select_for_update().get(pk=pk)
            except Campaign.DoesNotExist:
                return Response(
                    {"detail": "Campaign not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            if not campaign.is_active:
                return Response(
                    {"detail": "Cannot pledge to an inactive campaign."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if campaign.status != Campaign.Status.APPROVED:
                return Response(
                    {"detail": "Cannot pledge to a campaign that hasn't been approved."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            donation = Donation.objects.create(
                campaign=campaign,
                donor_name=donor_name or "Anonymous",
                amount=amount,
            )

            campaign.raised_amount = campaign.raised_amount + amount
            campaign.save(update_fields=["raised_amount", "updated_at"])

        response_serializer = CampaignSerializer(campaign)
        donation_serializer = DonationSerializer(donation)
        return Response(
            {
                "campaign": response_serializer.data,
                "donation": donation_serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )