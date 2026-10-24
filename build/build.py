#!/usr/bin/env python3
"""template.html -> ../index.html

- <code class="sql" data-run>        : 쿼리를 실제 MySQL에서 실행해 결과 테이블을 바로 뒤에 삽입
- <code class="sql" data-run="err">  : 에러가 나야 하는 쿼리. 실제 에러 메시지를 삽입
- <code class="sql" data-fn>         : 각 줄의 `식 -- 기대값` 주석을 SELECT 식으로 검산
- /*@STEPS@*/                        : 실행 순서 스테퍼의 단계별 중간 결과(JSON)

사용: mysql에 schema.sql을 넣은 뒤  python3 build/build.py
"""
import datetime
import decimal
import html
import json
import os
import re
import sys

import pymysql

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'template.html')
OUT = os.path.join(HERE, '..', 'index.html')

conn = pymysql.connect(host='localhost', user='study', password='study', database='study',
                       charset='utf8mb4', autocommit=True)


def fmt(v):
    if v is None:
        return None
    if isinstance(v, (datetime.date, datetime.datetime)):
        return v.isoformat(sep=' ') if isinstance(v, datetime.datetime) else v.isoformat()
    if isinstance(v, bytes):
        return v.decode()
    if isinstance(v, float):
        return str(int(v)) if v.is_integer() else repr(v)
    return str(v)


def run(sql):
    with conn.cursor() as cur:
        cur.execute(sql)
        cols = [d[0] for d in cur.description]
        return cols, cur.fetchall()


def table_html(cols, rows, cap):
    h = ['<div class="rt"><table><caption>%s <span>(%d행)</span></caption><thead><tr>' % (html.escape(cap), len(rows))]
    h += ['<th>%s</th>' % html.escape(c) for c in cols]
    h.append('</tr></thead><tbody>')
    for r in rows:
        h.append('<tr>')
        for v in r:
            if v is None:
                h.append('<td class="null">NULL</td>')
            elif isinstance(v, (int, float, decimal.Decimal)):
                h.append('<td class="n">%s</td>' % html.escape(fmt(v)))
            else:
                h.append('<td>%s</td>' % html.escape(fmt(v)))
        h.append('</tr>')
    if not rows:
        h.append('<tr><td class="empty" colspan="%d">결과 없음 (0행)</td></tr>' % len(cols))
    h.append('</tbody></table></div>')
    return ''.join(h)


def find_comment(line):
    q = False
    for i, ch in enumerate(line):
        if ch == "'":
            q = not q
        elif not q and line.startswith('--', i):
            return line[:i], line[i + 2:]
    return line, None


VAL = r"(?:'[^']*'|NULL|-?\d+(?:\.\d+)?)"
EXPECT_RE = re.compile(r'^\s*(%s(?:, %s)*)(?:\s|$)' % (VAL, VAL))

errors = []
checked = {'run': 0, 'err': 0, 'fn': 0}


def check_fn(sql):
    for line in sql.split('\n'):
        expr, cm = find_comment(line)
        expr = expr.strip().rstrip(',').strip()
        if not expr or cm is None:
            continue
        m = EXPECT_RE.match(cm)
        if not m:
            continue
        expected = [t.strip("'") for t in re.findall(VAL, m.group(1))]
        try:
            _, rows = run('SELECT ' + expr)
        except Exception as e:  # noqa
            errors.append('fn 실행 실패: %s -> %s' % (expr, e))
            continue
        got = ['NULL' if v is None else fmt(v) for v in rows[0]]
        if got != expected:
            errors.append('fn 불일치: %s\n   주석=%s  실제=%s' % (expr, expected, got))
        checked['fn'] += 1


CODE_RE = re.compile(r'<pre><code class="sql"([^>]*)>(.*?)</code></pre>', re.S)


def repl(m):
    attrs, body = m.group(1), m.group(2)
    sql = html.unescape(body).strip('\n')
    out = '<pre><code class="sql">%s</code></pre>' % html.escape(sql, quote=False)
    a = dict(re.findall(r'data-(\w+)(?:="([^"]*)")?', attrs))
    if 'fn' in a:
        check_fn(sql)
    if 'run' in a:
        mode = a['run']
        try:
            cols, rows = run(sql)
            if mode == 'err':
                errors.append('에러가 나야 하는데 성공함:\n' + sql)
            else:
                out += table_html(cols, rows, a.get('cap') or '결과')
                checked['run'] += 1
        except pymysql.MySQLError as e:
            if mode != 'err':
                errors.append('실행 실패: %s\n%s' % (e, sql))
            else:
                code, msg = e.args[0], e.args[1]
                out += '<div class="err"><b>ERROR %s</b> %s</div>' % (code, html.escape(msg))
                checked['err'] += 1
    return out


