import re

# проверка ответов и подсчёт очков

from rapidfuzz import fuzz


def _strip_feat(text: str):
    """Убирает feat./featuring/ft. и всё после них, а также скобки."""
    text = re.sub(r"\(.*?\)", " ", text)          # убрать (feat. ...) и прочие скобки
    text = re.sub(r"\[.*?\]", " ", text)
    text = re.split(r"\bfeat\b|\bfeaturing\b|\bft\b", text, flags=re.I)[0]
    return text


def normalize(text: str):
    """Единый вид: без feat, нижний регистр, без пунктуации и артиклей."""
    text = _strip_feat(text)
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)
    for w in ["the ", "a ", "and ", " и "]:
        text = text.replace(w, " ")
    return re.sub(r"\s+", " ", text).strip()


def split_artists(artist: str):
    """Разбивает строку исполнителей на список: 'A feat. B & C' -> ['A','B','C']."""
    # сначала отделяем основного от feat
    parts = re.split(r"\bfeat\b|\bfeaturing\b|\bft\b|[,&]|\bx\b|\band\b|\bи\b",
                     artist, flags=re.I)
    # но featured-исполнители часто в скобках — вытащим и их
    extra = re.findall(r"\((?:feat\.?|ft\.?|featuring)\s*(.*?)\)", artist, flags=re.I)
    for e in extra:
        parts += re.split(r"[,&]|\bx\b|\band\b|\bи\b", e, flags=re.I)
    out = []
    for p in parts:
        p = _strip_feat(p).strip()
        if p and p.lower() not in [o.lower() for o in out]:
            out.append(p)
    return out or [artist]


def check_answer(user_answer: str, correct_answer: str, threshold: int = 78):
    """Нечёткое сравнение, устойчивое к опечаткам и к feat./скобкам."""
    a = normalize(user_answer)
    b = normalize(correct_answer)
    if not a or not b:
        return False, 0
    # сравниваем и целиком, и по вхождению (частичное совпадение)
    score = max(fuzz.ratio(a, b), fuzz.partial_ratio(a, b))
    return score >= threshold, score


def check_artists(user_answer: str, artist_field: str, threshold: int = 74):
    """Для раунда по исполнителю: засчитывает совпадение с ЛЮБЫМ из исполнителей,
    в любом порядке. Возвращает (сколько угадано, всего, засчитано ли хоть один)."""
    artists = split_artists(artist_field)
    ua = normalize(user_answer)
    matched = 0
    for art in artists:
        na = normalize(art)
        if not na:
            continue
        sc = max(fuzz.ratio(ua, na), fuzz.partial_ratio(ua, na))
        if sc >= threshold:
            matched += 1
    return matched, len(artists), matched > 0


def calculate_points(base_points: int, answer_time: float, time_limit: float = 30.0):
    if answer_time >= time_limit:
        return int(base_points * 0.3)
    ratio = 1 - (answer_time / time_limit)
    return int(base_points * (0.3 + 0.7 * ratio))
