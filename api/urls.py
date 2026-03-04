from django.urls import path

from .views import (
    ActiveProgramsView,
    ApplicationCreateView,
    CallbackRequestCreateView,
    CaseDetailView,
    CaseListView,
    ProgramDetailView,
    ProgramsWithBatchesView,
    PublicationDetailView,
    PublicationFeaturedView,
    PublicationListView,
    TestimonialFeaturedView,
    TestimonialListCreateView,
)

urlpatterns = [
    path('active-programs/', ActiveProgramsView.as_view(), name='active-programs'),
    path('programs-with-batches/', ProgramsWithBatchesView.as_view(), name='programs-with-batches'),
    path('programs/<int:program_id>/', ProgramDetailView.as_view(), name='program-detail'),
    path('applications/', ApplicationCreateView.as_view(), name='application-create'),
    path('callback-requests/', CallbackRequestCreateView.as_view(), name='callback-request-create'),
    # Publications
    path('publications/', PublicationListView.as_view(), name='publication-list'),
    path('publications/featured/', PublicationFeaturedView.as_view(), name='publication-featured'),
    path('publications/<slug:slug>/', PublicationDetailView.as_view(), name='publication-detail'),
    # Cases
    path('cases/', CaseListView.as_view(), name='case-list'),
    path('cases/<slug:slug>/', CaseDetailView.as_view(), name='case-detail'),
    # Testimonials
    path('testimonials/', TestimonialListCreateView.as_view(), name='testimonial-list'),
    path('testimonials/featured/', TestimonialFeaturedView.as_view(), name='testimonial-featured'),
]

