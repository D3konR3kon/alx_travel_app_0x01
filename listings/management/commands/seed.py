# listings/management/commands/seed.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from decimal import Decimal
from datetime import date, timedelta
import random
from listings.models import Listing, Booking, Review


class Command(BaseCommand):
    help = 'Seed the database with sample listings, bookings, and reviews data'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--listings',
            type=int,
            default=20,
            help='Number of listings to create (default: 20)'
        )
        parser.add_argument(
            '--bookings',
            type=int,
            default=50,
            help='Number of bookings to create (default: 50)'
        )
        parser.add_argument(
            '--reviews',
            type=int,
            default=30,
            help='Number of reviews to create (default: 30)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding'
        )
    
    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(
                self.style.WARNING('Clearing existing data...')
            )
            self.clear_data()
        
        self.stdout.write(
            self.style.SUCCESS('Starting database seeding...')
        )
        
        with transaction.atomic():
            users = self.create_users()
            listings = self.create_listings(users, options['listings'])
            bookings = self.create_bookings(users, listings, options['bookings'])
            reviews = self.create_reviews(users, listings, bookings, options['reviews'])
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully seeded database with:\n'
                f'- {len(users)} users\n'
                f'- {len(listings)} listings\n'
                f'- {len(bookings)} bookings\n'
                f'- {len(reviews)} reviews'
            )
        )
    
    def clear_data(self):
        """Clear existing data"""
        Review.objects.all().delete()
        Booking.objects.all().delete()
        Listing.objects.all().delete()
        # Keep admin user, delete others
        User.objects.exclude(is_superuser=True).delete()
    
    def create_users(self):
        """Create sample users"""
        users_data = [
            {'username': 'john_host', 'first_name': 'John', 'last_name': 'Smith', 'email': 'john@example.com'},
            {'username': 'sarah_host', 'first_name': 'Sarah', 'last_name': 'Johnson', 'email': 'sarah@example.com'},
            {'username': 'mike_guest', 'first_name': 'Mike', 'last_name': 'Brown', 'email': 'mike@example.com'},
            {'username': 'emma_guest', 'first_name': 'Emma', 'last_name': 'Davis', 'email': 'emma@example.com'},
            {'username': 'alex_traveler', 'first_name': 'Alex', 'last_name': 'Wilson', 'email': 'alex@example.com'},
            {'username': 'lisa_explorer', 'first_name': 'Lisa', 'last_name': 'Miller', 'email': 'lisa@example.com'},
            {'username': 'david_nomad', 'first_name': 'David', 'last_name': 'Garcia', 'email': 'david@example.com'},
            {'username': 'anna_wanderer', 'first_name': 'Anna', 'last_name': 'Martinez', 'email': 'anna@example.com'},
        ]
        
        users = []
        for user_data in users_data:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults=user_data
            )
            if created:
                user.set_password('password123')
                user.save()
            users.append(user)
        
        self.stdout.write(f'Created/updated {len(users)} users')
        return users
    
    def create_listings(self, users, count):
        """Create sample listings"""
        locations = [
            'New York, NY', 'Los Angeles, CA', 'Chicago, IL', 'Houston, TX',
            'Phoenix, AZ', 'Philadelphia, PA', 'San Antonio, TX', 'San Diego, CA',
            'Dallas, TX', 'San Jose, CA', 'Austin, TX', 'Jacksonville, FL',
            'San Francisco, CA', 'Columbus, OH', 'Fort Worth, TX', 'Indianapolis, IN',
            'Charlotte, NC', 'Seattle, WA', 'Denver, CO', 'Washington, DC'
        ]
        
        property_types = ['house', 'apartment', 'condo', 'villa', 'cabin']
        
        amenities_options = [
            'WiFi, Kitchen, Parking',
            'Pool, Gym, WiFi, Air Conditioning',
            'Kitchen, Washer, Dryer, Balcony',
            'Hot Tub, Fireplace, Mountain View',
            'Beach Access, WiFi, Parking, Kitchen',
            'City View, Gym, Concierge, WiFi',
            'Garden, BBQ, Parking, Pet Friendly',
            'Rooftop Terrace, WiFi, Kitchen, Elevator'
        ]
        
        listing_titles = [
            'Cozy Downtown Apartment', 'Luxury Beachfront Villa', 'Modern City Loft',
            'Charming Suburban House', 'Mountain Cabin Retreat', 'Stylish Studio Apartment',
            'Family-Friendly Home', 'Elegant Penthouse Suite', 'Rustic Country House',
            'Contemporary Condo', 'Historic Brownstone', 'Seaside Cottage',
            'Urban Oasis', 'Peaceful Garden Home', 'Sleek High-Rise Unit',
            'Traditional Farmhouse', 'Artistic Warehouse Loft', 'Riverside Cabin',
            'Designer Apartment', 'Tropical Paradise Villa'
        ]
        
        listings = []
        hosts = users[:4]  # Use first 4 users as hosts
        
        for i in range(count):
            title = random.choice(listing_titles)
            if i < len(listing_titles):
                title = listing_titles[i]
            
            listing = Listing.objects.create(
                title=title,
                description=f"Beautiful {title.lower()} perfect for your stay. "
                           f"This property offers comfort and convenience in a great location.",
                location=random.choice(locations),
                price_per_night=Decimal(str(random.randint(50, 500))),
                number_of_bedrooms=random.randint(1, 4),
                number_of_bathrooms=random.randint(1, 3),
                max_guests=random.randint(2, 8),
                property_type=random.choice(property_types),
                amenities=random.choice(amenities_options),
                availability=random.choice([True, True, True, False]),  # 75% available
                host=random.choice(hosts)
            )
            listings.append(listing)
        
        self.stdout.write(f'Created {len(listings)} listings')
        return listings
    
    def create_bookings(self, users, listings, count):
        """Create sample bookings"""
        statuses = ['pending', 'confirmed', 'cancelled', 'completed']
        guests = users[2:]  # Use users starting from index 2 as guests
        
        bookings = []
        
        for _ in range(count):
            listing = random.choice(listings)
            guest = random.choice(guests)
            
            # Generate random dates
            start_date = date.today() + timedelta(days=random.randint(-30, 90))
            nights = random.randint(1, 14)
            end_date = start_date + timedelta(days=nights)
            
            # Skip if guest is same as host
            if guest == listing.host:
                continue
            
            booking = Booking.objects.create(
                listing=listing,
                guest=guest,
                check_in_date=start_date,
                check_out_date=end_date,
                number_of_guests=random.randint(1, min(listing.max_guests, 4)),
                status=random.choice(statuses),
                special_requests=random.choice([
                    '', 'Late check-in requested', 'Need parking space',
                    'Celebrating anniversary', 'Traveling with pet'
                ])
            )
            bookings.append(booking)
        
        self.stdout.write(f'Created {len(bookings)} bookings')
        return bookings
    
    def create_bookings(self, users, listings, count):
        """Create sample bookings"""
        statuses = ['pending', 'confirmed', 'cancelled', 'completed']
        guests = users[2:]  # Use users starting from index 2 as guests
        
        bookings = []
        
        for _ in range(count):
            listing = random.choice(listings)
            guest = random.choice(guests)
            
            # Generate random dates
            start_date = date.today() + timedelta(days=random.randint(-30, 90))
            nights = random.randint(1, 14)
            end_date = start_date + timedelta(days=nights)
            
            # Skip if guest is same as host
            if guest == listing.host:
                continue
            
            # Calculate total price
            total_price = listing.price_per_night * nights
            
            booking = Booking.objects.create(
                listing=listing,
                guest=guest,
                check_in_date=start_date,
                check_out_date=end_date,
                number_of_guests=random.randint(1, min(listing.max_guests, 4)),
                total_price=total_price, 
                status=random.choice(statuses),
                special_requests=random.choice([
                    '', 'Late check-in requested', 'Need parking space',
                    'Celebrating anniversary', 'Traveling with pet'
                ])
            )
            bookings.append(booking)
        
        self.stdout.write(f'Created {len(bookings)} bookings')
        return bookings
    
    def create_reviews(self, users, listings, bookings, count):
        """Create sample reviews"""
        review_comments = [
            "Amazing place! Clean, comfortable, and great location.",
            "Host was very responsive and helpful. Highly recommend!",
            "Perfect for our family vacation. Will definitely book again.",
            "Beautiful property with stunning views. Loved every minute.",
            "Great value for money. Everything was as described.",
            "Excellent communication from host. Property exceeded expectations.",
            "Convenient location with easy access to attractions.",
            "Peaceful and relaxing stay. Perfect for a getaway.",
            "Modern amenities and comfortable beds. Great experience overall.",
            "Would recommend to anyone looking for quality accommodation."
        ]
        
        reviews = []
        completed_bookings = [b for b in bookings if b.status == 'completed']
        guests = users[2:]
        
        # Create reviews for some completed bookings
        for booking in completed_bookings[:count//2]:
            if random.choice([True, False]):  # 50% chance
                try:
                    review = Review.objects.create(
                        listing=booking.listing,
                        reviewer=booking.guest,
                        booking=booking,
                        rating=random.randint(3, 5),  # Mostly positive reviews
                        comment=random.choice(review_comments)
                    )
                    reviews.append(review)
                except Exception as e:
                    # Skip if review already exists or other constraint violation
                    continue
        
        # Create additional reviews without specific bookings
        remaining_count = count - len(reviews)
        for _ in range(remaining_count):
            listing = random.choice(listings)
            reviewer = random.choice(guests)
            
            # Skip if reviewer is the host or already reviewed this listing
            if (reviewer == listing.host or 
                Review.objects.filter(listing=listing, reviewer=reviewer).exists()):
                continue
            
            try:
                review = Review.objects.create(
                    listing=listing,
                    reviewer=reviewer,
                    rating=random.randint(1, 5),
                    comment=random.choice(review_comments)
                )
                reviews.append(review)
            except Exception as e:
                # Skip if constraint violation (e.g., duplicate review)
                continue
            
            # Stop if we've reached the desired count
            if len(reviews) >= count:
                break
        
        self.stdout.write(f'Created {len(reviews)} reviews')
        return reviews