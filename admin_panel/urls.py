from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    # Авторизация
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    
    # Dashboard
    path('', views.dashboard_view, name='dashboard'),
    
    # Direction URLs
    path('directions/', views.DirectionListView.as_view(), name='direction_list'),
    path('directions/create/', views.DirectionCreateView.as_view(), name='direction_create'),
    path('directions/<int:pk>/edit/', views.DirectionUpdateView.as_view(), name='direction_edit'),
    path('directions/<int:pk>/delete/', views.DirectionDeleteView.as_view(), name='direction_delete'),
    
    # LearningFormat URLs
    path('learning-formats/', views.LearningFormatListView.as_view(), name='learningformat_list'),
    path('learning-formats/create/', views.LearningFormatCreateView.as_view(), name='learningformat_create'),
    path('learning-formats/<int:pk>/edit/', views.LearningFormatUpdateView.as_view(), name='learningformat_edit'),
    path('learning-formats/<int:pk>/delete/', views.LearningFormatDeleteView.as_view(), name='learningformat_delete'),
    
    # Program URLs
    path('programs/', views.ProgramListView.as_view(), name='program_list'),
    path('programs/create/', views.ProgramCreateView.as_view(), name='program_create'),
    path('programs/<int:pk>/edit/', views.ProgramUpdateView.as_view(), name='program_edit'),
    path('programs/<int:pk>/delete/', views.ProgramDeleteView.as_view(), name='program_delete'),
    
    # CourseBatch URLs
    path('course-batches/', views.CourseBatchListView.as_view(), name='coursebatch_list'),
    path('course-batches/create/', views.CourseBatchCreateView.as_view(), name='coursebatch_create'),
    path('course-batches/<int:pk>/edit/', views.CourseBatchUpdateView.as_view(), name='coursebatch_edit'),
    path('course-batches/<int:pk>/delete/', views.CourseBatchDeleteView.as_view(), name='coursebatch_delete'),

    # Application URLs
    path('applications/', views.ApplicationListView.as_view(), name='application_list'),
    path('applications/create/', views.ApplicationCreateView.as_view(), name='application_create'),
    path('applications/<int:pk>/edit/', views.ApplicationUpdateView.as_view(), name='application_edit'),
    path('applications/<int:pk>/delete/', views.ApplicationDeleteView.as_view(), name='application_delete'),

    # CallbackRequest URLs
    path('callback-requests/', views.CallbackRequestListView.as_view(), name='callbackrequest_list'),
    path('callback-requests/create/', views.CallbackRequestCreateView.as_view(), name='callbackrequest_create'),
    path('callback-requests/<int:pk>/edit/', views.CallbackRequestUpdateView.as_view(), name='callbackrequest_edit'),
    path('callback-requests/<int:pk>/delete/', views.CallbackRequestDeleteView.as_view(), name='callbackrequest_delete'),

    # Publication URLs (новости и статьи)
    path('publications/', views.PublicationListView.as_view(), name='publication_list'),
    path('publications/create/', views.PublicationCreateView.as_view(), name='publication_create'),
    path('publications/<int:pk>/edit/', views.PublicationUpdateView.as_view(), name='publication_edit'),
    path('publications/<int:pk>/delete/', views.PublicationDeleteView.as_view(), name='publication_delete'),

    # Case URLs
    path('cases/', views.CaseListView.as_view(), name='case_list'),
    path('cases/create/', views.CaseCreateView.as_view(), name='case_create'),
    path('cases/<int:pk>/edit/', views.CaseUpdateView.as_view(), name='case_edit'),
    path('cases/<int:pk>/delete/', views.CaseDeleteView.as_view(), name='case_delete'),

    # Testimonial URLs
    path('testimonials/', views.TestimonialListView.as_view(), name='testimonial_list'),
    path('testimonials/create/', views.TestimonialCreateView.as_view(), name='testimonial_create'),
    path('testimonials/<int:pk>/edit/', views.TestimonialUpdateView.as_view(), name='testimonial_edit'),
    path('testimonials/<int:pk>/delete/', views.TestimonialDeleteView.as_view(), name='testimonial_delete'),
]
