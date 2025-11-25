from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db.models import Q
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
import json
from .models import Account, Transaction, Card, DepositRequest
from decimal import Decimal
import random
from django.utils import timezone

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Создаем автоматически расчетный счет для нового пользователя
            account_number = ''.join([str(random.randint(0, 9)) for _ in range(16)])
            Account.objects.create(
                user=user,
                account_number=account_number,
                account_type='checking',
                balance=1000.00  # Начальный баланс для новых пользователей
            )
            
            # Автоматический вход после регистрации
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            
            messages.success(request, 'Регистрация прошла успешно! Добро пожаловать в банк "Хмура"!')
            return redirect('index')
    else:
        form = UserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})

@login_required
def index(request):
    accounts = Account.objects.filter(user=request.user, is_active=True)
    cards = Card.objects.filter(user=request.user, is_active=True)
    
    # Получаем последние транзакции
    transactions = Transaction.objects.filter(
        Q(from_account__user=request.user) | 
        Q(to_account__user=request.user)
    ).order_by('-created_at')[:5]
    
    context = {
        'accounts': accounts,
        'cards': cards,
        'transactions': transactions,
    }
    return render(request, 'index.html', context)

@login_required
def accounts_view(request):
    accounts = Account.objects.filter(user=request.user, is_active=True)
    return render(request, 'accounts.html', {'accounts': accounts})

@login_required
def transactions_view(request):
    transactions = Transaction.objects.filter(
        Q(from_account__user=request.user) | 
        Q(to_account__user=request.user)
    ).order_by('-created_at')[:50]
    return render(request, 'transactions.html', {'transactions': transactions})

@login_required
def transfer_view(request):
    if request.method == 'POST':
        from_account_id = request.POST.get('from_account')
        to_account_number = request.POST.get('to_account')
        amount = Decimal(request.POST.get('amount'))
        description = request.POST.get('description', '')
        
        try:
            from_account = Account.objects.get(id=from_account_id, user=request.user)
            to_account = Account.objects.get(account_number=to_account_number)
            
            if from_account.balance >= amount:
                from_account.balance -= amount
                to_account.balance += amount
                from_account.save()
                to_account.save()
                
                Transaction.objects.create(
                    from_account=from_account,
                    to_account=to_account,
                    amount=amount,
                    transaction_type='transfer',
                    description=f"Перевод: {description}"
                )
                
                return JsonResponse({'success': True, 'message': 'Перевод выполнен успешно'})
            else:
                return JsonResponse({'success': False, 'message': 'Недостаточно средств'})
                
        except Account.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Счет не найден'})
    
    accounts = Account.objects.filter(user=request.user, is_active=True)
    return render(request, 'transfer.html', {'accounts': accounts})

@login_required
def deposit_view(request):
    if request.method == 'POST':
        account_id = request.POST.get('account')
        amount = Decimal(request.POST.get('amount'))
        description = request.POST.get('description', 'Пополнение счета')
        
        try:
            account = Account.objects.get(id=account_id, user=request.user)
            
            # Создаем запрос на пополнение
            deposit_request = DepositRequest.objects.create(
                user=request.user,
                account=account,
                amount=amount,
                description=description,
                status='completed',  # В реальной системе здесь была бы проверка платежа
                completed_at=timezone.now()
            )
            
            # Пополняем счет
            account.balance += amount
            account.save()
            
            # Создаем транзакцию
            Transaction.objects.create(
                to_account=account,
                amount=amount,
                transaction_type='deposit',
                description=description
            )
            
            messages.success(request, f'Счет успешно пополнен на {amount} ₽')
            return redirect('accounts')
            
        except Account.DoesNotExist:
            messages.error(request, 'Счет не найден')
    
    accounts = Account.objects.filter(user=request.user, is_active=True)
    return render(request, 'deposit.html', {'accounts': accounts})

@login_required
@require_POST
@csrf_exempt
def ajax_get_account_balance(request):
    account_id = request.POST.get('account_id')
    try:
        account = Account.objects.get(id=account_id, user=request.user)
        return JsonResponse({
            'success': True,
            'balance': str(account.balance),
            'currency': account.currency
        })
    except Account.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Счет не найден'})

@login_required
@require_POST
@csrf_exempt
def ajax_get_transactions(request):
    account_id = request.POST.get('account_id')
    try:
        transactions = Transaction.objects.filter(
            Q(from_account_id=account_id) | 
            Q(to_account_id=account_id)
        ).order_by('-created_at')[:20]
        
        transactions_data = []
        for transaction in transactions:
            transactions_data.append({
                'date': transaction.created_at.strftime('%d.%m.%Y %H:%M'),
                'type': transaction.get_transaction_type_display(),
                'amount': str(transaction.amount),
                'description': transaction.description,
                'is_outgoing': transaction.from_account_id == int(account_id)
            })
        
        return JsonResponse({'success': True, 'transactions': transactions_data})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@login_required
@require_POST
@csrf_exempt
def ajax_validate_account(request):
    account_number = request.POST.get('account_number')
    try:
        account = Account.objects.get(account_number=account_number)
        return JsonResponse({
            'success': True,
            'account_exists': True,
            'account_type': account.get_account_type_display(),
            'user_name': f"{account.user.first_name} {account.user.last_name}".strip() or account.user.username
        })
    except Account.DoesNotExist:
        return JsonResponse({
            'success': True,
            'account_exists': False
        })