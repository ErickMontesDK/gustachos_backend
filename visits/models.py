from django.db import models

class ClientType(models.Model):
    name = models.CharField(
        max_length=100, 
        unique=True, 
        null=False,
        blank=False,
        verbose_name="Client Type Name",
        help_text="The category or type of the client (e.g., Retail, Wholesale)."
    )

    abbreviation = models.CharField(unique=True, max_length=5, verbose_name="Abbreviation", null=True, blank=True)
    
    class Meta:
        verbose_name = "Client Type"
        verbose_name_plural = "Client Types"

    def __str__(self):
        return f"{self.name} ({self.abbreviation})"

class Client(models.Model):
    """
    Client/Customer model to visit.
    """
    code = models.CharField(
        max_length=20, 
        unique=True, 
        verbose_name="Client Code",
        help_text="Unique identifier for the client.",
        null=False,
        blank=False
    )
    client_type = models.ForeignKey(
        ClientType, 
        on_delete=models.SET_NULL,
        related_name="clients",
        verbose_name="Type",
        null=True,
        blank=True
    )
    name = models.CharField(max_length=150, verbose_name="Business Name", null=False, blank=False)
    address = models.CharField(max_length=255, verbose_name="Address", null=True, blank=True)
    neighborhood = models.CharField(max_length=100, null=True, blank=True, verbose_name="Neighborhood")
    municipality = models.CharField(max_length=100, verbose_name="Municipality", null=True, blank=True)
    state = models.CharField(max_length=100, verbose_name="State", null=True, blank=True)
    route = models.ForeignKey(
        'Route', 
        on_delete=models.PROTECT,
        related_name="clients",
        verbose_name="Route",
        null=True,
        blank=True
    )
    
    latitude = models.DecimalField(max_digits=12, decimal_places=9, null=False, blank=False)
    longitude = models.DecimalField(max_digits=12, decimal_places=9, null=False, blank=False)
    
    sector = models.CharField(max_length=100, null=True, blank=True, verbose_name="Sector")
    market = models.CharField(max_length=100, null=True, blank=True, verbose_name="Market")
    
    is_active = models.BooleanField(default=False, verbose_name="Is Active")
    is_deleted = models.BooleanField(default=False, verbose_name="Is Deleted")
    created_by = models.ForeignKey(
        'users.User', 
        on_delete=models.SET_NULL, 
        related_name="registered_clients", 
        verbose_name="Created By", 
        null=True, 
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At", null=True, blank=True)

    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        ordering = ['name']

    def get_full_address(self):
        return f"{self.address}, {self.neighborhood}. {self.municipality}, {self.state}"

    def __str__(self):
        return f"{self.code} - {self.name}"


class Visit(models.Model):
    """
    Model to record a visit to a client.
    """
    client = models.ForeignKey(
        Client, 
        on_delete=models.PROTECT,
        related_name="visits",
        verbose_name="Client",
        null=False,
        blank=False
    )
    deliverer = models.ForeignKey(
        'users.User', 
        on_delete=models.PROTECT,
        related_name="visits",
        verbose_name="Deliverer",
        null=False,
        blank=False
    )
    
    visited_at = models.DateTimeField(verbose_name="Visited At", null=False, blank=False, auto_now_add=False)
    
    latitude_recorded = models.DecimalField(max_digits=12, decimal_places=9, null=False, blank=False)
    longitude_recorded = models.DecimalField(max_digits=12, decimal_places=9, null=False, blank=False)
    
    is_productive = models.BooleanField(default=False, verbose_name="Is Productive")
    is_deleted = models.BooleanField(default=False, verbose_name="Is Deleted")
    is_valid = models.BooleanField(default=False, verbose_name="Is Valid")
    distance_from_client = models.DecimalField(max_digits=12, decimal_places=6, null=True, blank=True)
    notes = models.TextField(null=True, blank=True, verbose_name="Notes")

    class Meta:
        verbose_name = "Visit"
        verbose_name_plural = "Visits"

    def __str__(self):
        client_name = getattr(self.client, "name", "Unknown client")
        return f"Visit to {client_name} on {self.visited_at:%Y-%m-%d %H:%M}"

    # sale = models.BooleanField(default=False) #TODO: Not implemented yet


class Route(models.Model):
    """
    Model to record a route.
    """
    DAYS_OF_WEEK = (
        ('Mon', 'Monday'),
        ('Tue', 'Tuesday'),
        ('Wed', 'Wednesday'),
        ('Thu', 'Thursday'),
        ('Fri', 'Friday'),
        ('Sat', 'Saturday'),
        ('Sun', 'Sunday'),
    )
    name = models.CharField(max_length=100, verbose_name="Route Name")
    deliverer = models.ForeignKey(
        'users.User', 
        on_delete=models.PROTECT,
        related_name="routes",
        verbose_name="Deliverer"
    )
    day_of_week = models.CharField(max_length=3, verbose_name="Day of Week", choices=DAYS_OF_WEEK)



    

    
    