# ---------- 실행 순서 스테퍼: 단계별 중간 결과 ----------
STEP_SQL = [
    # FROM + JOIN : 주문 10행 중 고객과 짝이 없는 비회원 주문이 떨어져 나감
    """SELECT o.order_id, o.customer_id, c.name, c.city, o.order_date, o.amount,
              c.customer_id IS NULL AS _x
       FROM orders o LEFT JOIN customers c ON o.customer_id = c.customer_id
       ORDER BY o.order_id""",
    # WHERE
    """SELECT o.order_id, o.customer_id, c.name, c.city, o.order_date, o.amount,
              o.order_date < '2026-09-01' AS _x
       FROM orders o JOIN customers c ON o.customer_id = c.customer_id
       ORDER BY o.order_id""",
    # GROUP BY
    """SELECT c.customer_id, c.city,
              GROUP_CONCAT(o.order_id ORDER BY o.order_id SEPARATOR ', ') AS `묶인 order_id`,
              GROUP_CONCAT(o.amount ORDER BY o.order_id SEPARATOR ', ') AS `묶인 amount`
       FROM orders o JOIN customers c ON o.customer_id = c.customer_id
       WHERE o.order_date >= '2026-09-01'
       GROUP BY c.customer_id, c.city ORDER BY c.customer_id""",
    # HAVING
    """SELECT c.customer_id, c.city, SUM(o.amount) AS `SUM(o.amount)`,
              SUM(o.amount) < 150000 AS _x
       FROM orders o JOIN customers c ON o.customer_id = c.customer_id
       WHERE o.order_date >= '2026-09-01'
       GROUP BY c.customer_id, c.city ORDER BY c.customer_id""",
    # SELECT
    """SELECT c.city, COUNT(*) AS order_cnt
       FROM orders o JOIN customers c ON o.customer_id = c.customer_id
       WHERE o.order_date >= '2026-09-01'
       GROUP BY c.customer_id, c.city
       HAVING SUM(o.amount) >= 150000 ORDER BY c.customer_id""",
    # DISTINCT
    """WITH t AS (
         SELECT c.customer_id, c.city, COUNT(*) AS order_cnt
         FROM orders o JOIN customers c ON o.customer_id = c.customer_id
         WHERE o.order_date >= '2026-09-01'
         GROUP BY c.customer_id, c.city
         HAVING SUM(o.amount) >= 150000)
       SELECT city, order_cnt,
              ROW_NUMBER() OVER (PARTITION BY city, order_cnt ORDER BY customer_id) > 1 AS _x
       FROM t ORDER BY customer_id""",
    # ORDER BY
    """SELECT DISTINCT c.city, COUNT(*) AS order_cnt
       FROM orders o JOIN customers c ON o.customer_id = c.customer_id
       WHERE o.order_date >= '2026-09-01'
       GROUP BY c.customer_id, c.city
       HAVING SUM(o.amount) >= 150000
       ORDER BY order_cnt""",
    # LIMIT
    """WITH t AS (
         SELECT DISTINCT c.city, COUNT(*) AS order_cnt
         FROM orders o JOIN customers c ON o.customer_id = c.customer_id
         WHERE o.order_date >= '2026-09-01'
         GROUP BY c.customer_id, c.city
         HAVING SUM(o.amount) >= 150000)
       SELECT city, order_cnt, ROW_NUMBER() OVER (ORDER BY order_cnt) > 1 AS _x
       FROM t ORDER BY order_cnt""",
]
FINAL_SQL = """SELECT DISTINCT c.city, COUNT(*) AS order_cnt
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_date >= '2026-09-01'
GROUP BY c.customer_id, c.city
HAVING SUM(o.amount) >= 150000
ORDER BY order_cnt
LIMIT 1"""


def steps_json():
    data = []
    for sql in STEP_SQL:
        cols, rows = run(sql)
        x = []
        if cols[-1] == '_x':
            x = [i for i, r in enumerate(rows) if r[-1]]
            cols, rows = cols[:-1], [r[:-1] for r in rows]
        data.append({'cols': cols, 'rows': [[fmt(v) for v in r] for r in rows], 'x': x})
    # 마지막 단계에서 살아남은 행 == 실제 쿼리 결과인지 검산
    _, final = run(FINAL_SQL)
    last = data[-1]
    alive = [r for i, r in enumerate(last['rows']) if i not in last['x']]
    if alive != [[fmt(v) for v in r] for r in final]:
        errors.append('스테퍼 마지막 단계와 실제 결과가 다름: %s vs %s' % (alive, final))
    return json.dumps(data, ensure_ascii=False)


src = open(SRC, encoding='utf-8').read()
out = CODE_RE.sub(repl, src)
out = out.replace('/*@STEPS@*/', steps_json())

n_prac = len(re.findall(r'class="prac"', out))
ids = re.findall(r'class="prac" data-id="([^"]+)"', out)
if len(ids) != len(set(ids)):
    errors.append('연습문제 id 중복')

if errors:
    print('\n\n'.join(errors))
    sys.exit(1)
open(OUT, 'w', encoding='utf-8').write(out)
print('ok: 실행 %(run)d, 에러 예시 %(err)d, 함수 주석 검산 %(fn)d' % checked, '| 연습문제', n_prac)
