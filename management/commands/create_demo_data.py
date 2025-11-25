from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from bank_app.models import Account, Transaction, Card
from decimal import Decimal
import random

class Command(BaseCommand):
    help = 'Create demo data for bank application'

    def handle(self, *args, **options):
        # Создаем демо-пользователя
        user, created = User.objects.get_or_create(
            username='demo',
            defaults={
                'email': 'demo@humora.ru',
                'first_name': 'Демо',
                'last_name': 'Пользователь'
            }
        )
        if created:
            user.set_password('demo123')
            user.save()
            self.stdout.write(self.style.SUCCESS('Демо пользователь создан'))

        # Создаем счета
        accounts_data = [
            {'type': 'checking', 'balance': 150000.50},
            {'type': 'savings', 'balance': 50000.00},
            {'type': 'credit', 'balance': -25000.00},
        ]

        for acc_data in accounts_data:
            account, created = Account.objects.get_or_create(
                user=user,
                account_type=acc_data['type'],
                defaults={
                    'account_number': ''.join([str(random.randint(0, 9)) for _ in range(16)]),
                    'balance': Decimal(acc_data['balance']),
                    'currency': 'RUB'
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Счет {account.account_number} создан'))

        # Создаем демо-транзакции
        checking_account = Account.objects.filter(user=user, account_type='checking').first()
        savings_account = Account.objects.filter(user=user, account_type='savings').first()

        if checking_account and savings_account:
            transactions = [
                {'amount': 5000, 'type': 'deposit', 'desc': 'Пополнение через терминал'},
                {'amount': 1500, 'type': 'withdrawal', 'desc': 'Снятие в банкомате'},
                {'amount': 3000, 'type': 'transfer', 'desc': 'Перевод между счетами'},
            ]

            for trans in transactions:
                Transaction.objects.create(
                    from_account=checking_account if trans['type'] != 'deposit' else None,
                    to_account=checking_account if trans['type'] == 'deposit' else savings_account,
                    amount=Decimal(trans['amount']),
                    transaction_type=trans['type'],
                    description=trans['desc']
                )

            self.stdout.write(self.style.SUCCESS('Демо транзакции созданы'))

        # Создаем дополнительного пользователя для тестирования переводов
        other_user, created = User.objects.get_or_create(
            username='test_user',
            defaults={
                'email': 'test@humora.ru',
                'first_name': 'Тест',
                'last_name': 'Пользователь'
            }
        )
        if created:
            other_user.set_password('test123')
            other_user.save()
            self.stdout.write(self.style.SUCCESS('Тестовый пользователь создан'))

        # Создаем счет для тестового пользователя
        test_account, created = Account.objects.get_or_create(
            user=other_user,
            account_type='checking',
            defaults={
                'account_number': '1111222233334444',
                'balance': Decimal('50000.00'),
                'currency': 'RUB'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Тестовый счет {test_account.account_number} создан'))

        self.stdout.write(self.style.SUCCESS('Демо данные успешно созданы!'))
        self.stdout.write(self.style.SUCCESS('Логин: demo / Пароль: demo123'))
        self.stdout.write(self.style.SUCCESS('Логин для переводов: test_user / Пароль: test123'))