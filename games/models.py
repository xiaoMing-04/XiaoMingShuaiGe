from django.db import models
from django.utils import timezone
from users.models import MyUser
import stripe
from django.conf import settings
from decimal import Decimal

stripe.api_key = settings.STRIPE_SECRET_KEY

# Create your models here.

# Game:
# - id: PK(stripe)
# - price_id: string (stripe) (update)
# - title: string
# - desc: text
# - price: decimal
# - discount: decimal (optional)
# - publisher: string
# - release_date: datetime
# - img_url: string
# - category: string
# - quantity: interger

class Game(models.Model):
    stripe_product_id = models.CharField(max_length=100, blank=True, null=True, editable=False)
    stripe_price_id = models.CharField(max_length=100, blank=True, null=True, editable=False)
    
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    publisher = models.CharField(max_length=255)
    release_date = models.DateTimeField(default=timezone.now)
    image = models.ImageField(upload_to='game_images', default='game_images/default.png')
    category = models.CharField(max_length=255)
    quantity = models.IntegerField(default=0)

    def __str__(self):
        return self.name


    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        try:
            # Create Stripe product
            stripe_product = stripe.Product.create(
                name=self.name,
                description=self.description
            )

            # Calculate discounted price
            discounted_price = self.price * (Decimal('1.00') - (self.discount / Decimal('100.00')))

            # Create Stripe price
            stripe_price = stripe.Price.create(
                product=stripe_product.id,
                unit_amount=int(discounted_price * 100),
                currency='usd',
            )

            self.stripe_product_id = stripe_product.id
            self.stripe_price_id = stripe_price.id
            super().save(update_fields=['stripe_product_id', 'stripe_price_id'])
        except Exception as e:
            print(f"Stripe error: {e}")
            raise
    
    
    
# Key:
# - id: PK
# - game_id: FK (update)
# - game_price_id: string  (stripe product price id)
# - key: string, unique
# - status: Enum [available, sold]

class Key(models.Model):
    STATUS_CHOICES = (
        ('available', 'Available'),
        ('sold', 'Sold'),
    )
    
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='keys')
    game_price_id = models.CharField(max_length=255, unique=True)
    key = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='available')
    
    def __str__(self):
        return f"{self.key} ({self.status})"
    

# User_game:
# - id: PF
# - user_id: FK
# - game_id: FK

class UserGame(models.Model):
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='owned_games')
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='owned_by_users')
    
    
    def __str__(self):
        return f"{self.user.email} owns {self.game.title}"
