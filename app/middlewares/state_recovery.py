# from typing import Any, Awaitable, Callable
# from aiogram import BaseMiddleware
# from aiogram.types import TelegramObject
# from aiogram.fsm.storage.redis import RedisStorage
#
#
# class StateRecoveryMiddleware(BaseMiddleware):
#     async def __call__(
#             self,
#             handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
#             event: TelegramObject,
#             data: dict[str, Any]
#     ) -> Any:
#         if not hasattr(event, 'from_user'):
#             return await handler(event, data)
#
#         state = data.get('state')
#         storage = data.get('storage')
#
#         if not state or not isinstance(storage, RedisStorage):
#             return await handler(event, data)
#
#         try:
#             if not await state.get_state():
#                 user_id = event.from_user.id
#                 redis_key = f"fsm:{user_id}:state"
#
#                 # Используем redis-клиент из storage
#                 redis = storage.redis
#                 restored_state = await redis.get(redis_key)
#
#                 if restored_state:
#                     await state.set_state(restored_state)
#                     print(f"Восстановлено состояние для {user_id}: {restored_state}")
#
#         except Exception as e:
#             print(f"Ошибка восстановления состояния: {e}")
#
#         return await handler(event, data)
