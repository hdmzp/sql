DROP DATABASE IF EXISTS study;
CREATE DATABASE study DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE study;
CREATE TABLE customers (
  customer_id INT PRIMARY KEY,
  name        VARCHAR(20) NOT NULL,
  grade       VARCHAR(10),
  city        VARCHAR(10) NOT NULL,
  join_date   DATE NOT NULL
);
CREATE TABLE products (
  product_id   INT PRIMARY KEY,
  product_name VARCHAR(20) NOT NULL,
  category     VARCHAR(10) NOT NULL,
  price        INT NOT NULL
);
CREATE TABLE orders (
  order_id    INT PRIMARY KEY,
  customer_id INT,
  product_id  INT NOT NULL,
  order_date  DATE NOT NULL,
  qty         INT NOT NULL,
  amount      INT NOT NULL
);
INSERT INTO customers VALUES
 (1,'김하늘','VIP','서울','2024-01-15'),
 (2,'이도윤','GOLD','부산','2024-03-02'),
 (3,'박서연','VIP','서울','2024-05-20'),
 (4,'최준호',NULL,'대전','2025-02-11'),
 (5,'정예린','GOLD','서울','2025-06-30');
INSERT INTO products VALUES
 (101,'무선청소기','가전',320000),
 (102,'에어프라이어','가전',129000),
 (103,'수분크림','뷰티',38000),
 (104,'선크림','뷰티',25000),
 (105,'패딩점퍼','패션',189000),
 (106,'요가매트','생활',45000);
INSERT INTO orders VALUES
 (1, 1,   101,'2026-08-14',1,320000),
 (2, 3,   104,'2026-08-20',3, 75000),
 (3, 1,   103,'2026-09-01',2, 76000),
 (4, 1,   104,'2026-09-02',1, 25000),
 (5, 1,   103,'2026-09-03',1, 38000),
 (6, 2,   102,'2026-09-03',1,129000),
 (7, NULL,104,'2026-09-10',2, 50000),
 (8, 3,   105,'2026-09-21',1,189000),
 (9, 5,   101,'2026-10-05',1,320000),
 (10,2,   103,'2026-10-05',1, 38000);
