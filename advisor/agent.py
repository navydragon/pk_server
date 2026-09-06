from __future__ import annotations

from dataclasses import dataclass, field

from asgiref.sync import sync_to_async
from django.conf import settings
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.profiles.openai import OpenAIModelProfile
from pydantic_ai.providers.openai import OpenAIProvider

from .catalog import get_program, list_directions, search_programs


SYSTEM_PROMPT = """
Ты — консультант по программам повышения квалификации и профессиональной переподготовки
Института экономики и финансов РУТ (МИИТ).

Правила:
1. Рекомендуй ТОЛЬКО программы из инструментов list_directions / search_programs / get_program.
2. Не выдумывай названия курсов, цены, даты, форматы и id.
3. Если подходящих программ нет — честно скажи об этом и предложи оставить заявку или заказать звонок.
4. Отвечай по-русски, кратко и по делу (2–6 предложений).
5. В конце ответа перечисли 1–3 подходящие программы с id и краткой причиной выбора.
6. Если пользователь не уточнил цель/формат/бюджет — задай 1–2 уточняющих вопроса, но всё равно покажи ближайшие варианты из каталога.
""".strip()


@dataclass
class AdvisorDeps:
    mentioned_program_ids: list[int] = field(default_factory=list)

    def track(self, programs: list[dict]) -> list[dict]:
        for item in programs:
            pid = item.get('id')
            if isinstance(pid, int) and pid not in self.mentioned_program_ids:
                self.mentioned_program_ids.append(pid)
        return programs


def is_llm_configured() -> bool:
    return bool(getattr(settings, 'LLM_API_KEY', '') and getattr(settings, 'LLM_MODEL', ''))


def build_model() -> OpenAIChatModel:
    provider = OpenAIProvider(
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL or None,
    )
    return OpenAIChatModel(
        settings.LLM_MODEL,
        provider=provider,
        profile=OpenAIModelProfile(openai_supports_strict_tool_definition=False),
    )


advisor_agent = Agent(
    model=None,  # set per-run when configured
    deps_type=AdvisorDeps,
    system_prompt=SYSTEM_PROMPT,
)


@advisor_agent.tool
async def list_catalog_directions(ctx: RunContext[AdvisorDeps]) -> list[dict]:
    """Вернуть список активных направлений обучения."""
    return await sync_to_async(list_directions)()


@advisor_agent.tool
async def search_catalog_programs(
    ctx: RunContext[AdvisorDeps],
    query: str = '',
    direction: str = '',
    program_type: str = '',
    learning_format: str = '',
    max_hours: int | None = None,
    max_cost: int | None = None,
) -> list[dict]:
    """
    Найти активные программы в каталоге.
    program_type: pk (повышение квалификации), pp (переподготовка) или пусто.
    """
    programs = await sync_to_async(search_programs)(
        query=query,
        direction=direction,
        program_type=program_type,
        learning_format=learning_format,
        max_hours=max_hours,
        max_cost=max_cost,
        limit=8,
    )
    return ctx.deps.track(programs)


@advisor_agent.tool
async def get_catalog_program(ctx: RunContext[AdvisorDeps], program_id: int) -> dict:
    """Получить карточку активной программы по id."""
    program = await sync_to_async(get_program)(program_id)
    if not program:
        return {'error': f'Программа id={program_id} не найдена или неактивна'}
    ctx.deps.track([program])
    return program


async def run_advisor_chat(
    message: str,
    history: list[dict] | None = None,
) -> tuple[str, list[int]]:
    if not is_llm_configured():
        raise RuntimeError('LLM is not configured')

    model = build_model()
    deps = AdvisorDeps()

    prompt_parts: list[str] = []
    for item in (history or [])[-12:]:
        role = item.get('role')
        content = (item.get('content') or '').strip()
        if not content or role not in ('user', 'assistant'):
            continue
        label = 'Пользователь' if role == 'user' else 'Консультант'
        prompt_parts.append(f'{label}: {content}')
    prompt_parts.append(f'Пользователь: {message.strip()}')
    prompt = '\n'.join(prompt_parts)

    result = await advisor_agent.run(prompt, deps=deps, model=model)
    reply = result.output if isinstance(result.output, str) else str(result.output)
    return reply, deps.mentioned_program_ids
