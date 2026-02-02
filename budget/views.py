from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from order.models import Order
from foodCreate.models import Products

from .forms import (
    BudgetForm,
    BudgetTemplateForm,
    BudgetTemplateItemForm,
    ShoppingListItemQuantityForm,
    ShoppingListItemForm,
)
from .models import Budget, BudgetTemplate, BudgetTemplateItem, ShoppingListItem
from .utils import build_price_predictions, build_savings_suggestions


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
    product_options = list(Products.objects.filter(is_active=True).order_by('title')[:200])
    template_form = BudgetTemplateForm()

    category_totals = {}
    for item in items:
        if item.product:
            category_name = item.product.category.name
            category_totals[category_name] = category_totals.get(category_name, Decimal('0.00')) + item.total_cost

    discounted_items = [item for item in items if item.product and item.product.discount_price]
    affordable_discounts = [
        item for item in discounted_items if item.total_cost <= max(budget.remaining_budget, Decimal('0.00'))
    ]

    remaining_budget = budget.remaining_budget
    item_product_ids = [item.product_id for item in items if item.product_id]
    suggested_discounts = []
    if remaining_budget > 0:
        suggested_discounts = list(
            Products.objects.filter(
                discount_price__isnull=False,
                discount_price__lte=remaining_budget,
            )
            .exclude(id__in=item_product_ids)
            .order_by('discount_price')[:5]
        )

    budgets = Budget.objects.filter(user=request.user).order_by('-created_at')
    templates = BudgetTemplate.objects.filter(user=request.user).order_by('-updated_at')
    active_order = Order.objects.filter(user=request.user, is_ordered=False).first()
    price_predictions = build_price_predictions(items)
    savings_suggestions = build_savings_suggestions(items, remaining_budget)
    for item in items:
        item.suggestions = []
        if item.product or not item.name:
            continue
        item.suggestions = list(
            Products.objects.filter(title__icontains=item.name, is_active=True)
            .order_by('price')[:3]
        )

    context = {
        'budget': budget,
        'items': items,
        'add_form': add_form,
        'product_options': product_options,
        'category_totals': category_totals,
        'discounted_items': discounted_items,
        'affordable_discounts': affordable_discounts,
        'suggested_discounts': suggested_discounts,
        'budgets': budgets,
        'templates': templates,
        'template_form': template_form,
        'active_order': active_order,
        'price_predictions': price_predictions,
        'savings_suggestions': savings_suggestions,
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
        name = form.cleaned_data.get('name', '')
        quantity = form.cleaned_data['quantity']
        item, created = ShoppingListItem.objects.get_or_create(budget=budget, product=product, name=name)
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
def edit_budget_item(request, budget_id, item_id):
    budget = get_object_or_404(Budget, id=budget_id, user=request.user)
    item = get_object_or_404(ShoppingListItem, id=item_id, budget=budget)
    if request.method == 'POST':
        form = ShoppingListItemForm(request.POST, instance=item)
        if form.is_valid():
            product = form.cleaned_data.get('product')
            if product and ShoppingListItem.objects.filter(budget=budget, product=product).exclude(id=item.id).exists():
                messages.warning(
                    request,
                    'That product is already in your shopping list. Please update the quantity instead.',
                )
                return redirect('budget:view-budget', budget_id=budget.id)
            form.save()
            messages.success(request, 'Shopping list item updated.')
            return redirect('budget:view-budget', budget_id=budget.id)
    else:
        form = ShoppingListItemForm(instance=item)
    return render(
        request,
        'budget/edit_item.html',
        {'budget': budget, 'form': form, 'item': item},
    )


@login_required
@require_GET
def product_autocomplete(request):
    query = request.GET.get("q", "").strip()
    if not query:
        return JsonResponse({"results": []})
    products = (
        Products.objects.filter(is_active=True, title__icontains=query)
        .order_by("title")[:10]
    )
    results = [{"id": product.id, "title": product.title} for product in products]
    return JsonResponse({"results": results})


@login_required
def remove_from_budget(request, budget_id, item_id):
    budget = get_object_or_404(Budget, id=budget_id, user=request.user)
    item = get_object_or_404(ShoppingListItem, id=item_id, budget=budget)
    item.delete()
    messages.info(request, 'Item removed from your shopping list.')
    return redirect('budget:view-budget', budget_id=budget.id)


@login_required
def update_budget_item_quantity(request, budget_id, item_id):
    budget = get_object_or_404(Budget, id=budget_id, user=request.user)
    item = get_object_or_404(ShoppingListItem, id=item_id, budget=budget)
    if request.method != 'POST':
        return redirect('budget:view-budget', budget_id=budget.id)

    form = ShoppingListItemQuantityForm(request.POST, instance=item)
    if form.is_valid():
        updated_item = form.save()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'quantity': updated_item.quantity,
                'total_cost': str(updated_item.total_cost),
                'unit_price': str(updated_item.unit_price),
            })
        messages.success(request, 'Quantity updated.')
    else:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Unable to update quantity.'}, status=400)
        messages.error(request, 'Unable to update quantity. Please try again.')
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
            name="",
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
            name=item.name,
            quantity=item.quantity,
        )
    messages.success(request, 'Budget duplicated. You can now adjust it for a new trip.')
    return redirect('budget:view-budget', budget_id=budget.id)


