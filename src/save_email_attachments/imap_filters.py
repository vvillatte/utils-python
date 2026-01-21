import re
from datetime import datetime

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def build_search_criteria(args):
    criteria = []
    if args.from_:
        criteria += ['FROM', f'"{args.from_}"']
    if args.to:
        criteria += ['TO', f'"{args.to}"']
    if args.after:
        criteria += ['SINCE', format_date(args.after)]
    if args.before:
        criteria += ['BEFORE', format_date(args.before)]
    if args.subject:
        criteria += ['SUBJECT', f'"{args.subject}"']
    if args.unread:
        criteria += ['UNSEEN']
    return criteria

def format_date(date_str):
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.strftime("%d-%b-%Y")

def validate_search_fields(search):
    """
    Validate search criteria before building IMAP search commands.
    Raises ValueError on invalid input.
    """

    # Validate email fields
    for field in ["from_", "to"]:
        value = search.get(field)
        if value:
            if not EMAIL_REGEX.match(value):
                raise ValueError(f"Invalid email format for '{field}': {value}")

    # Validate date fields
    for field in ["after", "before"]:
        value = search.get(field)
        if value:
            try:
                datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                raise ValueError(f"Invalid date format for '{field}': {value}. "
                                 "Expected YYYY-MM-DD")

    # Logical consistency: after <= before
    after = search.get("after")
    before = search.get("before")
    if after and before:
        d_after = datetime.strptime(after, "%Y-%m-%d")
        d_before = datetime.strptime(before, "%Y-%m-%d")
        if d_after > d_before:
            raise ValueError("Search date range is inconsistent: "
                             "'after' is later than 'before'")

    # Ensure at least one meaningful criterion
    if not any(search.get(k) for k in ["from_", "to", "subject", "after", "before", "unread"]):
        raise ValueError("No valid search criteria provided")

    return True
