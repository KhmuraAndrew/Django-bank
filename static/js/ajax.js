$(document).ready(function() {
    // Получение баланса счета
    $('.get-balance-btn').on('click', function() {
        const accountId = $(this).data('account-id');
        const $balanceElement = $(this).siblings('.balance');
        
        $balanceElement.html('<div class="loading"></div>');
        
        $.ajax({
            url: '/ajax/get_balance/',
            type: 'POST',
            data: {
                'account_id': accountId,
                'csrfmiddlewaretoken': $('[name=csrfmiddlewaretoken]').val()
            },
            success: function(response) {
                if (response.success) {
                    $balanceElement.text(response.balance + ' ' + response.currency);
                } else {
                    $balanceElement.text('Ошибка');
                    showAlert(response.message, 'error');
                }
            },
            error: function() {
                $balanceElement.text('Ошибка');
                showAlert('Произошла ошибка при получении баланса', 'error');
            }
        });
    });

    // Получение истории транзакций
    $('.get-transactions-btn').on('click', function() {
        const accountId = $(this).data('account-id');
        const $transactionsContainer = $(this).siblings('.transactions-list');
        
        $transactionsContainer.html('<div class="loading"></div>');
        
        $.ajax({
            url: '/ajax/get_transactions/',
            type: 'POST',
            data: {
                'account_id': accountId,
                'csrfmiddlewaretoken': $('[name=csrfmiddlewaretoken]').val()
            },
            success: function(response) {
                if (response.success) {
                    let html = '';
                    response.transactions.forEach(transaction => {
                        const amountClass = transaction.is_outgoing ? 'transaction-outgoing' : 'transaction-incoming';
                        const amountPrefix = transaction.is_outgoing ? '-' : '+';
                        
                        html += `
                            <div class="transaction-item">
                                <div class="transaction-date">${transaction.date}</div>
                                <div class="transaction-type">${transaction.type}</div>
                                <div class="transaction-amount ${amountClass}">
                                    ${amountPrefix}${transaction.amount}
                                </div>
                                <div class="transaction-description">${transaction.description}</div>
                            </div>
                        `;
                    });
                    $transactionsContainer.html(html);
                } else {
                    $transactionsContainer.text('Ошибка загрузки');
                    showAlert(response.message, 'error');
                }
            },
            error: function() {
                $transactionsContainer.text('Ошибка загрузки');
                showAlert('Произошла ошибка при загрузке транзакций', 'error');
            }
        });
    });

    // Форма перевода
    $('#transfer-form').on('submit', function(e) {
        e.preventDefault();
        
        const $form = $(this);
        const $submitBtn = $form.find('button[type="submit"]');
        const $alertContainer = $('#alert-container');
        
        $submitBtn.prop('disabled', true).text('Отправка...');
        $alertContainer.empty();
        
        $.ajax({
            url: $form.attr('action'),
            type: 'POST',
            data: $form.serialize(),
            success: function(response) {
                if (response.success) {
                    showAlert(response.message, 'success');
                    $form[0].reset();
                } else {
                    showAlert(response.message, 'error');
                }
            },
            error: function() {
                showAlert('Произошла ошибка при выполнении перевода', 'error');
            },
            complete: function() {
                $submitBtn.prop('disabled', false).text('Выполнить перевод');
            }
        });
    });

    function showAlert(message, type) {
        const alertClass = type === 'success' ? 'alert-success' : 'alert-error';
        const alertHtml = `<div class="alert ${alertClass}">${message}</div>`;
        $('#alert-container').html(alertHtml);
        
        setTimeout(() => {
            $('#alert-container').empty();
        }, 5000);
    }
});
// Валидация номера счета
$('#to_account').on('blur', function() {
    const accountNumber = $(this).val();
    const $validation = $('#account-validation');
    
    if (accountNumber.length === 16) {
        $validation.html('<div class="loading"></div> Проверка счета...');
        
        $.ajax({
            url: '/ajax/validate_account/',
            type: 'POST',
            data: {
                'account_number': accountNumber,
                'csrfmiddlewaretoken': $('[name=csrfmiddlewaretoken]').val()
            },
            success: function(response) {
                if (response.success && response.account_exists) {
                    $validation.html(`<div class="alert-success">Счет найден: ${response.account_type} (${response.user_name})</div>`);
                } else {
                    $validation.html('<div class="alert-error">Счет не найден. Проверьте номер счета.</div>');
                }
            },
            error: function() {
                $validation.html('<div class="alert-error">Ошибка проверки счета</div>');
            }
        });
    } else if (accountNumber.length > 0) {
        $validation.html('<div class="alert-error">Номер счета должен содержать 16 цифр</div>');
    } else {
        $validation.empty();
    }
});

// Обновление доступного баланса
$('#from_account').on('change', function() {
    const selectedOption = $(this).find('option:selected');
    const balance = selectedOption.data('balance') || 0;
    $('#available-balance').text(balance);
});

// Проверка суммы при вводе
$('#amount').on('input', function() {
    const amount = parseFloat($(this).val()) || 0;
    const availableBalance = parseFloat($('#available-balance').text()) || 0;
    const $submitBtn = $('#submit-btn');
    
    if (amount > availableBalance) {
        $submitBtn.prop('disabled', true).text('Недостаточно средств');
    } else {
        $submitBtn.prop('disabled', false).text('Выполнить перевод');
    }
});

// Загрузка последних транзакций
function loadRecentTransactions() {
    $.ajax({
        url: '/ajax/get_transactions/',
        type: 'POST',
        data: {
            'account_id': $('#from_account').val(),
            'csrfmiddlewaretoken': $('[name=csrfmiddlewaretoken]').val()
        },
        success: function(response) {
            if (response.success) {
                let html = '';
                response.transactions.slice(0, 5).forEach(transaction => {
                    const amountClass = transaction.is_outgoing ? 'transaction-outgoing' : 'transaction-incoming';
                    const amountPrefix = transaction.is_outgoing ? '-' : '+';
                    
                    html += `
                        <div class="transaction-item">
                            <div class="transaction-date">${transaction.date}</div>
                            <div class="transaction-description">${transaction.description}</div>
                            <div class="transaction-amount ${amountClass}">
                                ${amountPrefix}${transaction.amount} ₽
                            </div>
                        </div>
                    `;
                });
                $('#recent-transactions').html(html || '<p>Нет recent transactions</p>');
            }
        }
    });
}

$('#from_account').on('change', loadRecentTransactions);