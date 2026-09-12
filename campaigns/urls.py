from django.urls import path

from campaigns.views import CampaignDetailView, CampaignListCreateView, PledgeView

app_name = "campaigns"

urlpatterns = [
    path("api/campaigns/", CampaignListCreateView.as_view(), name="campaign-list-create"),
    path("api/campaigns/<int:pk>/", CampaignDetailView.as_view(), name="campaign-detail"),
    path("api/campaigns/<int:pk>/pledge/", PledgeView.as_view(), name="campaign-pledge"),
]