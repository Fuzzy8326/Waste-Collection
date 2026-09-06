from django.urls import path
from . import views

# URL patterns for the Waste Collection app
urlpatterns = [

    # ------------------------------
    # Home page – public landing page / dashboard
    # ------------------------------
    path('', views.HomeView.as_view(), name='home'),

    # ------------------------------
    # Auth – Signup / Login / Logout
    # ------------------------------
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('login/', views.CollectionLoginView.as_view(), name='login'),
    path('logout/', views.CollectionLogoutView.as_view(), name='logout'),

    # ------------------------------
    # List all collection requests (moved off '/', which is now the homepage)
    # ------------------------------
    path('collections/',
         views.CollectionListView.as_view(),
         name='collection_list'),

    # ------------------------------
    # Detail page – View a single collection record
    # <int:pk> captures the record's primary key
    # ------------------------------
    path('collection/<int:pk>/',
         views.CollectionDetailView.as_view(),
         name='collection_detail'),

    # ------------------------------
    # Create page – Add a new waste collection entry
    # ------------------------------
    path('collection/new/',
         views.CollectionCreateView.as_view(),
         name='collection_create'),

    # ------------------------------
    # Update page – Edit an existing collection entry
    # ------------------------------
    path('collection/<int:pk>/edit/',
         views.CollectionUpdateView.as_view(),
         name='collection_update'),

    # ------------------------------
    # Delete page – Remove a collection entry
    # ------------------------------
    path('collection/<int:pk>/delete/',
         views.CollectionDeleteView.as_view(),
         name='collection_delete'),

    # ------------------------------
    # Admin tool – bulk-archive completed collections for a chosen month
    # (archived records stay visible in the resident's own history)
    # ------------------------------
    path('collections/archive-completed/',
         views.ArchiveCompletedByMonthView.as_view(),
         name='archive_completed'),
]