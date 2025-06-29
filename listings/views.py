from rest_framework import viewsets, status, permissions, views, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer, CharField
from django.contrib.auth.models import User
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import ListingSerializer, BookingSerializer, UserSerializer
from .models import Payment, Booking, Listing
from django.contrib.auth.models import User

class RegisterSerializer(ModelSerializer):
    password = CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name']
        read_only_fields = ['id', 'created_at', 'last_seen', 'updated_at']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],

        )
        return user

class RegisterView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({'message': 'User registered successfully'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

class ListingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing property listings.
    
    Provides CRUD operations for listings including:
    - List all listings
    - Create new listing
    - Retrieve specific listing
    - Update listing
    - Delete listing
    - Search listings by location or name
    """
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer
    
    @swagger_auto_schema(
        method='get',
        operation_description="Search listings by location or property name",
        manual_parameters=[
            openapi.Parameter(
                'search',
                openapi.IN_QUERY,
                description="Search term for location or property name",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'min_price',
                openapi.IN_QUERY,
                description="Minimum price per night",
                type=openapi.TYPE_NUMBER
            ),
            openapi.Parameter(
                'max_price',
                openapi.IN_QUERY,
                description="Maximum price per night",
                type=openapi.TYPE_NUMBER
            ),
        ],
        responses={200: ListingSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Search listings based on various criteria.
        """
        queryset = self.get_queryset()
        
    
        search_term = request.query_params.get('search', None)
        if search_term:
            queryset = queryset.filter(
                Q(location__icontains=search_term) |
                Q(name__icontains=search_term) |
                Q(description__icontains=search_term)
            )
        

        min_price = request.query_params.get('min_price', None)
        if min_price:
            try:
                queryset = queryset.filter(price_per_night__gte=float(min_price))
            except ValueError:
                pass
                
        max_price = request.query_params.get('max_price', None)
        if max_price:
            try:
                queryset = queryset.filter(price_per_night__lte=float(max_price))
            except ValueError:
                pass
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        method='get',
        operation_description="Get all bookings for a specific listing",
        responses={200: BookingSerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def bookings(self, request, pk=None):
        """
        Get all bookings for a specific listing.
        """
        listing = self.get_object()
        bookings = Booking.objects.filter(property_id=listing)
        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data)


class BookingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing property bookings.
    
    Provides CRUD operations for bookings including:
    - List all bookings
    - Create new booking
    - Retrieve specific booking
    - Update booking
    - Delete booking
    - Get user's bookings
    """
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Create a new booking with validation.
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Additional validation can be added here
            # e.g., check for overlapping bookings, availability, etc.
            
            # Check if the listing exists
            property_id = serializer.validated_data.get('property_id')
            if not Listing.objects.filter(id=property_id.id).exists():
                return Response(
                    {'error': 'Listing does not exist'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check for overlapping bookings
            check_in = serializer.validated_data.get('check_in')
            check_out = serializer.validated_data.get('check_out')
            
            overlapping_bookings = Booking.objects.filter(
                property_id=property_id,
                check_in__lt=check_out,
                check_out__gt=check_in
            )
            
            if overlapping_bookings.exists():
                return Response(
                    {'error': 'Property is not available for the selected dates'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        method='get',
        operation_description="Get bookings for a specific user",
        manual_parameters=[
            openapi.Parameter(
                'user_id',
                openapi.IN_QUERY,
                description="User ID to filter bookings",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={200: BookingSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def user_bookings(self, request):
        """
        Get all bookings for a specific user.
        """
        user_id = request.query_params.get('user_id', None)
        if not user_id:
            return Response(
                {'error': 'user_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            bookings = Booking.objects.filter(user_id=user_id)
            serializer = self.get_serializer(bookings, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @swagger_auto_schema(
        method='post',
        operation_description="Cancel a booking",
        responses={
            200: openapi.Response('Booking cancelled successfully'),
            404: openapi.Response('Booking not found')
        }
    )
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel a specific booking.
        """
        try:
            booking = self.get_object()
            # Add any cancellation logic here (e.g., check cancellation policy)
            booking.delete()
            return Response(
                {'message': 'Booking cancelled successfully'},
                status=status.HTTP_200_OK
            )
        except Booking.DoesNotExist:
            return Response(
                {'error': 'Booking not found'},
                status=status.HTTP_404_NOT_FOUND
            )


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