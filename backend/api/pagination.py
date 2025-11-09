from __future__ import annotations

from typing import Optional

from rest_framework.pagination import PageNumberPagination


class LimitPageNumberPagination(PageNumberPagination):
    """Page-number pagination with a customizable `limit` parameter."""

    page_size_query_param = "limit"
    max_page_size = 6

    def get_page_size(self, request) -> Optional[int]:
        limit = self._sanitize_limit(request)
        if limit is None:
            return super().get_page_size(request)
        return min(limit, self.max_page_size)

    def _sanitize_limit(self, request) -> Optional[int]:
        raw_limit = request.query_params.get(self.page_size_query_param)
        if raw_limit in (None, ""):
            return None
        try:
            return int(raw_limit)
        except (TypeError, ValueError):
            return None
