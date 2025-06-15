from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Listing, Booking, Review
from datetime import date


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        read_only_fields = ['id']


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for Review model"""
    reviewer = UserSerializer(read_only=True)
    reviewer_name = serializers.CharField(source='reviewer.get_full_name', read_only=True)
    
    class Meta:
        model = Review
        fields = [
            'id', 'rating', 'comment', 'created_at', 'updated_at',
            'reviewer', 'reviewer_name'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ListingSerializer(serializers.ModelSerializer):
    """Serializer for Listing model"""
    host = UserSerializer(read_only=True)
    host_name = serializers.CharField(source='host.get_full_name', read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)
    average_rating = serializers.ReadOnlyField()
    reviews_count = serializers.SerializerMethodField()
    amenities_list = serializers.SerializerMethodField()
    
    class Meta:
        model = Listing
        fields = [
            'id', 'title', 'description', 'location', 'price_per_night',
            'number_of_bedrooms', 'number_of_bathrooms', 'max_guests',
            'property_type', 'amenities', 'amenities_list', 'availability',
            'host', 'host_name', 'reviews', 'average_rating', 'reviews_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_reviews_count(self, obj):
        """Get the total number of reviews for this listing"""
        return obj.reviews.count()
    
    def get_amenities_list(self, obj):
        """Convert comma-separated amenities to list"""
        if obj.amenities:
            return [amenity.strip() for amenity in obj.amenities.split(',') if amenity.strip()]
        return []
    
    def validate_price_per_night(self, value):
        """Validate that price is positive"""
        if value <= 0:
            raise serializers.ValidationError("Price per night must be positive.")
        return value
    
    def validate_max_guests(self, value):
        """Validate that max guests is reasonable"""
        if value <= 0:
            raise serializers.ValidationError("Max guests must be at least 1.")
        if value > 50:
            raise serializers.ValidationError("Max guests cannot exceed 50.")
        return value


class ListingListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing lists (without reviews)"""
    host_name = serializers.CharField(source='host.get_full_name', read_only=True)
    average_rating = serializers.ReadOnlyField()
    reviews_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Listing
        fields = [
            'id', 'title', 'location', 'price_per_night',
            'number_of_bedrooms', 'number_of_bathrooms', 'max_guests',
            'property_type', 'availability', 'host_name',
            'average_rating', 'reviews_count', 'created_at'
        ]
    
    def get_reviews_count(self, obj):
        return obj.reviews.count()


class BookingSerializer(serializers.ModelSerializer):
    """Serializer for Booking model"""
    listing = ListingListSerializer(read_only=True)
    listing_id = serializers.CharField(write_only=True, help_text="UUID of the listing to book")
    guest = UserSerializer(read_only=True)
    guest_name = serializers.CharField(source='guest.get_full_name', read_only=True)
    nights = serializers.SerializerMethodField()
    
    class Meta:
        model = Booking
        fields = [
            'id', 'listing', 'listing_id', 'guest', 'guest_name',
            'check_in_date', 'check_out_date', 'number_of_guests',
            'total_price', 'status', 'special_requests', 'nights',
            'guest_email', 'guest_phone', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'total_price', 'created_at', 'updated_at']
    
    def get_nights(self, obj):
        """Calculate number of nights"""
        return (obj.check_out_date - obj.check_in_date).days
    
    def validate(self, data):
        """Validate booking data"""
        check_in = data.get('check_in_date')
        check_out = data.get('check_out_date')
        number_of_guests = data.get('number_of_guests')
        listing_id = data.get('listing_id')

        if check_in and check_out:
            if check_out <= check_in:
                raise serializers.ValidationError(
                    "Check-out date must be after check-in date."
                )
            if check_in < date.today():
                raise serializers.ValidationError(
                    "Check-in date cannot be in the past."
                )
 
        if listing_id and number_of_guests:
            try:
                listing = Listing.objects.get(id=listing_id)
                if number_of_guests > listing.max_guests:
                    raise serializers.ValidationError(
                        f"Number of guests ({number_of_guests}) exceeds "
                        f"maximum capacity ({listing.max_guests})."
                    )
                if not listing.availability:
                    raise serializers.ValidationError(
                        "This listing is not available for booking."
                    )
            except Listing.DoesNotExist:
                raise serializers.ValidationError("Invalid listing ID.")
        
        return data
    
    def create(self, validated_data):
        """Create booking with calculated total price"""
        listing_id = validated_data.pop('listing_id')
        listing = Listing.objects.get(id=listing_id)
        

        nights = (validated_data['check_out_date'] - validated_data['check_in_date']).days
        total_price = listing.price_per_night * nights
        
        booking = Booking.objects.create(
            listing=listing,
            total_price=total_price,
            guest=self.context['request'].user,  # Set the guest to the current user
            **validated_data
        )
        return booking


class BookingListSerializer(serializers.ModelSerializer):
    """Simplified serializer for booking lists"""
    listing_title = serializers.CharField(source='listing.title', read_only=True)
    listing_location = serializers.CharField(source='listing.location', read_only=True)
    guest_name = serializers.CharField(source='guest.get_full_name', read_only=True)
    nights = serializers.SerializerMethodField()
    
    class Meta:
        model = Booking
        fields = [
            'id', 'listing_title', 'listing_location', 'guest_name',
            'check_in_date', 'check_out_date', 'number_of_guests',
            'total_price', 'status', 'nights', 'created_at'
        ]
    
    def get_nights(self, obj):
        return (obj.check_out_date - obj.check_in_date).days