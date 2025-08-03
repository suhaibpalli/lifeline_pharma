from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg, Count, F
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone

from .models import Product, Category, Manufacturer, ProductReview, Stock
from .forms import ProductSearchForm, ProductReviewForm, ProductFilterForm

class ProductCatalogView(ListView):
    """Product catalog with search and filtering"""
    model = Product
    template_name = 'products/catalog.html'
    context_object_name = 'products'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).select_related(
            'category', 'manufacturer'
        ).prefetch_related('images', 'reviews')
        
        # Search functionality
        query = self.request.GET.get('query')
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(manufacturer__name__icontains=query) |
                Q(category__name__icontains=query)
            )
        
        # Category filtering
        category_slug = self.request.GET.get('category')
        if category_slug:
            try:
                category = Category.objects.get(slug=category_slug)
                # Include products from subcategories
                categories = [category] + category.get_all_children
                queryset = queryset.filter(category__in=categories)
            except Category.DoesNotExist:
                pass
        
        # Manufacturer filtering
        manufacturer_slug = self.request.GET.get('manufacturer')
        if manufacturer_slug:
            queryset = queryset.filter(manufacturer__slug=manufacturer_slug)
        
        # Price filtering
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        if min_price:
            queryset = queryset.filter(patient_price__gte=min_price)
        if max_price:
            queryset = queryset.filter(patient_price__lte=max_price)
        
        # Prescription filtering
        prescription_required = self.request.GET.get('prescription_required')
        if prescription_required:
            queryset = queryset.filter(prescription_required=prescription_required)
        
        # Stock filtering
        in_stock = self.request.GET.get('in_stock')
        if in_stock:
            queryset = queryset.filter(stock_quantity__gt=0)
        
        # Sorting
        sort = self.request.GET.get('sort', '-created_at')
        if sort:
            queryset = queryset.order_by(sort)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = ProductSearchForm(self.request.GET)
        context['filter_form'] = ProductFilterForm(self.request.GET)
        context['categories'] = Category.objects.filter(is_active=True, parent=None)
        context['manufacturers'] = Manufacturer.objects.filter(is_active=True)[:10]
        context['total_products'] = self.get_queryset().count()
        
        # Add user-specific pricing
        for product in context['products']:
            product.user_price = product.get_price_for_user(self.request.user)
            product.discount_percentage = product.get_discount_percentage(self.request.user)
        
        return context

class ProductDetailView(DetailView):
    """Product detail view"""
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_object(self, queryset=None):
        product = super().get_object(queryset)
        # Increment view count
        Product.objects.filter(id=product.id).update(view_count=F('view_count') + 1)
        return product
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = context['product']
        
        # User-specific pricing
        context['user_price'] = product.get_price_for_user(self.request.user)
        context['discount_percentage'] = product.get_discount_percentage(self.request.user)
        
        # Reviews
        reviews = product.reviews.filter(is_approved=True).select_related('user')
        context['reviews'] = reviews
        context['user_review'] = None
        
        if self.request.user.is_authenticated:
            context['user_review'] = reviews.filter(user=self.request.user).first()
        
        # Related products
        context['related_products'] = Product.objects.filter(
            category=product.category,
            is_active=True
        ).exclude(id=product.id)[:4]
        
        # Stock status
        context['stock_status'] = {
            'in_stock': product.is_in_stock,
            'low_stock': product.is_low_stock,
            'quantity': product.stock_quantity if product.track_inventory else None
        }
        
        return context

class CategoryProductsView(ListView):
    """Products by category"""
    model = Product
    template_name = 'products/category_products.html'
    context_object_name = 'products'
    paginate_by = 12
    
    def get_queryset(self):
        self.category = get_object_or_404(Category, slug=self.kwargs['slug'], is_active=True)
        # Include products from subcategories
        categories = [self.category] + self.category.get_all_children
        return Product.objects.filter(
            category__in=categories,
            is_active=True
        ).select_related('category', 'manufacturer').prefetch_related('images')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        context['subcategories'] = self.category.children.filter(is_active=True)
        return context

