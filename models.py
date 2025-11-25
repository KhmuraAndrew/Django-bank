from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
import uuid
from django.core.validators import MinValueValidator

class Account(models.Model):
    ACCOUNT_TYPES = (
        ('checking', 'Расчетный счет'),
        ('savings', 'Накопительный счет'),
        ('credit', 'Кредитный счет'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    account_number = models.CharField(max_length=20, unique=True)
    account_type = models.CharField(max_length=10, choices=ACCOUNT_TYPES)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    currency = models.CharField(max_length=3, default='RUB')

    def __str__(self):
        return f"{self.account_number} - {self.user.username}"

class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('deposit', 'Пополнение'),
        ('withdrawal', 'Снятие'),
        ('transfer', 'Перевод'),
        ('payment', 'Платеж'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    from_account = models.ForeignKey(Account, on_delete=models.CASCADE, 
                                   related_name='sent_transactions', null=True, blank=True)
    to_account = models.ForeignKey(Account, on_delete=models.CASCADE, 
                                 related_name='received_transactions', null=True, blank=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0.01)])
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, default='completed')

    def __str__(self):
        return f"Transaction {self.id}"

class Card(models.Model):
    CARD_TYPES = (
        ('debit', 'Дебетовая'),
        ('credit', 'Кредитная'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    card_number = models.CharField(max_length=16)
    card_type = models.CharField(max_length=10, choices=CARD_TYPES)
    expiration_date = models.CharField(max_length=5)
    cvv = models.CharField(max_length=3)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"****{self.card_number[-4:]}"

class DepositRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Ожидает'),
        ('completed', 'Выполнено'),
        ('cancelled', 'Отменено'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0.01)])
    description = models.CharField(max_length=255, default='Пополнение счета')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Deposit {self.amount} to {self.account.account_number}"