@login_required
def create_template(request, budget_id):
    budget = get_object_or_404(Budget, id=budget_id, user=request.user)
    if request.method != 'POST':
        return redirect('budget:view-budget', budget_id=budget.id)

    form = BudgetTemplateForm(request.POST)
    if form.is_valid():
        template = form.save(commit=False)
        template.user = request.user
        template.save()
        for item in budget.items.all():
            if not item.product:
                continue
            BudgetTemplateItem.objects.create(
                template=template,
                product=item.product,
                quantity=item.quantity,
            )
        messages.success(request, 'Template created from your current budget.')
    else:
        messages.error(request, 'Please provide a template name.')
    return redirect('budget:view-budget', budget_id=budget.id)


@login_required
def add_template_item(request, template_id):
    template = get_object_or_404(BudgetTemplate, id=template_id, user=request.user)
    if request.method != 'POST':
        return redirect('budget:view-template', template_id=template.id)

    form = BudgetTemplateItemForm(request.POST)
    if form.is_valid():
        product = form.cleaned_data['product']
        quantity = form.cleaned_data['quantity']
        item, created = BudgetTemplateItem.objects.get_or_create(template=template, product=product)
        if created:
            item.quantity = quantity
        else:
            item.quantity += quantity
        item.save()
        messages.success(request, 'Template item added.')
    else:
        messages.error(request, 'Unable to add that item.')
    return redirect('budget:view-template', template_id=template.id)


@login_required
def view_template(request, template_id):
    template = get_object_or_404(BudgetTemplate, id=template_id, user=request.user)
    templates = BudgetTemplate.objects.filter(user=request.user).order_by('-updated_at')
    item_form = BudgetTemplateItemForm()
    return render(
        request,
        'budget/view_template.html',
        {
            'template': template,
            'templates': templates,
            'item_form': item_form,
        },
    )


@login_required
def remove_template_item(request, template_id, item_id):
    template = get_object_or_404(BudgetTemplate, id=template_id, user=request.user)
    item = get_object_or_404(BudgetTemplateItem, id=item_id, template=template)
    item.delete()
    messages.info(request, 'Template item removed.')
    return redirect('budget:view-template', template_id=template.id)


@login_required
def apply_template(request, budget_id, template_id):
    budget = get_object_or_404(Budget, id=budget_id, user=request.user)
    template = get_object_or_404(BudgetTemplate, id=template_id, user=request.user)
    for template_item in template.items.all():
        item, created = ShoppingListItem.objects.get_or_create(
            budget=budget,
            product=template_item.product,
            name="",
        )
        if created:
            item.quantity = template_item.quantity
        else:
            item.quantity += template_item.quantity
        item.save()
    messages.success(request, 'Template applied to your budget.')
    return redirect('budget:view-budget', budget_id=budget.id)
