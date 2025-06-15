from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Avg
from rangefilter.filter import DateRangeFilter
from listings.utils.filters import NumericRangeFilter
from .models import Listing, Booking, Review, ListingImage


class ListingImageInline(admin.TabularInline):
    model = ListingImage
    extra = 1
    fields = ('image', 'caption', 'is_primary', 'order')
    readonly_fields = ('created_at',)


class ReviewInline(admin.TabularInline):
    model = Review
    extra = 0
    readonly_fields = ('created_at', 'reviewer', 'rating', 'comment')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'location', 'property_type', 'price_per_night',
        'max_guests', 'availability', 'booking_count', 'avg_rating', 'created_at'
    ]
    list_filter = [
        'property_type', 'availability', 'instant_book', 'created_at',
        ('price_per_night', NumericRangeFilter),
        ('max_guests', NumericRangeFilter),
    ]
    search_fields = ['title', 'location', 'description', 'amenities']
    readonly_fields = ['id', 'created_at', 'updated_at', 'booking_count', 'avg_rating']

    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'title', 'description', 'property_type', 'host')
        }),
        ('Location', {
            'fields': ('location', 'latitude', 'longitude')
        }),
        ('Property Details', {
            'fields': ('price_per_night', 'max_guests', 'number_of_bedrooms', 'number_of_bathrooms')
        }),
        ('Amenities & Rules', {
            'fields': ('amenities', 'house_rules'),
            'classes': ('collapse',)
        }),
        ('Settings', {
            'fields': ('availability', 'instant_book')
        }),
        ('Statistics', {
            'fields': ('booking_count', 'avg_rating'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    inlines = [ListingImageInline, ReviewInline]
    actions = ['activate_listings', 'deactivate_listings', 'enable_instant_book']

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            booking_count=Count('bookings'),
            avg_rating=Avg('reviews__rating')
        )

    def booking_count(self, obj):
        return obj.booking_count or 0
    booking_count.short_description = 'Bookings'
    booking_count.admin_order_field = 'booking_count'

    def avg_rating(self, obj):
        return f"{obj.avg_rating:.1f}★" if obj.avg_rating else "No ratings"
    avg_rating.short_description = 'Avg Rating'
    avg_rating.admin_order_field = 'avg_rating'

    def activate_listings(self, request, queryset):
        count = queryset.update(availability=True)
        self.message_user(request, f"{count} listings activated.")
    activate_listings.short_description = "Activate selected listings"

    def deactivate_listings(self, request, queryset):
        count = queryset.update(availability=False)
        self.message_user(request, f"{count} listings deactivated.")
    deactivate_listings.short_description = "Deactivate selected listings"

    def enable_instant_book(self, request, queryset):
        count = queryset.update(instant_book=True)
        self.message_user(request, f"Instant booking enabled for {count} listings.")
    enable_instant_book.short_description = "Enable instant booking"


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'property_name', 'get_guest_name', 'check_in_date', 'check_out_date',
        'number_of_guests', 'status', 'total_price', 'nights_display', 'created_at'
    ]
    list_filter = [
        'status', 'created_at',
        ('check_in_date', DateRangeFilter),
        ('check_out_date', DateRangeFilter),
        ('total_price', NumericRangeFilter),
        ('number_of_guests', NumericRangeFilter),
    ]
    search_fields = [
        'listing__title', 'guest__username', 'guest_email',
        'special_requests'
    ]
    readonly_fields = [
        'id', 'total_price', 'nights_display', 'created_at', 'updated_at'
    ]

    fieldsets = (
        ('Booking Information', {
            'fields': ('id', 'listing', 'status')
        }),
        ('Guest Details', {
            'fields': ('guest', 'guest_email', 'guest_phone')
        }),
        ('Stay Details', {
            'fields': ('check_in_date', 'check_out_date', 'number_of_guests', 'nights_display')
        }),
        ('Pricing', {
            'fields': ('total_price',)
        }),
        ('Special Requests', {
            'fields': ('special_requests',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['confirm_bookings', 'cancel_bookings', 'mark_completed']

    def property_name(self, obj):
        return format_html(
            '<a href="/admin/listings/listing/{}/change/">{}</a>',
            obj.listing.id,
            obj.listing.title
        )
    property_name.short_description = 'Property'

    def get_guest_name(self, obj):
        return obj.guest.get_full_name() or obj.guest.username
    get_guest_name.short_description = 'Guest Name'

    def nights_display(self, obj):
        return f"{obj.nights_count()} nights"
    nights_display.short_description = 'Nights'

    def confirm_bookings(self, request, queryset):
        count = queryset.filter(status='pending').update(status='confirmed')
        self.message_user(request, f"{count} bookings confirmed.")
    confirm_bookings.short_description = "Confirm selected bookings"

    def cancel_bookings(self, request, queryset):
        count = queryset.filter(status__in=['pending', 'confirmed']).update(status='cancelled')
        self.message_user(request, f"{count} bookings cancelled.")
    cancel_bookings.short_description = "Cancel selected bookings"

    def mark_completed(self, request, queryset):
        count = queryset.filter(status='confirmed').update(status='completed')
        self.message_user(request, f"{count} bookings marked as completed.")
    mark_completed.short_description = "Mark as completed"


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['listing_name', 'rating', 'reviewer', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['listing__title', 'reviewer__username', 'comment']
    readonly_fields = ['created_at']

    def listing_name(self, obj):
        return format_html(
            '<a href="/admin/listings/listing/{}/change/">{}</a>',
            obj.listing.id,
            obj.listing.title
        )
    listing_name.short_description = 'Listing'


@admin.register(ListingImage)
class ListingImageAdmin(admin.ModelAdmin):
    list_display = ['listing_name', 'caption', 'is_primary', 'order', 'image_preview']
    list_filter = ['is_primary', 'created_at']
    search_fields = ['listing__title', 'caption']
    readonly_fields = ['created_at', 'image_preview']

    def listing_name(self, obj):
        return obj.listing.title
    listing_name.short_description = 'Listing'

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 100px; height: 60px; object-fit: cover;"/>',
                obj.image.url
            )
        return "No image"
    image_preview.short_description = 'Preview'


# Admin site customization
admin.site.site_header = "ALX Travel App Admin"
admin.site.site_title = "ALX Travel App"
admin.site.index_title = "Welcome to ALX Travel App Administration"
