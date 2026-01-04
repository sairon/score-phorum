from collections import namedtuple
import re

from django.db.models import Q


SearchToken = namedtuple('SearchToken', ['text', 'is_phrase'])


def user_can_view_protected_room(user, room):
    from .models import UserRoomKeyring

    try:
        record = UserRoomKeyring.objects.get(user=user, room=room)
        if room.password_changed < record.last_successful_entry:
            return True
    except UserRoomKeyring.DoesNotExist:
        return False
    return False


def get_ip_addr(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip_addr = x_forwarded_for.split(",")[0]
    else:
        ip_addr = request.META.get("REMOTE_ADDR")
    return ip_addr


def get_custom_resource_filename(user_id, resource_type):
    return "custom_%(res_type)s_id%(user_id)s.%(res_type)s" \
           % dict(res_type=resource_type, user_id=user_id)


def parse_search_query(query):
    """Parse query into tokens (quoted phrases and individual words).

    Returns list of SearchToken namedtuples, e.g.:
    '"cat chases" dog' → [SearchToken('cat chases', True), SearchToken('dog', False)]
    'cat chases dog' → [SearchToken('cat', False), ...]
    """
    tokens = []
    # Match quoted phrases or individual words
    pattern = r'"([^"]+)"|(\S+)'
    for match in re.finditer(pattern, query):
        if match.group(1):
            # Quoted phrase
            tokens.append(SearchToken(match.group(1), is_phrase=True))
        else:
            # Unquoted word
            tokens.append(SearchToken(match.group(2), is_phrase=False))
    return tokens


def build_token_pattern(token, is_phrase=False):
    r"""Build regex pattern for a single token.

    For phrases (is_phrase=True), wildcards are literal.
    For words, wildcard rules apply:
    - 'word' → r'\yword\y'
    - 'word*' → r'\yword\S*'
    - '*word' → r'\S*word\y'
    - '*word*' → r'\S*word\S*'
    - 'wo*rd' → r'\ywo\S*rd\y' (internal wildcard, boundaries on edges)
    """
    if is_phrase:
        # Phrases: wildcards are literal, just escape and add boundaries
        escaped = re.escape(token)
        return r'\y' + escaped + r'\y'

    has_start_wildcard = token.startswith('*')
    has_end_wildcard = token.endswith('*')

    # Remove edge wildcards for processing
    inner = token.lstrip('*').rstrip('*')

    # Escape and replace internal wildcards (\S* = non-whitespace)
    escaped = re.escape(inner).replace(r'\*', r'\S*')

    # Add prefix: \S* for wildcard, \y for word boundary
    prefix = r'\S*' if has_start_wildcard else r'\y'
    suffix = r'\S*' if has_end_wildcard else r'\y'

    return prefix + escaped + suffix


def build_search_patterns(query):
    """Build list of patterns from query (one per token)."""
    tokens = parse_search_query(query)
    return [build_token_pattern(t.text, t.is_phrase) for t in tokens]


def search_messages(query, user):
    r"""Search PublicMessage for matching text.

    Returns a list of (thread_id, newest_match) tuples for pagination.
    Uses database-level GROUP BY for efficiency.

    Uses PostgreSQL-specific features:
    - unaccent() for diacritics-insensitive matching
    - ~* regex operator for case-insensitive matching
    - \y for word boundaries

    Word order is independent - all tokens must match but in any order.
    Quoted phrases must match exactly as written.
    """
    from .models import PublicMessage, UserRoomKeyring
    from django.db.models import Max
    from django.db.models.functions import Coalesce

    patterns = build_search_patterns(query)

    # Build room access filter
    if user.is_authenticated:
        unlocked_room_ids = UserRoomKeyring.objects.filter(
            user=user
        ).values_list('room_id', flat=True)
        room_filter = Q(room__password='') | Q(room_id__in=unlocked_room_ids)
    else:
        room_filter = Q(room__password='')

    # Build pattern filters using custom lookup
    pattern_filter = Q()
    for pattern in patterns:
        pattern_filter &= Q(text__unaccent_iregex=pattern)

    # Query: group by thread, get newest match date, return only IDs
    thread_matches = (
        PublicMessage.objects
        .filter(room_filter, deleted_by__isnull=True)
        .filter(pattern_filter)
        .annotate(effective_thread_id=Coalesce('thread_id', 'id'))
        .values('effective_thread_id')
        .annotate(newest_match=Max('created'))
        .order_by('-newest_match')
        .values_list('effective_thread_id', 'newest_match')
    )

    return list(thread_matches)


def get_matching_reply_ids(query, thread_ids, user):
    """Get matching reply IDs for specific threads only.

    Returns dict: {thread_id: [reply_id, ...]}
    """
    from .models import PublicMessage, UserRoomKeyring
    from collections import defaultdict

    if not thread_ids:
        return {}

    patterns = build_search_patterns(query)

    # Room filter
    if user.is_authenticated:
        unlocked_room_ids = UserRoomKeyring.objects.filter(
            user=user
        ).values_list('room_id', flat=True)
        room_filter = Q(room__password='') | Q(room_id__in=unlocked_room_ids)
    else:
        room_filter = Q(room__password='')

    # Build pattern filters using custom lookup
    pattern_filter = Q()
    for pattern in patterns:
        pattern_filter &= Q(text__unaccent_iregex=pattern)

    # Get only reply IDs (not root messages) for the specified threads
    reply_data = (
        PublicMessage.objects
        .filter(room_filter, deleted_by__isnull=True, thread_id__in=thread_ids)
        .filter(pattern_filter)
        .values_list('id', 'thread_id')
    )

    # Group by thread
    result = defaultdict(list)
    for reply_id, thread_id in reply_data:
        result[thread_id].append(reply_id)

    return dict(result)


def fetch_matching_replies(thread_ids, matching_reply_ids_by_thread):
    """Fetch matching replies for given threads in a single query.

    Call this after pagination to only fetch replies for visible threads.
    """
    from .models import PublicMessage

    # Collect reply IDs only for the requested threads
    reply_ids = []
    for thread_id in thread_ids:
        reply_ids.extend(matching_reply_ids_by_thread.get(thread_id, []))

    if not reply_ids:
        return {}

    all_replies = PublicMessage.objects.filter(
        pk__in=reply_ids
    ).select_related('author', 'room', 'room__author', 'room__moderator', 'recipient', 'deleted_by').order_by('created')

    # Group by thread_id
    replies_by_thread = {}
    for reply in all_replies:
        if reply.thread_id not in replies_by_thread:
            replies_by_thread[reply.thread_id] = []
        replies_by_thread[reply.thread_id].append(reply)

    return replies_by_thread
