# cgi.py - ملف مؤقت لحل مشكلة التوافق مع بايثون 3.13
def parse_header(line):
    if not line:
        return "", {}
    parts = line.split(';')
    key = parts[0].strip()
    pdict = {}
    for part in parts[1:]:
        if '=' in part:
            k, v = part.split('=', 1)
            pdict[k.strip()] = v.strip().replace('"', '')
    return key, pdict
