import sys
import os
import unittest
from unittest.mock import MagicMock, patch
from decimal import Decimal
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

# Добавляем корневую папку проекта в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services import create_wallet, process_operation, OperationType
from custom_exceptions import WalletCreationError, InvalidOperationTypeError, WalletNotFoundError, \
    InsufficientFundsError


# Тесты для WalletService
class TestWalletService(unittest.TestCase):
    @patch("services.AsyncSession")  # Мокаем AsyncSession
    async def test_create_wallet_success(self, MockSession: Any) -> None:
        """
        Тест для проверки успешного создания кошелька.
        Проверяет, что кошелёк создаётся и возвращается правильный UUID и баланс.
        """
        mock_session = MagicMock(spec=AsyncSession)
        MockSession.return_value = mock_session
        mock_session.execute.return_value.fetchone.return_value = (uuid4(), Decimal("100.00"))

        result = await create_wallet(mock_session, Decimal("100.00"))
        self.assertIn("wallet_uuid", result)
        self.assertEqual(result["balance"], 100.00)

    @patch("services.AsyncSession")
    async def test_create_wallet_failure(self, MockSession: Any) -> None:
        """
        Тест для проверки неудачного создания кошелька.
        Проверяет, что при ошибке создания кошелька выбрасывается исключение WalletCreationError.
        """
        mock_session = MagicMock(spec=AsyncSession)
        MockSession.return_value = mock_session
        mock_session.execute.return_value.fetchone.return_value = None

        with self.assertRaises(WalletCreationError):
            await create_wallet(mock_session, Decimal("100.00"))

    @patch("services.AsyncSession")
    async def test_process_operation_deposit_success(self, MockSession: Any) -> None:
        """
        Тест для проверки успешного депозита на кошелёк.
        Проверяет, что баланс увеличивается при депозите.
        """
        mock_session = MagicMock(spec=AsyncSession)
        MockSession.return_value = mock_session
        wallet_uuid = uuid4()
        mock_session.execute.return_value.fetchone.return_value = (Decimal("200.00"))

        result = await process_operation(mock_session, wallet_uuid, OperationType.DEPOSIT, Decimal("100.00"))
        self.assertEqual(result, Decimal("200.00"))

    @patch("services.AsyncSession")
    async def test_process_operation_withdraw_success(self, MockSession: Any) -> None:
        """
        Тест для проверки успешного снятия средств с кошелька.
        Проверяет, что баланс уменьшается при снятии средств.
        """
        mock_session = MagicMock(spec=AsyncSession)
        MockSession.return_value = mock_session
        wallet_uuid = uuid4()
        mock_session.execute.return_value.fetchone.return_value = (Decimal("50.00"))

        result = await process_operation(mock_session, wallet_uuid, OperationType.WITHDRAW, Decimal("50.00"))
        self.assertEqual(result, Decimal("50.00"))

    @patch("services.AsyncSession")
    async def test_process_operation_withdraw_insufficient_funds(self, MockSession: Any) -> None:
        """
        Тест для проверки попытки снятия средств при недостаточности баланса.
        Ожидается исключение InsufficientFundsError.
        """
        mock_session = MagicMock(spec=AsyncSession)
        MockSession.return_value = mock_session
        wallet_uuid = uuid4()
        mock_session.execute.return_value.fetchone.return_value = None
        mock_session.execute.return_value.fetchone.return_value = (wallet_uuid, Decimal("10.00"))

        with self.assertRaises(InsufficientFundsError):
            await process_operation(mock_session, wallet_uuid, OperationType.WITHDRAW, Decimal("50.00"))

    @patch("services.AsyncSession")
    async def test_process_operation_invalid_operation(self, MockSession: Any) -> None:
        """
        Тест для проверки ошибки при неверном типе операции.
        Ожидается исключение InvalidOperationTypeError.
        """
        mock_session = MagicMock(spec=AsyncSession)
        MockSession.return_value = mock_session

        with self.assertRaises(InvalidOperationTypeError):
            await process_operation(mock_session, uuid4(), "INVALID", Decimal("50.00"))



    @patch("services.AsyncSession")
    async def test_process_operation_deposit_balance(self, MockSession: Any) -> None:
        """
        Тест для проверки правильности депозита на кошелёк.
        Проверяет, что баланс корректно увеличивается при депозите.
        """
        mock_session = MagicMock(spec=AsyncSession)
        MockSession.return_value = mock_session
        wallet_uuid = uuid4()

        # Начальный баланс 0
        mock_session.execute.return_value.fetchone.return_value = (Decimal("0.00"))

        # Депозит на 100
        result = await process_operation(mock_session, wallet_uuid, OperationType.DEPOSIT, Decimal("100.00"))
        self.assertEqual(result, Decimal("100.00"))

        # Теперь депозит на 50
        result = await process_operation(mock_session, wallet_uuid, OperationType.DEPOSIT, Decimal("50.00"))
        self.assertEqual(result, Decimal("150.00"))

    @patch("services.AsyncSession")
    async def test_process_operation_withdraw_balance(self, MockSession: Any) -> None:
        """
        Тест для проверки правильности снятия средств с кошелька.
        Проверяет, что баланс корректно уменьшается при снятии средств.
        """
        mock_session = MagicMock(spec=AsyncSession)
        MockSession.return_value = mock_session
        wallet_uuid = uuid4()

        # Начальный баланс 150
        mock_session.execute.return_value.fetchone.return_value = (Decimal("150.00"))

        # Снимаем 50
        result = await process_operation(mock_session, wallet_uuid, OperationType.WITHDRAW, Decimal("50.00"))
        self.assertEqual(result, Decimal("100.00"))

        # Снимаем еще 30
        result = await process_operation(mock_session, wallet_uuid, OperationType.WITHDRAW, Decimal("30.00"))
        self.assertEqual(result, Decimal("70.00"))

    @patch("services.AsyncSession")
    async def test_process_operation_withdraw_insufficient_balance(self, MockSession: Any) -> None:
        """
        Тест для проверки ошибки недостаточности средств при попытке снять деньги.
        Ожидается исключение InsufficientFundsError.
        """
        mock_session = MagicMock(spec=AsyncSession)
        MockSession.return_value = mock_session
        wallet_uuid = uuid4()

        # Баланс 30
        mock_session.execute.return_value.fetchone.return_value = (Decimal("30.00"))

        # Пытаемся снять 50, но средств недостаточно
        with self.assertRaises(InsufficientFundsError):
            await process_operation(mock_session, wallet_uuid, OperationType.WITHDRAW, Decimal("50.00"))

    @patch("services.AsyncSession")
    async def test_process_operation_withdraw_zero_balance(self, MockSession: Any) -> None:
        """
        Тест для проверки ошибки при снятии средств с нулевым балансом.
        Ожидается исключение InsufficientFundsError.
        """
        mock_session = MagicMock(spec=AsyncSession)
        MockSession.return_value = mock_session
        wallet_uuid = uuid4()

        # Баланс 0
        mock_session.execute.return_value.fetchone.return_value = (Decimal("0.00"))

        # Пытаемся снять 10, но средств недостаточно
        with self.assertRaises(InsufficientFundsError):
            await process_operation(mock_session, wallet_uuid, OperationType.WITHDRAW, Decimal("10.00"))

    @patch("services.AsyncSession")
    async def test_process_operation_deposit_and_withdraw_zero_balance(self, MockSession: Any) -> None:
        """
        Тест для проверки последовательных операций депозита и снятия при нулевом балансе.
        Проверяется правильность баланса после депозита и снятия средств.
        """
        mock_session = MagicMock(spec=AsyncSession)
        MockSession.return_value = mock_session
        wallet_uuid = uuid4()

        # Начальный баланс 0
        mock_session.execute.return_value.fetchone.return_value = (Decimal("0.00"))

        # Депозит на 100
        result = await process_operation(mock_session, wallet_uuid, OperationType.DEPOSIT, Decimal("100.00"))
        self.assertEqual(result, Decimal("100.00"))

        # Снятие 50
        result = await process_operation(mock_session, wallet_uuid, OperationType.WITHDRAW, Decimal("50.00"))
        self.assertEqual(result, Decimal("50.00"))

        # Снятие оставшихся 50
        result = await process_operation(mock_session, wallet_uuid, OperationType.WITHDRAW, Decimal("50.00"))
        self.assertEqual(result, Decimal("0.00"))

        # Пытаемся снять с нулевого баланса
        with self.assertRaises(InsufficientFundsError):
            await process_operation(mock_session, wallet_uuid, OperationType.WITHDRAW, Decimal("10.00"))


# Запуск тестов
if __name__ == "__main__":
    unittest.main()
