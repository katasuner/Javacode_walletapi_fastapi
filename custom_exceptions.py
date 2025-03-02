class WalletNotFoundError(Exception):
    """Исключение, если кошелёк не найден"""
    pass


class InsufficientFundsError(Exception):
    """Исключение, если недостаточно средств для списания"""
    pass


class WalletCreationError(Exception):
    """Ошибка создания кошелька."""
    pass


class InvalidOperationTypeError(Exception):
    """Недопустимый тип операции."""
    pass