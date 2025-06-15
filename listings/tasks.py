from celery import shared_task
from .models import Listing

@shared_task
def process_listing_data():
    listings_count = Listing.objects.count()
    return f"Processed {listings_count} listings"