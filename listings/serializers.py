from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.models import User
from .models import Listing, Booking, Review, Payment
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
    



class PaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for Payment model
    """
    booking_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Payment
        fields = [
            'id', 'booking', 'amount', 'currency', 'chapa_transaction_id',
            'chapa_reference', 'chapa_checkout_url', 'status', 'payment_method',
            'customer_email', 'customer_name', 'customer_phone',
            'verified_at', 'verification_attempts', 'created_at', 'updated_at',
            'booking_details'
        ]
        read_only_fields = [
            'id', 'chapa_transaction_id', 'chapa_checkout_url', 'chapa_reference',
            'verified_at', 'verification_attempts', 'created_at', 'updated_at'
        ]
    
    def get_booking_details(self, obj):
        """Get basic booking details"""
        return {
            'id': str(obj.booking.id),
            'listing_title': obj.booking.listing.title,
            'check_in_date': obj.booking.check_in_date,
            'check_out_date': obj.booking.check_out_date,
            'number_of_guests': obj.booking.number_of_guests,
            'total_price': obj.booking.total_price
        }

class PaymentInitializationSerializer(serializers.Serializer):
    """
    Serializer for payment initialization request
    """
    booking_id = serializers.UUIDField()
    customer_name = serializers.CharField(max_length=100)
    customer_email = serializers.EmailField()
    customer_phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    currency = serializers.CharField(max_length=3, default='ETB')
    
    def validate_booking_id(self, value):
        """Validate that booking exists and is not already paid"""
        try:
            booking = Booking.objects.get(id=value)
            
            # Check if booking already has a successful payment
            if hasattr(booking, 'payment') and booking.payment.is_successful():
                raise serializers.ValidationError("This booking has already been paid for.")
            
            # Check if booking is in a valid state for payment
            if booking.status == 'cancelled':
                raise serializers.ValidationError("Cannot pay for a cancelled booking.")
            
            return value
        except Booking.DoesNotExist:
            raise serializers.ValidationError("Booking not found.")

class PaymentVerificationSerializer(serializers.Serializer):
    """
    Serializer for payment verification request
    """
    tx_ref = serializers.CharField(max_length=100)
    
    def validate_tx_ref(self, value):
        """Validate that payment exists"""
        try:
            payment = Payment.objects.get(chapa_reference=value)
            return value
        except Payment.DoesNotExist:
            raise serializers.ValidationError("Payment reference not found.")

class BookingWithPaymentSerializer(serializers.ModelSerializer):
    """
    Extended booking serializer that includes payment information
    """
    payment_status = serializers.SerializerMethodField()
    payment_details = serializers.SerializerMethodField()
    listing_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Booking
        fields = [
            'id', 'listing', 'guest', 'guest_email', 'guest_phone',
            'check_in_date', 'check_out_date', 'number_of_guests',
            'total_price', 'status', 'special_requests',
            'created_at', 'updated_at', 'payment_status', 'payment_details',
            'listing_details'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_payment_status(self, obj):
        """Get payment status if payment exists"""
        if hasattr(obj, 'payment'):
            return obj.payment.status
        return 'no_payment'
    
    def get_payment_details(self, obj):
        """Get payment details if payment exists"""
        if hasattr(obj, 'payment'):
            return {
                'id': str(obj.payment.id),
                'amount': obj.payment.amount,
                'currency': obj.payment.currency,
                'status': obj.payment.status,
                'payment_method': obj.payment.payment_method,
                'chapa_reference': obj.payment.chapa_reference,
                'created_at': obj.payment.created_at
            }
        return None
    
    def get_listing_details(self, obj):
        """Get basic listing details"""
        return {
            'id': str(obj.listing.id),
            'title': obj.listing.title,
            'location': obj.listing.location,
            'property_type': obj.listing.property_type,
            'price_per_night': obj.listing.price_per_night
        }

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']
        read_only_fields = ['id', 'date_joined']

class ListingSerializer(serializers.ModelSerializer):
    """
    Serializer for Listing model
    """
    average_rating = serializers.ReadOnlyField()
    total_bookings = serializers.ReadOnlyField()
    amenities_list = serializers.ReadOnlyField(source='get_amenities_list')
    
    class Meta:
        model = Listing
        fields = [
            'id', 'title', 'description', 'location', 'property_type',
            'price_per_night', 'max_guests', 'number_of_bedrooms',
            'number_of_bathrooms', 'amenities', 'amenities_list', 'house_rules',
            'latitude', 'longitude', 'availability', 'instant_book',
            'host', 'created_at', 'updated_at', 'average_rating', 'total_bookings'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'average_rating', 'total_bookings']