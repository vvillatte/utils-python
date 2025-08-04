from datetime import datetime

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