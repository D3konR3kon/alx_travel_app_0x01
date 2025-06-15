from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
import uuid


class Listing(models.Model):
    """
    Model representing a property listing.
    """
    PROPERTY_TYPES = [
        ('apartment', 'Apartment'),
        ('house', 'House'),
        ('villa', 'Villa'),
        ('cabin', 'Cabin'),
        ('condo', 'Condominium'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200, help_text="Property title")
    description = models.TextField(help_text="Detailed property description")
    location = models.CharField(max_length=200, help_text="Property location")
    property_type = models.CharField(
        max_length=20, 
        choices=PROPERTY_TYPES, 
        default='apartment',
        help_text="Type of property"
    )
    price_per_night = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text="Price per night in local currency"
    )
    max_guests = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(50)],
        help_text="Maximum number of guests allowed"
    )
    number_of_bedrooms = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Number of bedrooms"
    )
    number_of_bathrooms = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Number of bathrooms"
    )
    amenities = models.TextField(
        blank=True,
        help_text="Comma-separated list of amenities"
    )
    house_rules = models.TextField(
        blank=True,
        help_text="Property rules and guidelines"
    )
    
    # Location details
    latitude = models.FloatField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
        help_text="Latitude coordinate"
    )
    longitude = models.FloatField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
        help_text="Longitude coordinate"
    )
    
    # Availability and status
    availability = models.BooleanField(default=True, help_text="Is listing available for booking?")
    instant_book = models.BooleanField(default=False, help_text="Allow instant booking?")
    
    # Host information
    host = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='listings',
        null=True,
        blank=True,
        help_text="Property host/owner"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['location']),
            models.Index(fields=['price_per_night']),
            models.Index(fields=['property_type']),
            models.Index(fields=['availability']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.location}"
    
    def get_amenities_list(self):
        """Return amenities as a list."""
        if self.amenities:
            return [amenity.strip() for amenity in self.amenities.split(',')]
        return []
    
    def average_rating(self):
        """Calculate average rating from reviews."""
        reviews = self.reviews.all()
        if reviews:
            return sum(review.rating for review in reviews) / len(reviews)
        return 0
    
    def total_bookings(self):
        """Get total number of bookings for this listing."""
        return self.bookings.count()


class Booking(models.Model):
    """
    Model representing a booking for a property.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    listing = models.ForeignKey(
        Listing, 
        on_delete=models.CASCADE, 
        related_name='bookings',
        help_text="The property being booked"
    )
    
    # Guest information
    guest = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bookings',
        help_text="Guest who made the booking"
    )
    guest_email = models.EmailField(help_text="Guest contact email")
    guest_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Guest contact phone"
    )
    
    # Booking details
    check_in_date = models.DateField(help_text="Check-in date")
    check_out_date = models.DateField(help_text="Check-out date")
    number_of_guests = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Number of guests"
    )
    
    # Pricing
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total booking cost (calculated automatically)"
    )
    
    # Status and requests
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Booking status"
    )
    special_requests = models.TextField(
        blank=True,
        help_text="Special requests from guest"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['guest']),
            models.Index(fields=['check_in_date', 'check_out_date']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Booking {self.id} - {self.listing.title}"
    
    def save(self, *args, **kwargs):
        """Override save to calculate total cost."""
        if self.check_in_date and self.check_out_date and self.listing:
            nights = (self.check_out_date - self.check_in_date).days
            self.total_price = nights * self.listing.price_per_night
        super().save(*args, **kwargs)
    
    def nights_count(self):
        """Calculate number of nights."""
        if self.check_out_date and self.check_in_date:
            return (self.check_out_date - self.check_in_date).days
        return 0
    
    def is_past(self):
        """Check if booking is in the past."""
        from datetime import date
        return self.check_out_date < date.today()
    
    def is_current(self):
        """Check if booking is currently active."""
        from datetime import date
        today = date.today()
        return self.check_in_date <= today <= self.check_out_date
    
    def can_cancel(self):
        """Check if booking can be cancelled."""
        from datetime import date, timedelta
        # Allow cancellation up to 24 hours before check-in
        return (
            self.status in ['pending', 'confirmed'] and
            self.check_in_date > date.today() + timedelta(days=1)
        )


class Review(models.Model):
    """
    Model for property reviews.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name='review',
        null=True,
        blank=True
    )
    reviewer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5 stars"
    )
    comment = models.TextField(help_text="Review comment")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['listing', 'reviewer']  # One review per user per listing
    
    def __str__(self):
        return f"{self.rating}★ - {self.listing.title}"


class ListingImage(models.Model):
    """
    Model for property images.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(
        upload_to='listings/',
        help_text="Property image"
    )
    caption = models.CharField(
        max_length=200,
        blank=True,
        help_text="Image caption"
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="Is this the primary image?"
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return f"Image for {self.listing.title}"