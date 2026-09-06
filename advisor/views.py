from asgiref.sync import async_to_sync
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from .agent import is_llm_configured, run_advisor_chat
from .catalog import get_programs_by_ids, get_quiz_filters
from .serializers import (
    AdvisorChatRequestSerializer,
    AdvisorChatResponseSerializer,
)


class AdvisorFiltersView(APIView):
    """Справочники для квиза подбора программы."""

    authentication_classes: list = []
    permission_classes: list = []
    renderer_classes = [JSONRenderer]

    @extend_schema(
        summary='Справочники для квиза подбора',
        tags=['Подбор программы'],
    )
    def get(self, request, *args, **kwargs):
        return Response(get_quiz_filters())


class AdvisorChatView(APIView):
    """Чат-консультант по каталогу программ (PydanticAI)."""

    authentication_classes: list = []
    permission_classes: list = []
    renderer_classes = [JSONRenderer]

    @extend_schema(
        summary='Чат с консультантом по программам',
        request=AdvisorChatRequestSerializer,
        responses={200: AdvisorChatResponseSerializer},
        tags=['Подбор программы'],
    )
    def post(self, request, *args, **kwargs):
        if not is_llm_configured():
            return Response(
                {
                    'detail': (
                        'Чат-консультант временно недоступен: не настроен LLM. '
                        'Воспользуйтесь квизом «Подбор» на этой странице.'
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        serializer = AdvisorChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = serializer.validated_data['message']
        history = serializer.validated_data.get('history') or []

        try:
            reply, mentioned_ids = async_to_sync(run_advisor_chat)(
                message=message,
                history=history,
            )
        except Exception:
            return Response(
                {
                    'detail': (
                        'Не удалось получить ответ консультанта. '
                        'Попробуйте позже или воспользуйтесь квизом «Подбор».'
                    )
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        programs = get_programs_by_ids(mentioned_ids[:5])
        for item in programs:
            item['reason'] = ''

        return Response({'reply': reply, 'programs': programs})
