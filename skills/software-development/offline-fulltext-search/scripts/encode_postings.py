#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Delta-encoding para postings lists de un indice invertido (offline-fulltext-search).

Por que: un indice invertido de ~4M postings como JSON plano pesa ~25 MB;
con delta-encoding (postings ordenados, guardar diferencias como 1 char) baja a ~15 MB.
El decoder en JS decodifica de forma perezosa (solo el token consultado).

Uso:
    from encode_postings import encode_postings, decode_postings
    s = encode_postings([3, 5, 6, 9, 900])   # -> string compacto
    assert decode_postings(s) == [3, 5, 6, 9, 900]
"""


def encode_postings(lst):
    """Postings ASCENDENTES -> string compacto.

    Cada posting se guarda como delta-1 respecto al anterior (0 = consecutivo):
    - delta-1 en [0, 89]  -> 1 char: chr(33 + delta)
    - delta mayor         -> '~<delta>~' (raro: postings muy espaciados)
    """
    out = []
    prev = -1
    for x in lst:
        d = x - prev - 1
        prev = x
        if 0 <= d < 90:
            out.append(chr(33 + d))
        else:
            out.append('~' + str(d) + '~')
    return ''.join(out)


def decode_postings(s):
    """Inverso de encode_postings."""
    res = []
    prev = -1
    i = 0
    n = len(s)
    while i < n:
        c = s[i]
        if c == '~':
            j = s.index('~', i + 1)
            d = int(s[i + 1:j])
            i = j + 1
        else:
            d = ord(c) - 33
            i += 1
        prev += d + 1
        res.append(prev)
    return res


# Decoder JS equivalente (para el index.html):
# function getPostings(tok){
#   if (INDICE.has(tok)) return INDICE.get(tok);
#   const raw = INDICE_RAW[tok];
#   if (!raw) { INDICE.set(tok, null); return null; }
#   const res = []; let prev = -1, i = 0, n = raw.length;
#   while (i < n) {
#     const c = raw[i];
#     let d;
#     if (c === '~') { const j = raw.indexOf('~', i+1); d = parseInt(raw.slice(i+1, j)); i = j+1; }
#     else { d = raw.charCodeAt(i) - 33; i++; }
#     prev += d + 1; res.push(prev);
#   }
#   INDICE.set(tok, res);
#   return res;
# }


if __name__ == '__main__':
    casos = [[3, 5, 6, 9], [0, 1, 2], [999, 1000], [1]]
    for c in casos:
        e = encode_postings(c)
        d = decode_postings(e)
        assert d == c, f"{c} -> {e!r} -> {d}"
        print(f"OK  {c}  ({len(c)} postings -> {len(e)} chars)")
    print("encode/decode round-trip OK")
