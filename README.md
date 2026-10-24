# MySQL 쿼리 학습 노트

MySQL 8.0 쿼리 문법을 개념 → 예시 → 연습문제 순서로 정리한 단일 HTML 페이지입니다.
`index.html`을 브라우저로 열면 바로 동작합니다(서버 불필요).

- 쿼리 실행 순서 단계별 시각화
- 장별 개념 설명, 예시 쿼리와 결과 테이블, 함정 정리, 연습문제 45개
- 답안과 "풀었음" 체크는 브라우저 localStorage에 저장

## 결과 테이블 검증

모든 예시·정답 쿼리의 결과 테이블은 실제 MySQL 8.0에서 실행한 결과를 빌드 시 삽입합니다.

```bash
mysql -uroot --default-character-set=utf8mb4 < build/schema.sql
mysql -uroot -e "CREATE USER IF NOT EXISTS 'study'@'localhost' IDENTIFIED BY 'study'; GRANT ALL ON study.* TO 'study'@'localhost';"
pip install pymysql
python3 build/build.py   # build/template.html -> index.html
```

- `data-run`: 쿼리를 실행해 결과 테이블 삽입
- `data-run="err"`: 에러가 나야 하는 쿼리, 실제 에러 메시지 삽입
- `data-fn`: `식 -- 기대값` 주석을 실제 실행값과 대조
