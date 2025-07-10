import hashlib
import pickle

from backend.app.clients.redis_client import rds
from backend.app.clients.openai_client import embedding

ONE_DAY = 60 * 60 * 24

def get_cached_embedding(text: str) -> list[float]:
    key  = "emb:" + hashlib.sha1(text.encode()).hexdigest()

    if (cached := rds.get(key)):
        return pickle.loads(cached)

    # 캐시가 없다면 OpenAI 호출
    emb = embedding(input=[text], model="text-embedding-3-small")
    rds.setex(key, ONE_DAY, pickle.dumps(emb))
    return emb