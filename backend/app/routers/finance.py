import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.finance import Category, FinanceAccount, Transaction, TransactionType
from app.models.user import User
from app.schemas.finance import AccountCreate, AccountResponse, CategoryCreate, CategoryResponse, TransactionCreate, TransactionResponse

router = APIRouter(prefix="/finance", tags=["finance"])

DEFAULT_CATEGORIES = {
    "expense": [
        "Food & Dining",
        "Groceries",
        "Transport",
        "Shopping",
        "Bills & Utilities",
        "Rent",
        "Health",
        "Education",
        "Entertainment",
        "Travel",
        "Family",
        "Other Expense",
    ],
    "income": [
        "Salary",
        "Business",
        "Freelance",
        "Investment",
        "Gift",
        "Other Income",
    ],
}


@router.post("/accounts", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(payload: AccountCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> AccountResponse:
    account = FinanceAccount(user_id=user.id, name=payload.name.strip(), account_type=payload.account_type, currency=payload.currency.upper(), opening_balance=payload.opening_balance)
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return AccountResponse.model_validate(account)


@router.get("/accounts", response_model=list[AccountResponse])
async def list_accounts(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> list[AccountResponse]:
    result = await db.execute(select(FinanceAccount).where(FinanceAccount.user_id == user.id).order_by(FinanceAccount.created_at.asc()))
    return [AccountResponse.model_validate(row) for row in result.scalars().all()]


@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(payload: CategoryCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> CategoryResponse:
    category = Category(user_id=user.id, name=payload.name.strip(), transaction_type=payload.transaction_type)
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return CategoryResponse.model_validate(category)


@router.get("/categories", response_model=list[CategoryResponse])
async def list_categories(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> list[CategoryResponse]:
    result = await db.execute(select(Category).where(Category.user_id == user.id).order_by(Category.name.asc()))
    return [CategoryResponse.model_validate(row) for row in result.scalars().all()]


@router.post("/transactions", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(payload: TransactionCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> TransactionResponse:
    account = await db.scalar(select(FinanceAccount).where(FinanceAccount.id == payload.account_id, FinanceAccount.user_id == user.id))
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    if payload.category_id is not None:
        category = await db.scalar(select(Category).where(Category.id == payload.category_id, Category.user_id == user.id))
        if category is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    transaction = Transaction(
        user_id=user.id,
        account_id=payload.account_id,
        category_id=payload.category_id,
        transaction_type=payload.transaction_type,
        amount=payload.amount,
        occurred_on=payload.occurred_on,
        merchant=payload.merchant.strip() if payload.merchant else None,
        note=payload.note,
    )
    db.add(transaction)
    await db.commit()
    await db.refresh(transaction)
    return TransactionResponse.model_validate(transaction)


@router.get("/transactions", response_model=list[TransactionResponse])
async def list_transactions(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> list[TransactionResponse]:
    result = await db.execute(select(Transaction).where(Transaction.user_id == user.id).order_by(Transaction.occurred_on.desc(), Transaction.created_at.desc()))
    return [TransactionResponse.model_validate(row) for row in result.scalars().all()]


@router.delete("/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(transaction_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> None:
    transaction = await db.scalar(select(Transaction).where(Transaction.id == transaction_id, Transaction.user_id == user.id))
    if transaction is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    await db.delete(transaction)
    await db.commit()


@router.post("/categories/bootstrap", response_model=list[CategoryResponse])
async def bootstrap_categories(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[CategoryResponse]:
    existing_rows = await db.execute(
        select(Category).where(Category.user_id == user.id)
    )
    existing = list(existing_rows.scalars().all())
    existing_keys = {
        (row.name.strip().lower(), row.transaction_type.value)
        for row in existing
    }

    created: list[Category] = []
    for tx_type, names in DEFAULT_CATEGORIES.items():
        for name in names:
            key = (name.lower(), tx_type)
            if key in existing_keys:
                continue
            category = Category(
                user_id=user.id,
                name=name,
                transaction_type=TransactionType(tx_type),
            )
            db.add(category)
            created.append(category)

    if created:
        await db.commit()

    result = await db.execute(
        select(Category)
        .where(Category.user_id == user.id)
        .order_by(Category.transaction_type.asc(), Category.name.asc())
    )
    return [
        CategoryResponse.model_validate(row)
        for row in result.scalars().all()
    ]
