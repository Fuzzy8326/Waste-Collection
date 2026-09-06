# Import Django's model classes and timezone utilities
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

# Define the WasteCollection model - represents a waste collection record in the database
class WasteCollection(models.Model):
    """
    Model to store waste collection information.
    Each instance represents one waste collection appointment.
    """

    # Define choices for waste types - these will appear as image cards
    WASTE_TYPES = [
        ('plastic', 'Plastic'),      # Plastic waste
        ('paper', 'Paper'),          # Paper and cardboard
        ('glass', 'Glass'),          # Glass bottles and containers
        ('metal', 'Metal'),          # Metal cans and items
        ('organic', 'Organic'),      # Food waste and organic matter
        ('electronic', 'Electronic'), # E-waste (computers, phones, etc.)
    ]

    # ---------------------------------------------------------------
    # Status workflow (client-facing wording):
    #   submitted  -> the resident just requested a collection
    #   pending    -> staff accepted the request; pickup is pending
    #   collected  -> the waste has physically been picked up
    #   completed  -> the recycling order/process has finished
    #
    # Residents can never set this directly - it always starts at
    # "submitted" and only moves forward when an admin updates it.
    # ---------------------------------------------------------------
    STATUS_CHOICES = [
        ('submitted', 'Submitted for Collection'),
        ('pending', 'Pending Pickup'),
        ('collected', 'Collected'),
        ('completed', 'Completed'),
    ]

    archived = models.BooleanField(
    default=False,
    help_text="Hidden from the admin's active list once archived, but still fully visible in the resident's own history.",
)
    # stores short text with maximum length
    # Used for household/family name
    household_name = models.CharField(max_length=200)

    # stores longer text without length limit
    # Used for full address with multiple lines
    address = models.TextField()

    # stores phone number as text (preserves formatting like +1-555-1234)
    phone = models.CharField(max_length=20)

    # Now rendered client-side as clickable image cards instead of a
    # plain dropdown, but it's still a simple choice field under the hood.
    waste_type = models.CharField(max_length=20, choices=WASTE_TYPES)

    weight_kg = models.DecimalField(max_digits=6, decimal_places=2)

    # DateField: stores only the date (no time)
    # default=timezone.now: if no date provided, use current date
    collection_date = models.DateField(default=timezone.now)

    # CharField with choices and default value
    # default='submitted': every new request starts as "Submitted for Collection"
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')

    # TextField for optional additional notes
    # blank=True: not required in forms
    # null=True: can be NULL in database
    notes = models.TextField(blank=True, null=True)

    # -----------------------------------------------------------------
    # Link each record to the user (resident) who requested it.
    # This is what lets us tell "admin" and "user" apart in views/templates
    # and lets a resident see only their own collection requests.
    # null=True so the existing migration/data doesn't break; new records
    # will always have this set by the view.
    # -----------------------------------------------------------------
    requested_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='collection_requests',
    )

    # DateTimeField: stores date and time
    # auto_now_add=True: automatically set when record is created (never changes)
    created_at = models.DateTimeField(auto_now_add=True)

    # DateTimeField with auto_now: updates every time record is saved
    # Tracks the last modification time
    updated_at = models.DateTimeField(auto_now=True)

    # Meta class: provides metadata options for the model
    class Meta:
        # ordering: default sort order when querying records
        # '-collection_date': newest collection dates first (- means descending)
        # '-created_at': if dates are equal, sort by creation time
        ordering = ['-collection_date', '-created_at']

    # String representation: how the object appears as text
    # Used in Django admin, dropdowns, and when printing the object
    def __str__(self):
        return f"{self.household_name} - {self.waste_type} - {self.collection_date}"
