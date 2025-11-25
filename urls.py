from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('accounts/', views.accounts_view, name='accounts'),
    path('transactions/', views.transactions_view, name='transactions'),
    path('transfer/', views.transfer_view, name='transfer'),
    path('deposit/', views.deposit_view, name='deposit'),
    path('register/', views.register, name='register'),
    path('ajax/get_balance/', views.ajax_get_account_balance, name='ajax_get_balance'),
    path('ajax/get_transactions/', views.ajax_get_transactions, name='ajax_get_transactions'),
    path('ajax/validate_account/', views.ajax_validate_account, name='ajax_validate_account'),
]