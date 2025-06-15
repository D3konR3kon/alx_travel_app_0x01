from rest_framework import viewsets, status, permissions, views
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer, CharField
from django.contrib.auth.models import User
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Listing, Booking
from .serializers import ListingSerializer, BookingSerializer, UserSerializer


class RegisterSerializer(ModelSerializer):
    password = CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name']
        read_only_fields = ['user_id', 'created_at', 'last_seen', 'updated_at']

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
        
        # Search by location or property name
        search_term = request.query_params.get('search', None)
        if search_term:
            queryset = queryset.filter(
                Q(location__icontains=search_term) |
                Q(name__icontains=search_term) |
                Q(description__icontains=search_term)
            )
        
        # Filter by price range
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