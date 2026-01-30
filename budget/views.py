from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from order.models import Order

from .forms import BudgetForm, ShoppingListItemForm
from .models import Budget, ShoppingListItem


@login_required
def budget_dashboard(request):
    budget = Budget.get_active_for_user(request.user)
    if budget:
        return redirect('budget:view-budget', budget_id=budget.id)
    return redirect('budget:set-budget')


@login_required
def set_budget(request):
    if request.method == 'POST':
        form = BudgetForm(request.POST)
        if form.is_valid():
            budget = form.save(commit=False)
            budget.user = request.user
            budget.save()
            messages.success(request, 'Budget saved. Start adding items to your plan!')
            return redirect('budget:view-budget', budget_id=budget.id)
    else:
        form = BudgetForm()
    return render(request, 'budget/set_budget.html', {'form': form})


@login_required
def view_budget(request, budget_id):
    budget = get_object_or_404(Budget, id=budget_id, user=request.user)
    items = budget.items.select_related('product', 'product__category').all()
    add_form = ShoppingListItemForm()

    category_totals = {}
    for item in items:
        category_name = item.product.category.name
        category_totals[category_name] = category_totals.get(category_name, Decimal('0.00')) + item.total_cost

    discounted_items = [item for item in items if item.product.discount_price]
    affordable_discounts = [
        item for item in discounted_items if item.total_cost <= max(budget.remaining_budget, Decimal('0.00'))
    ]

    budgets = Budget.objects.filter(user=request.user).order_by('-created_at')

    context = {
        'budget': budget,
        'items': items,
        'add_form': add_form,
        'category_totals': category_totals,
        'discounted_items': discounted_items,
        'affordable_discounts': affordable_discounts,
        'budgets': budgets,
    }
    return render(request, 'budget/view_budget.html', context)


@login_required
def add_to_budget(request, budget_id):
    budget = get_object_or_404(Budget, id=budget_id, user=request.user)
    if request.method != 'POST':
        return redirect('budget:view-budget', budget_id=budget.id)

    form = ShoppingListItemForm(request.POST)
    if form.is_valid():
        product = form.cleaned_data['product']
        quantity = form.cleaned_data['quantity']
        item, created = ShoppingListItem.objects.get_or_create(budget=budget, product=product)
        if created:
            item.quantity = quantity
        else:
            item.quantity += quantity
        item.save()
        messages.success(request, 'Item added to your shopping list.')
    else:
        messages.error(request, 'Unable to add that item. Please try again.')
    return redirect('budget:view-budget', budget_id=budget.id)


@login_required
def remove_from_budget(request, budget_id, item_id):
    budget = get_object_or_404(Budget, id=budget_id, user=request.user)
    item = get_object_or_404(ShoppingListItem, id=item_id, budget=budget)
    item.delete()
    messages.info(request, 'Item removed from your shopping list.')
    return redirect('budget:view-budget', budget_id=budget.id)


@login_required
def add_from_cart(request, budget_id):
    budget = get_object_or_404(Budget, id=budget_id, user=request.user)
    order = Order.objects.filter(user=request.user, is_ordered=False).first()
    if not order:
        messages.warning(request, 'You have no active cart to import.')
        return redirect('budget:view-budget', budget_id=budget.id)

    for order_item in order.items.all():
        item, created = ShoppingListItem.objects.get_or_create(
            budget=budget,
            product=order_item.item,
        )
        if created:
            item.quantity = order_item.quantity
        else:
            item.quantity += order_item.quantity
        item.save()

    messages.success(request, 'Cart items added to your budget plan.')
    return redirect('budget:view-budget', budget_id=budget.id)


@login_required
def duplicate_budget(request, budget_id):
    original = get_object_or_404(Budget, id=budget_id, user=request.user)
    budget = Budget.objects.create(user=request.user, total_budget=original.total_budget)
    for item in original.items.all():
        ShoppingListItem.objects.create(
            budget=budget,
            product=item.product,
            quantity=item.quantity,
        )
    messages.success(request, 'Budget duplicated. You can now adjust it for a new trip.')
    return redirect('budget:view-budget', budget_id=budget.id)
