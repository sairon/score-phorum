import re
import unicodedata

from django import template
from django.utils.safestring import mark_safe

from ..utils import parse_search_query

register = template.Library()


def normalize_diacritics(text):
    """Remove diacritics from text for comparison."""
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )


def build_highlight_pattern(token, is_phrase=False):
    r"""Build regex pattern for highlighting a single token.

    Uses \b (Python word boundary) instead of \y (PostgreSQL).
    For phrases, wildcards are literal.
    Token is normalized (diacritics removed) to match normalized text.
    """
    # Normalize token for diacritics-insensitive matching
    normalized_token = normalize_diacritics(token)

    if is_phrase:
        # Phrases: wildcards are literal, just escape and add boundaries
        escaped = re.escape(normalized_token)
        return r'\b' + escaped + r'\b'

    has_start_wildcard = normalized_token.startswith('*')
    has_end_wildcard = normalized_token.endswith('*')

    # Remove edge wildcards for processing
    inner = normalized_token.lstrip('*').rstrip('*')

    # Escape and replace internal wildcards (\S* = non-whitespace, greedy)
    escaped = re.escape(inner).replace(r'\*', r'\S*')

    # Add prefix/suffix: \S* for wildcard (greedy to match whole word), \b for word boundary
    prefix = r'\S*' if has_start_wildcard else r'\b'
    suffix = r'\S*' if has_end_wildcard else r'\b'

    return prefix + escaped + suffix


@register.filter
def highlight_search(text, query):
    """
    Highlight search matches in HTML text.

    Handles:
    - HTML content (doesn't highlight inside tags)
    - Wildcard patterns (* → .*) for words only
    - Case-insensitive matching
    - Diacritics-insensitive matching
    - Multiple tokens (quoted phrases and words)
    """
    if not query or not text:
        return text

    # Parse query into tokens and build combined pattern
    tokens = parse_search_query(query)
    token_patterns = [build_highlight_pattern(t.text, t.is_phrase) for t in tokens]
    pattern = '|'.join(f'({p})' for p in token_patterns)

    def highlight_text_segment(segment):
        """Highlight matches in a text segment (not HTML tags)."""
        # Normalize segment for diacritics-insensitive matching
        normalized = normalize_diacritics(segment)

        # Find all matches in normalized text
        matches = list(re.finditer(pattern, normalized, re.IGNORECASE))
        if not matches:
            return segment

        # Apply highlights in reverse order to preserve positions
        result = segment
        for match in reversed(matches):
            start, end = match.start(), match.end()
            original_match = segment[start:end]
            result = result[:start] + '<mark class="search-highlight">' + original_match + '</mark>' + result[end:]

        return result

    # Split text into HTML tags and text segments
    # Pattern matches HTML tags
    parts = re.split(r'(<[^>]+>)', text)

    result_parts = []
    for part in parts:
        if part.startswith('<') and part.endswith('>'):
            # This is an HTML tag, don't modify
            result_parts.append(part)
        else:
            # This is text content, highlight matches
            result_parts.append(highlight_text_segment(part))

    return mark_safe(''.join(result_parts))


@register.filter
def new_posts(room, visits):
    if not visits:
        return room.total_messages
    return visits.get(room.id, room.total_messages)


@register.filter
def is_newer_than(message, compared_time=None):
    if not compared_time:
        return True
    return message.created > compared_time


@register.filter
def can_be_deleted_by(message, user):
    return message.can_be_deleted_by(user)
