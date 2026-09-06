from django.contrib import admin
from .models import WasteCollection

# ---------------------------------------------------------
# Admin configuration for the WasteCollection model
# This controls how the model appears in the Django admin site
# ---------------------------------------------------------
@admin.register(WasteCollection)
class WasteCollectionAdmin(admin.ModelAdmin):

    # Fields displayed in the list view table in admin
    list_display = [
        'household_name', 
        'waste_type', 
        'weight_kg', 
        'collection_date', 
        'status'
    ]

    # Filters shown on the right side of the admin list page
    list_filter = [
        'waste_type', 
        'status', 
        'collection_date'
    ]

    # Search bar: admin can search by these fields
    search_fields = [
        'household_name', 
        'address', 
        'phone'
    ]

    # Adds date-based navigation at the top (by year → month → day)
    date_hierarchy = 'collection_date'
