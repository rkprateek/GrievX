from redis.asyncio import Redis


def create_redis_client(redis_url: str) -> Redis:
    return Redis.from_url(redis_url, encoding="utf-8", decode_responses=True)


async def check_redis_connection(client: Redis) -> None:
    await client.ping()