class ManufacturerProductsView(ListView):
    """Products by manufacturer"""
    model = Product
    template_name = 'products/manufacturer_products.html'
    context_object_name = 'products'
    paginate_by = 12
    
    def get_queryset(self):
        self.manufacturer = get_object_or_404(Manufacturer, slug=self.kwargs['slug'], is_active=True)
        return Product.objects.filter(
            manufacturer=self.manufacturer,
            is_active=True
        ).select_related('category', 'manufacturer').prefetch_related('images')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['manufacturer'] = self.manufacturer
        return context

class ProductSearchView(ListView):
    """Product search results"""
    model = Product
    template_name = 'products/search_results.html'
    context_object_name = 'products'
    paginate_by = 12
    
    def get_queryset(self):
        query = self.request.GET.get('q', '').strip()
        if not query:
            return Product.objects.none()
        
        return Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(manufacturer__name__icontains=query) |
            Q(category__name__icontains=query),
            is_active=True
        ).select_related('category', 'manufacturer').prefetch_related('images')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        context['total_results'] = self.get_queryset().count()
        return context

class ProductReviewCreateView(LoginRequiredMixin, CreateView):
    """Create product review"""
    model = ProductReview
    form_class = ProductReviewForm
    template_name = 'products/review_form.html'
    login_url = '/accounts/login/'
    
    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(Product, slug=kwargs['slug'])
        
        # Check if user already reviewed this product
        if ProductReview.objects.filter(product=self.product, user=request.user).exists():
            messages.warning(request, 'You have already reviewed this product.')
            return redirect(self.product.get_absolute_url())
        
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.product = self.product
        form.instance.user = self.request.user
        messages.success(self.request, 'Your review has been submitted successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return self.product.get_absolute_url()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = self.product
        return context

# AJAX Views
def product_quick_view(request, product_id):
    """AJAX view for product quick view modal"""
    if request.method == 'GET':
        try:
            product = Product.objects.select_related('category', 'manufacturer').get(
                id=product_id, is_active=True
            )
            user_price = product.get_price_for_user(request.user)
            discount_percentage = product.get_discount_percentage(request.user)
            
            data = {
                'id': product.id,
                'name': product.name,
                'slug': product.slug,
                'manufacturer': product.manufacturer.name,
                'category': product.category.name,
                'description': product.short_description or product.description[:200],
                'mrp_price': float(product.mrp_price),
                'user_price': float(user_price),
                'discount_percentage': discount_percentage,
                'prescription_required': product.prescription_required,
                'in_stock': product.is_in_stock,
                'stock_quantity': product.stock_quantity if product.track_inventory else None,
                'primary_image': product.primary_image.image_data if product.primary_image else None,
                'url': product.get_absolute_url(),
            }
            return JsonResponse(data)
        except Product.DoesNotExist:
            return JsonResponse({'error': 'Product not found'}, status=404)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

def search_suggestions(request):
    """AJAX view for search suggestions"""
    if request.method == 'GET':
        query = request.GET.get('q', '').strip()
        if len(query) < 2:
            return JsonResponse({'suggestions': []})
        
        # Get product suggestions
        products = Product.objects.filter(
            name__icontains=query,
            is_active=True
        )[:5]
        
        # Get category suggestions
        categories = Category.objects.filter(
            name__icontains=query,
            is_active=True
        )[:3]
        
        suggestions = []
        
        # Add product suggestions
        for product in products:
            suggestions.append({
                'type': 'product',
                'name': product.name,
                'url': product.get_absolute_url(),
                'manufacturer': product.manufacturer.name,
                'price': float(product.get_price_for_user(request.user)),
            })
        
        # Add category suggestions
        for category in categories:
            suggestions.append({
                'type': 'category',
                'name': category.name,
                'url': category.get_absolute_url(),
                'product_count': category.product_count,
            })
        
        return JsonResponse({'suggestions': suggestions})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)
