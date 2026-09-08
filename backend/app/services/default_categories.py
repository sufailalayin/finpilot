from app.models.finance import Category, TransactionType


DEFAULT_CATEGORIES = [
    ("Salary", TransactionType.INCOME),
    ("Business Income", TransactionType.INCOME),
    ("Other Income", TransactionType.INCOME),
    ("Food & Dining", TransactionType.EXPENSE),
    ("Groceries", TransactionType.EXPENSE),
    ("Transport", TransactionType.EXPENSE),
    ("Shopping", TransactionType.EXPENSE),
    ("Bills & Utilities", TransactionType.EXPENSE),
    ("Rent", TransactionType.EXPENSE),
    ("Health", TransactionType.EXPENSE),
    ("Education", TransactionType.EXPENSE),
    ("Entertainment", TransactionType.EXPENSE),
    ("Travel", TransactionType.EXPENSE),
    ("Other Expense", TransactionType.EXPENSE),
]


def build_default_categories(user_id):
    return [
        Category(user_id=user_id, name=name, transaction_type=transaction_type)
        for name, transaction_type in DEFAULT_CATEGORIES
    ]
