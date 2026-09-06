from django.apps import AppConfig

# -----------------------------------------------------
# Application configuration for the Recycling app
# This file tells Django how to set up and identify the app
# -----------------------------------------------------
class RecyclingConfig(AppConfig):
    # Defines the default type of primary key Django will use
    # for models that do not explicitly set a primary key field
    default_auto_field = 'django.db.models.BigAutoField'

    # The full Python path to the app (folder structure)
    # This must match the directory layout in your project
    name = 'waste_collection.recycling'
