from .models import Visit, Client, ClientType
from django.db.models import Q
from core.models import Business_Config
from datetime import datetime, time
import zoneinfo

def returnTrueOrFalse(value):
    if value == 'true':
        return True
    elif value == 'false':
        return False
    else:
        return None

def get_filtered_visits(request):
    user = request.user
    params = request.query_params
    queryset = Visit.objects.all()

    if user.role == 'ADMIN':
        is_deleted = params.get('is_deleted', 'False').capitalize()
        queryset = queryset.filter(is_deleted=is_deleted).select_related('client', 'deliverer')
    else:
        queryset = queryset.filter(is_deleted=False).select_related('client', 'deliverer')

    if params.get('sorting'):
        queryset = queryset.order_by(params.get('sorting'))
    else:
        queryset = queryset.order_by('-id')

    

    search_term = params.get('search_term')
    client_type = params.get('client_type')
    date_from = params.get('date_from')
    date_to = params.get('date_to')
    client_municipality = params.get('municipality')
    client_sector = params.get('sector')
    client_state = params.get('state')
    is_productive = returnTrueOrFalse(params.get('is_productive'))
    is_valid = returnTrueOrFalse(params.get('is_valid'))

    business_config = Business_Config.objects.first()
    tz_name = business_config.time_zone if business_config else 'UTC'
    tz = zoneinfo.ZoneInfo(tz_name)
    
    if date_from:
        try:
            dt_from = datetime.strptime(date_from, "%Y-%m-%d")
            date_from = datetime.combine(dt_from, time.min, tzinfo=tz)
        except (ValueError, TypeError):
            date_from = None
    
    if date_to:
        try:
            dt_to = datetime.strptime(date_to, "%Y-%m-%d")
            date_to = datetime.combine(dt_to, time.max, tzinfo=tz)
        except (ValueError, TypeError):
            date_to = None

    if search_term:
        queryset = queryset.filter(
            Q(client__code__icontains=search_term) | 
            Q(client__name__icontains=search_term) | 
            Q(client__address__icontains=search_term) |
            Q(client__neighborhood__icontains=search_term) |
            Q(client__market__icontains=search_term) | 
            Q(client__sector__icontains=search_term) | 
            Q(deliverer__first_name__icontains=search_term) | 
            Q(deliverer__last_name__icontains=search_term) 
        )

    if client_type:
        queryset = queryset.filter(client__client_type__id=client_type)
    
    if client_municipality:
        queryset = queryset.filter(client__municipality__icontains=client_municipality)
    
    if client_sector:
        queryset = queryset.filter(client__sector__icontains=client_sector)

    if client_state:
        queryset = queryset.filter(client__state__icontains=client_state)

    if date_from:
        queryset = queryset.filter(visited_at__gte=date_from)
    
    if date_to:
        queryset = queryset.filter(visited_at__lte=date_to)
    
    if is_productive is not None:
        queryset = queryset.filter(is_productive=is_productive)
    
    if is_valid is not None:
        queryset = queryset.filter(is_valid=is_valid)

    return queryset
    

def get_filtered_clients(request):
    user = request.user
    params = request.query_params
    queryset = Client.objects.all()

    if user.role == 'ADMIN':
        is_deleted = params.get('is_deleted', 'False').capitalize()
        queryset = queryset.filter(is_deleted=is_deleted).select_related('client_type')
    else:
        queryset = queryset.filter(is_deleted=False).select_related('client_type')

    sorting = params.get('sorting')
    code = params.get('code')
    client_type = params.get('client_type')
    sector = params.get('sector')
    market = params.get('market')
    municipality = params.get('municipality')
    state = params.get('state')
    address = params.get('address')
    name = params.get('name')
    is_active = returnTrueOrFalse(params.get('is_active'))

    if sorting:
        queryset = queryset.order_by(sorting)
    else:
        queryset = queryset.order_by('-id')
    
    if code:
        queryset = queryset.filter(code__icontains=code)
        
    if client_type:
        queryset = queryset.filter(client_type__id=client_type)
        
    if sector:
        queryset = queryset.filter(sector__icontains=sector)

    if market:
        queryset = queryset.filter(market__icontains=market)
        
    if municipality:
        queryset = queryset.filter(municipality__icontains=municipality)
        
    if state:
        queryset = queryset.filter(state__icontains=state)
            
    if address:
        queryset = queryset.filter(
            Q(address__icontains=address) |
            Q(neighborhood__icontains=address))

    if name:
        queryset = queryset.filter(name__icontains=name)

    if is_active is not None:
        queryset = queryset.filter(is_active=is_active)

    return queryset