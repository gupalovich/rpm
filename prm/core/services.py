def get_token():
    from prm.tokens.models import Token

    return Token.objects.first()


def create_transaction(*, buyer, token_amount):
    from prm.tokens.models import TokenTransaction

    token = get_token()
    transaction = TokenTransaction.objects.create(
        buyer=buyer, token_round=token.active_round, amount=token_amount
    )
    return transaction


def update_total_amount_sold_for_active_round():
    token = get_token()
    token.active_round.set_total_amount_sold()
    token.active_round.save()


# def set_total_amount_sold(self) -> None:
#     """На основе транзакций раунда, подсчитать кол-во проданных токенов"""
#     amount_sold = self.transactions.filter(status="success").aggregate(
#         total=models.Sum("amount")
#     )["total"]
#     if amount_sold:
#         self.total_amount_sold = amount_sold


# def test_set_total_amount_sold(self):
#     token = TokenFactory()
#     token_round = token.active_round
#     TokenTransactionFactory.create_batch(5, token_round=token_round, status=)
#     # Tests
#     token_round.set_total_amount_sold()
#     self.assertEqual(
#         token_round.total_amount_sold,
#         token_round.transactions.aggregate(total=Sum("amount"))["total"],
#     )
#     self.assertIsInstance(token_round.total_amount_sold, int)
