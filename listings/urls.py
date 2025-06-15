from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ListingViewSet, BookingViewSet, RegisterView


router = DefaultRouter()
router.register(r'listings', ListingViewSet, basename='listing')
router.register(r'bookings', BookingViewSet, basename='booking')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/register/', RegisterView.as_view(), name='register'),
    # path('auth/login/', RegisterView.as_view(), name='register')
    
   
]

# GET    /api/listings/                 - List all listings
# POST   /api/listings/                 - Create new listing
# GET    /api/listings/{id}/            - Retrieve specific listing
# PUT    /api/listings/{id}/            - Update listing
# PATCH  /api/listings/{id}/            - Partial update listing
# DELETE /api/listings/{id}/            - Delete listing
# GET    /api/listings/search/          - Search listings
# GET    /api/listings/{id}/bookings/   - Get bookings for a listing

# GET    /api/bookings/                 - List all bookings
# POST   /api/bookings/                 - Create new booking
# GET    /api/bookings/{id}/            - Retrieve specific booking
# PUT    /api/bookings/{id}/            - Update booking
# PATCH  /api/bookings/{id}/            - Partial update booking
# DELETE /api/bookings/{id}/            - Delete booking
# GET    /api/bookings/user_bookings/   - Get user's bookings
# POST   /api/bookings/{id}/cancel/     - Cancel a booking