from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from decimal import Decimal
from datetime import date, timedelta
import json
import uuid
from .models import Listing, Booking, Review, ListingImage


class ListingViewSetTestCase(APITestCase):
    """
    Test case for Listing ViewSet endpoints.
    """
  
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()

        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        

        self.listing = Listing.objects.create(
            title='Test Apartment',
            description='A beautiful test apartment',
            location='Test City',
            property_type='apartment',
            price_per_night=Decimal('100.00'),
            max_guests=4,
            number_of_bedrooms=2,
            number_of_bathrooms=1,
            amenities='WiFi, Kitchen, TV',
            house_rules='No smoking',
            latitude=40.7128,
            longitude=-74.0060,
            availability=True,
            instant_book=False,
            host=self.user
        )
        
        self.listing_data = {
            'title': 'New Test Listing',
            'description': 'A new test listing description',
            'location': 'New Test City',
            'property_type': 'house',
            'price_per_night': '150.00',
            'max_guests': 6,
            'number_of_bedrooms': 3,
            'number_of_bathrooms': 2,
            'amenities': 'WiFi, Kitchen, TV, Pool',
            'house_rules': 'No smoking, No pets',
            'latitude': 41.8781,
            'longitude': -87.6298,
            'availability': True,
            'instant_book': True
        }
    
    def test_get_listings_list(self):
        """Test GET /api/listings/ - List all listings."""
        url = reverse('listing-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Test Apartment')
    
    def test_create_listing(self):
        """Test POST /api/listings/ - Create new listing."""
        url = reverse('listing-list')
        response = self.client.post(url, self.listing_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'New Test Listing')
        self.assertEqual(response.data['property_type'], 'house')
        self.assertEqual(response.data['price_per_night'], '150.00')
        
        self.assertTrue(Listing.objects.filter(title='New Test Listing').exists())
    
    def test_get_listing_detail(self):
        """Test GET /api/listings/{id}/ - Retrieve specific listing."""
        url = reverse('listing-detail', kwargs={'pk': self.listing.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(self.listing.id))
        self.assertEqual(response.data['title'], 'Test Apartment')
        self.assertEqual(response.data['location'], 'Test City')
    
    def test_update_listing(self):
        """Test PUT /api/listings/{id}/ - Update listing."""
        url = reverse('listing-detail', kwargs={'pk': self.listing.id})
        updated_data = self.listing_data.copy()
        updated_data['title'] = 'Updated Test Apartment'
        updated_data['price_per_night'] = '175.00'
        
        response = self.client.put(url, updated_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Test Apartment')
        self.assertEqual(response.data['price_per_night'], '175.00')

        self.listing.refresh_from_db()
        self.assertEqual(self.listing.title, 'Updated Test Apartment')
        self.assertEqual(self.listing.price_per_night, Decimal('175.00'))
    
    def test_partial_update_listing(self):
        """Test PATCH /api/listings/{id}/ - Partial update listing."""
        url = reverse('listing-detail', kwargs={'pk': self.listing.id})
        partial_data = {'title': 'Partially Updated Apartment'}
        
        response = self.client.patch(url, partial_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Partially Updated Apartment')

        self.assertEqual(response.data['location'], 'Test City')
    
    def test_delete_listing(self):
        """Test DELETE /api/listings/{id}/ - Delete listing."""
        url = reverse('listing-detail', kwargs={'pk': self.listing.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertFalse(Listing.objects.filter(id=self.listing.id).exists())
    
    def test_search_listings(self):
        """Test GET /api/listings/search/ - Search listings."""
        Listing.objects.create(
            title='Beach House',
            description='Beautiful beach house',
            location='Miami Beach',
            property_type='house',
            price_per_night=Decimal('200.00'),
            max_guests=8,
            number_of_bedrooms=4,
            number_of_bathrooms=3,
            host=self.user
        )
        
        url = reverse('listing-search')

        response = self.client.get(url, {'search': 'Miami'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Beach House')
        
        response = self.client.get(url, {'min_price': '150', 'max_price': '250'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Beach House')
        
        response = self.client.get(url, {'search': 'NonExistent'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
    
    def test_get_listing_bookings(self):
        """Test GET /api/listings/{id}/bookings/ - Get bookings for a listing."""
        booking = Booking.objects.create(
            listing=self.listing,
            guest=self.user,
            guest_email='guest@example.com',
            check_in_date=date.today() + timedelta(days=7),
            check_out_date=date.today() + timedelta(days=10),
            number_of_guests=2,
            status='confirmed'
        )
        
        url = reverse('listing-bookings', kwargs={'pk': self.listing.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['guest_email'], 'guest@example.com')
    
    def test_get_nonexistent_listing(self):
        """Test GET request for non-existent listing returns 404."""
        fake_id = uuid.uuid4()
        url = reverse('listing-detail', kwargs={'pk': fake_id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_create_listing_invalid_data(self):
        """Test POST with invalid data returns 400."""
        url = reverse('listing-list')
        invalid_data = {
            'title': '', 
            'price_per_night': -50, 
            'max_guests': 0, 
        }
        
        response = self.client.post(url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class BookingViewSetTestCase(APITestCase):
    """
    Test case for Booking ViewSet endpoints.
    """
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()

        self.host = User.objects.create_user(
            username='host',
            email='host@example.com',
            password='hostpass123'
        )
        
        self.guest = User.objects.create_user(
            username='guest',
            email='guest@example.com',
            password='guestpass123'
        )
        
        self.listing = Listing.objects.create(
            title='Test Property',
            description='A test property for booking',
            location='Test Location',
            property_type='apartment',
            price_per_night=Decimal('100.00'),
            max_guests=4,
            number_of_bedrooms=2,
            number_of_bathrooms=1,
            host=self.host
        )

        self.booking = Booking.objects.create(
            listing=self.listing,
            guest=self.guest,
            guest_email='guest@example.com',
            guest_phone='+1234567890',
            check_in_date=date.today() + timedelta(days=7),
            check_out_date=date.today() + timedelta(days=10),
            number_of_guests=2,
            status='pending',
            special_requests='Test request'
        )
        
        self.booking_data = {
            'listing': str(self.listing.id),
            'guest': self.guest.id,
            'guest_email': 'newguest@example.com',
            'guest_phone': '+9876543210',
            'check_in_date': (date.today() + timedelta(days=14)).isoformat(),
            'check_out_date': (date.today() + timedelta(days=17)).isoformat(),
            'number_of_guests': 3,
            'status': 'pending',
            'special_requests': 'Early check-in please'
        }
    
    def test_get_bookings_list(self):
        """Test GET /api/bookings/ - List all bookings."""
        url = reverse('booking-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['guest_email'], 'guest@example.com')
    
    def test_create_booking(self):
        """Test POST /api/bookings/ - Create new booking."""
        url = reverse('booking-list')
        response = self.client.post(url, self.booking_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['guest_email'], 'newguest@example.com')
        self.assertEqual(response.data['number_of_guests'], 3)
        self.assertEqual(response.data['status'], 'pending')
        
        self.assertEqual(response.data['total_price'], '300.00')
        

        self.assertTrue(Booking.objects.filter(guest_email='newguest@example.com').exists())
    
    def test_get_booking_detail(self):
        """Test GET /api/bookings/{id}/ - Retrieve specific booking."""
        url = reverse('booking-detail', kwargs={'pk': self.booking.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(self.booking.id))
        self.assertEqual(response.data['guest_email'], 'guest@example.com')
        self.assertEqual(response.data['status'], 'pending')
    
    def test_update_booking(self):
        """Test PUT /api/bookings/{id}/ - Update booking."""
        url = reverse('booking-detail', kwargs={'pk': self.booking.id})
        updated_data = self.booking_data.copy()
        updated_data['status'] = 'confirmed'
        updated_data['number_of_guests'] = 4
        
        response = self.client.put(url, updated_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'confirmed')
        self.assertEqual(response.data['number_of_guests'], 4)
        
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'confirmed')
        self.assertEqual(self.booking.number_of_guests, 4)
    
    def test_partial_update_booking(self):
        """Test PATCH /api/bookings/{id}/ - Partial update booking."""
        url = reverse('booking-detail', kwargs={'pk': self.booking.id})
        partial_data = {'status': 'confirmed'}
        
        response = self.client.patch(url, partial_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'confirmed')

        self.assertEqual(response.data['guest_email'], 'guest@example.com')
    
    def test_delete_booking(self):
        """Test DELETE /api/bookings/{id}/ - Delete booking."""
        url = reverse('booking-detail', kwargs={'pk': self.booking.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        self.assertFalse(Booking.objects.filter(id=self.booking.id).exists())
    
    def test_cancel_booking(self):
        """Test POST /api/bookings/{id}/cancel/ - Cancel booking."""
        url = reverse('booking-cancel', kwargs={'pk': self.booking.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('cancelled', response.data['message'].lower())
        
        self.assertFalse(Booking.objects.filter(id=self.booking.id).exists())
    
    def test_get_user_bookings(self):
        """Test GET /api/bookings/user_bookings/ - Get user's bookings."""

        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        
        Booking.objects.create(
            listing=self.listing,
            guest=other_user,
            guest_email='other@example.com',
            check_in_date=date.today() + timedelta(days=20),
            check_out_date=date.today() + timedelta(days=23),
            number_of_guests=1,
            status='confirmed'
        )
        
        url = reverse('booking-user-bookings')
        response = self.client.get(url, {'user_id': self.guest.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['guest_email'], 'guest@example.com')
    
    def test_get_user_bookings_missing_user_id(self):
        """Test user_bookings endpoint without user_id parameter."""
        url = reverse('booking-user-bookings')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('user_id parameter is required', response.data['error'])
    
    def test_create_booking_overlapping_dates(self):
        """Test creating booking with overlapping dates."""
        url = reverse('booking-list')
        overlapping_data = self.booking_data.copy()
        overlapping_data['check_in_date'] = (date.today() + timedelta(days=8)).isoformat()
        overlapping_data['check_out_date'] = (date.today() + timedelta(days=11)).isoformat()
        
        response = self.client.post(url, overlapping_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('not available', response.data['error'])
    
    def test_create_booking_nonexistent_listing(self):
        """Test creating booking for non-existent listing."""
        url = reverse('booking-list')
        invalid_data = self.booking_data.copy()
        invalid_data['listing'] = str(uuid.uuid4())
        
        response = self.client.post(url, invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_create_booking_invalid_data(self):
        """Test POST with invalid booking data."""
        url = reverse('booking-list')
        invalid_data = {
            'listing': str(self.listing.id),
            'guest_email': 'invalid-email',  # Invalid email format
            'check_in_date': 'invalid-date',  # Invalid date format
            'check_out_date': (date.today() + timedelta(days=1)).isoformat(),
            'number_of_guests': -1,  # Invalid guest count
        }
        
        response = self.client.post(url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_cancel_nonexistent_booking(self):
        """Test cancelling non-existent booking."""
        fake_id = uuid.uuid4()
        url = reverse('booking-cancel', kwargs={'pk': fake_id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class BookingModelTestCase(TestCase):
    """
    Test case for Booking model methods.
    """
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.listing = Listing.objects.create(
            title='Test Property',
            description='A test property',
            location='Test Location',
            property_type='apartment',
            price_per_night=Decimal('100.00'),
            max_guests=4,
            number_of_bedrooms=2,
            number_of_bathrooms=1,
            host=self.user
        )
    
    def test_nights_count_calculation(self):
        """Test nights_count method."""
        booking = Booking.objects.create(
            listing=self.listing,
            guest=self.user,
            guest_email='test@example.com',
            check_in_date=date.today(),
            check_out_date=date.today() + timedelta(days=3),
            number_of_guests=2
        )
        
        self.assertEqual(booking.nights_count(), 3)
    
    def test_total_price_calculation(self):
        """Test automatic total price calculation."""
        booking = Booking.objects.create(
            listing=self.listing,
            guest=self.user,
            guest_email='test@example.com',
            check_in_date=date.today(),
            check_out_date=date.today() + timedelta(days=5),
            number_of_guests=2
        )
        
        self.assertEqual(booking.total_price, Decimal('500.00'))  # 5 nights * $100
    
    def test_is_past_method(self):
        """Test is_past method."""
        past_booking = Booking.objects.create(
            listing=self.listing,
            guest=self.user,
            guest_email='test@example.com',
            check_in_date=date.today() - timedelta(days=10),
            check_out_date=date.today() - timedelta(days=7),
            number_of_guests=2
        )
        
        future_booking = Booking.objects.create(
            listing=self.listing,
            guest=self.user,
            guest_email='test2@example.com',
            check_in_date=date.today() + timedelta(days=7),
            check_out_date=date.today() + timedelta(days=10),
            number_of_guests=2
        )
        
        self.assertTrue(past_booking.is_past())
        self.assertFalse(future_booking.is_past())
    
    def test_is_current_method(self):
        """Test is_current method."""
        current_booking = Booking.objects.create(
            listing=self.listing,
            guest=self.user,
            guest_email='test@example.com',
            check_in_date=date.today() - timedelta(days=1),
            check_out_date=date.today() + timedelta(days=2),
            number_of_guests=2
        )
        
        future_booking = Booking.objects.create(
            listing=self.listing,
            guest=self.user,
            guest_email='test2@example.com',
            check_in_date=date.today() + timedelta(days=7),
            check_out_date=date.today() + timedelta(days=10),
            number_of_guests=2
        )
        
        self.assertTrue(current_booking.is_current())
        self.assertFalse(future_booking.is_current())
    
    def test_can_cancel_method(self):
        """Test can_cancel method."""

        cancellable_booking = Booking.objects.create(
            listing=self.listing,
            guest=self.user,
            guest_email='test@example.com',
            check_in_date=date.today() + timedelta(days=3),
            check_out_date=date.today() + timedelta(days=6),
            number_of_guests=2,
            status='confirmed'
        )

        non_cancellable_booking = Booking.objects.create(
            listing=self.listing,
            guest=self.user,
            guest_email='test2@example.com',
            check_in_date=date.today(),
            check_out_date=date.today() + timedelta(days=3),
            number_of_guests=2,
            status='confirmed'
        )
        
        completed_booking = Booking.objects.create(
            listing=self.listing,
            guest=self.user,
            guest_email='test3@example.com',
            check_in_date=date.today() + timedelta(days=7),
            check_out_date=date.today() + timedelta(days=10),
            number_of_guests=2,
            status='completed'
        )
        
        self.assertTrue(cancellable_booking.can_cancel())
        self.assertFalse(non_cancellable_booking.can_cancel())
        self.assertFalse(completed_booking.can_cancel())


class ListingModelTestCase(TestCase):
    """
    Test case for Listing model methods.
    """
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.listing = Listing.objects.create(
            title='Test Property',
            description='A test property',
            location='Test Location',
            property_type='apartment',
            price_per_night=Decimal('100.00'),
            max_guests=4,
            number_of_bedrooms=2,
            number_of_bathrooms=1,
            amenities='WiFi, Kitchen, TV, Pool',
            host=self.user
        )
    
    def test_get_amenities_list(self):
        """Test get_amenities_list method."""
        amenities_list = self.listing.get_amenities_list()
        expected_list = ['WiFi', 'Kitchen', 'TV', 'Pool']
        
        self.assertEqual(amenities_list, expected_list)
    
    def test_get_amenities_list_empty(self):
        """Test get_amenities_list with empty amenities."""
        listing = Listing.objects.create(
            title='No Amenities Property',
            description='A property with no amenities',
            location='Test Location',
            property_type='apartment',
            price_per_night=Decimal('50.00'),
            max_guests=2,
            number_of_bedrooms=1,
            number_of_bathrooms=1,
            amenities='',
            host=self.user
        )
        
        amenities_list = listing.get_amenities_list()
        self.assertEqual(amenities_list, [])
    
    def test_average_rating(self):
        """Test average_rating method."""

        Review.objects.create(
            listing=self.listing,
            reviewer=self.user,
            rating=5,
            comment='Excellent property!'
        )
        
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        
        Review.objects.create(
            listing=self.listing,
            reviewer=other_user,
            rating=4,
            comment='Good property'
        )
        
        average = self.listing.average_rating()
        self.assertEqual(average, 4.5)
    
    def test_average_rating_no_reviews(self):
        """Test average_rating with no reviews."""
        average = self.listing.average_rating()
        self.assertEqual(average, 0)
    
    def test_total_bookings(self):
        """Test total_bookings method."""

        Booking.objects.create(
            listing=self.listing,
            guest=self.user,
            guest_email='test1@example.com',
            check_in_date=date.today() + timedelta(days=7),
            check_out_date=date.today() + timedelta(days=10),
            number_of_guests=2
        )
        
        Booking.objects.create(
            listing=self.listing,
            guest=self.user,
            guest_email='test2@example.com',
            check_in_date=date.today() + timedelta(days=14),
            check_out_date=date.today() + timedelta(days=17),
            number_of_guests=3
        )
        
        total = self.listing.total_bookings()
        self.assertEqual(total, 2)
    
    def test_listing_str_representation(self):
        """Test string representation of listing."""
        expected_str = f"{self.listing.title} - {self.listing.location}"
        self.assertEqual(str(self.listing), expected_str)


# Test runner command
if __name__ == '__main__':
    import django
    from django.conf import settings
    from django.test.utils import get_runner
    
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                }
            },
            INSTALLED_APPS=[
                'django.contrib.auth',
                'django.contrib.contenttypes',
                'rest_framework',
                'your_app_name',  # Replace with your actual app name
            ],
            SECRET_KEY='test-secret-key',
        )
    
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests([__name__])
    if failures:
        exit(failures)