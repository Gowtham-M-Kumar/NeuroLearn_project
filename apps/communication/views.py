from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import AACCategory, AACSymbol

@login_required
def aac_dashboard(request):
    """
    Main AAC Dashboard.
    Zone 1: Quick Needs (Symbols marked as is_quick_need)
    Zone 3: Categories (All categories)
    """
    quick_needs = AACSymbol.objects.filter(is_quick_need=True).order_by('order')
    categories = AACCategory.objects.all()
    
    context = {
        'quick_needs': quick_needs,
        'categories': categories,
    }
    return render(request, 'communication/dashboard.html', context)

@login_required
def aac_category_detail(request, category_id):
    """
    Zone 3 Detail: Shows all symbols for a specific category.
    """
    category = get_object_or_404(AACCategory, id=category_id)
    symbols = category.symbols.all()
    
    context = {
        'category': category,
        'symbols': symbols,
    }
    return render(request, 'communication/category_detail.html', context)

@login_required
def aac_learning_mode(request, symbol_id):
    """
    Zone 2: Deepdive into a specific symbol (Picture -> Word -> Association).
    """
    symbol = get_object_or_404(AACSymbol, id=symbol_id)
    
    context = {
        'symbol': symbol,
    }
    return render(request, 'communication/learning_mode.html', context)

@login_required
def aac_type_mode(request):
    return render(request, 'communication/type_mode.html')
