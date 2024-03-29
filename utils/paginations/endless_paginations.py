from dateutil import parser
from django.conf import settings
from rest_framework.pagination import BasePagination
from rest_framework.response import Response


class EndlessPagination(BasePagination):
    page_size = 20
    has_next_page = False

    def paginate_ordered_list(self, reversed_ordered_list, request):
        if 'created_at__gt' in request.query_params:
            created_at__gt = parser.isoparse(request.query_params['created_at__gt'])
            objects = []
            for obj in reversed_ordered_list:
                if obj.created_at <= created_at__gt:
                    break
                objects.append(obj)

            return objects

        index = 0
        if 'created_at__lt' in request.query_params:
            created_at__lt = parser.isoparse(request.query_params['created_at__lt'])
            for index, obj in enumerate(reversed_ordered_list):
                if obj.created_at < created_at__lt:
                    break
            else:
                reversed_ordered_list = []

        self.has_next_page = len(reversed_ordered_list) > index + self.page_size
        return reversed_ordered_list[index: index + self.page_size]

    def get_paginated_cached_list_in_redis(self, cached_list, request):
        paginated_list = self.paginate_ordered_list(cached_list, request)
        if 'created_at__gt' in request.query_params:
            return paginated_list

        if self.has_next_page:
            return paginated_list
        if len(paginated_list) < settings.REDIS_LIST_LENGTH_LIMIT:
            return paginated_list
        return None

    def paginate_queryset(self, queryset, request, view=None):
        if 'created_at__gt' in request.query_params:
            queryset = queryset.filter(
                created_at__gt=request.query_params['created_at__gt']
            )
            return queryset.order_by('-created_at')

        if 'created_at__lt' in request.query_params:
            queryset = queryset.filter(
                created_at__lt=request.query_params['created_at__lt']
            )

        queryset = queryset.order_by('-created_at')[:self.page_size + 1]
        self.has_next_page = len(queryset) > self.page_size
        return queryset[:self.page_size]

    def get_paginated_response(self, data):
        return Response({
            'has_next_page': self.has_next_page,
            'results': data
        })
