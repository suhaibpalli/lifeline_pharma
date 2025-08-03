from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from django.urls import reverse
from apps.core.models import TimeStampedModel
import uuid

User = get_user_model()

class Category(TimeStampedModel):
    """Product categories with hierarchical support"""
    
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='children'
    )
    image = models.TextField(blank=True)  # Base64 encoded image
    icon = models.CharField(max_length=50, blank=True)  # FontAwesome icon class
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ['sort_order', 'name']
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('products:category_products', kwargs={'slug': self.slug})
    
    @property
    def get_all_children(self):
        """Get all descendant categories"""
        children = []
        for child in self.children.filter(is_active=True):
            children.append(child)
            children.extend(child.get_all_children)
        return children
    
    @property
    def product_count(self):
        """Get total product count including subcategories"""
        count = self.products.filter(is_active=True).count()
        for child in self.get_all_children:
            count += child.products.filter(is_active=True).count()
        return count

class Manufacturer(TimeStampedModel):
    """Product manufacturers/brands"""
    
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    logo = models.TextField(blank=True)  # Base64 encoded logo
    website_url = models.URLField(blank=True)
    contact_email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Manufacturer"
        verbose_name_plural = "Manufacturers"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('products:manufacturer_products', kwargs={'slug': self.slug})
    
    @property
    def product_count(self):
        return self.products.filter(is_active=True).count()

class Product(TimeStampedModel):
    """Main product model"""
    
    PRESCRIPTION_CHOICES = [
        ('OTC', 'Over The Counter'),
        ('RX', 'Prescription Required'),
    ]
    
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.CASCADE, related_name='products')
    
    # Product Details
    description = models.TextField()
    short_description = models.TextField(max_length=500, blank=True)
    composition = models.TextField(blank=True)
    dosage_form = models.CharField(max_length=100, blank=True)  # Tablet, Capsule, Syrup, etc.
    strength = models.CharField(max_length=100, blank=True)  # 500mg, 10ml, etc.
    pack_size = models.CharField(max_length=100, blank=True)  # 10 tablets, 100ml bottle, etc.
    
    # Prescription Requirements
    prescription_required = models.CharField(
        max_length=3,
        choices=PRESCRIPTION_CHOICES,
        default='OTC'
    )
    
    # Pricing
    mrp_price = models.DecimalField(max_digits=10, decimal_places=2)
    patient_price = models.DecimalField(max_digits=10, decimal_places=2)
    pharmacy_price = models.DecimalField(max_digits=10, decimal_places=2)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    # Inventory
    stock_quantity = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=10)
    track_inventory = models.BooleanField(default=True)
    
    # Product Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    # SEO Fields
    meta_title = models.CharField(max_length=60, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    meta_keywords = models.TextField(blank=True)
    
    # Analytics
    view_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.manufacturer.name}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.name}-{self.manufacturer.name}")
        
        # Auto-generate short description if not provided
        if not self.short_description and self.description:
            self.short_description = self.description[:500]
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('products:product_detail', kwargs={'slug': self.slug})
    
    def get_price_for_user(self, user):
        """Get price based on user type"""
        if user and user.is_authenticated and user.user_type == 'PHARMACY':
            return self.pharmacy_price
        return self.patient_price
    
    def get_discount_percentage(self, user):
        """Calculate discount percentage"""
        user_price = self.get_price_for_user(user)
        if self.mrp_price > 0:
            discount = ((self.mrp_price - user_price) / self.mrp_price) * 100
            return round(discount, 1)
        return 0
    
    @property
    def is_in_stock(self):
        if not self.track_inventory:
            return True
        return self.stock_quantity > 0
    
    @property
    def is_low_stock(self):
        if not self.track_inventory:
            return False
        return self.stock_quantity <= self.low_stock_threshold
    
    @property
    def primary_image(self):
        """Get primary product image"""
        return self.images.filter(is_primary=True).first()
    
    @property
    def average_rating(self):
        """Calculate average rating"""
        reviews = self.reviews.filter(is_approved=True)
        if reviews.exists():
            return round(reviews.aggregate(models.Avg('rating'))['rating__avg'], 1)
        return 0
    
    @property
    def review_count(self):
        """Get total review count"""
        return self.reviews.filter(is_approved=True).count()

class ProductImage(TimeStampedModel):
    """Product images"""
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image_data = models.TextField()  # Base64 encoded image
    thumbnail_data = models.TextField(blank=True)  # Base64 encoded thumbnail
    alt_text = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = "Product Image"
        verbose_name_plural = "Product Images"
        ordering = ['sort_order', '-is_primary']
    
    def __str__(self):
        return f"{self.product.name} - Image {self.id}"
    
    def save(self, *args, **kwargs):
        # Ensure only one primary image per product
        if self.is_primary:
            ProductImage.objects.filter(
                product=self.product,
                is_primary=True
            ).exclude(id=self.id).update(is_primary=False)
        
        # If this is the first image, make it primary
        if not self.product.images.exists():
            self.is_primary = True
            
        super().save(*args, **kwargs)

class ProductReview(TimeStampedModel):
    """Product reviews and ratings"""
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='product_reviews')
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5 stars"
    )
    title = models.CharField(max_length=200, blank=True)
    review_text = models.TextField()
    is_verified_purchase = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=True)
    helpful_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = "Product Review"
        verbose_name_plural = "Product Reviews"
        ordering = ['-created_at']
        unique_together = ['product', 'user']  # One review per user per product
    
    def __str__(self):
        return f"{self.product.name} - {self.user.email} ({self.rating} stars)"

class Stock(TimeStampedModel):
    """Stock tracking model"""
    
    STOCK_MOVEMENT_TYPES = [
        ('IN', 'Stock In'),
        ('OUT', 'Stock Out'),
        ('ADJUSTMENT', 'Stock Adjustment'),
        ('RETURN', 'Return'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_movements')
    movement_type = models.CharField(max_length=10, choices=STOCK_MOVEMENT_TYPES)
    quantity = models.IntegerField()  # Positive for IN, negative for OUT
    batch_number = models.CharField(max_length=50, blank=True)
    expiry_date = models.DateField(blank=True, null=True)
    supplier = models.CharField(max_length=200, blank=True)
    cost_price_per_unit = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = "Stock Movement"
        verbose_name_plural = "Stock Movements"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.product.name} - {self.movement_type} ({self.quantity})"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update product stock quantity
        self.product.stock_quantity = self.product.stock_movements.aggregate(
            total=models.Sum('quantity')
        )['total'] or 0
        self.product.save(update_fields=['stock_quantity'])

class ProductTag(TimeStampedModel):
    """Product tags for better categorization"""
    
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    products = models.ManyToManyField(Product, related_name='tags', blank=True)
    
    class Meta:
        verbose_name = "Product Tag"
        verbose_name_plural = "Product Tags"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
