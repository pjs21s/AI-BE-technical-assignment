#!/usr/bin/env python
import os
import sys
import json
import glob
import logging
import openai

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    logger.error("OPENAI_API_KEY 환경변수가 필요합니다.")
    exit(1)

# 데이터베이스 연결 정보
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "database": os.getenv("POSTGRES_DB"),
}


def connect_to_db():
    """데이터베이스에 연결"""
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"],
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        logger.info(f"성공적으로 {DB_CONFIG['database']} 데이터베이스에 연결했습니다.")
        return conn
    except psycopg2.Error as e:
        logger.error(f"데이터베이스 연결 오류: {e}")
        raise


def create_company_table(conn):
    """company 테이블 생성 (존재하지 않을 경우)"""
    try:
        with conn.cursor() as cursor:
            # 테이블이 존재하는지 확인
            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'company'
                );
                """
            )
            table_exists = cursor.fetchone()[0]

            if not table_exists:
                logger.info(
                    "company 테이블이 존재하지 않습니다. 새로운 테이블을 생성합니다."
                )
                cursor.execute(
                    """
                    CREATE TABLE company (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(255) UNIQUE NOT NULL,
                        data JSONB NOT NULL
                    );
                """
                )
                logger.info("company 테이블이 성공적으로 생성되었습니다.")
            else:
                logger.info("company 테이블이 이미 존재합니다. 테이블 생성을 건너뜁니다.")

            # pgvector 확장
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            # summary_text 컬럼 추가
            cursor.execute(
                """
                ALTER TABLE company
                ADD COLUMN IF NOT EXISTS summary_text TEXT;
                """
            )
            # embedding 컬럼이 없으면 추가
            cursor.execute(
                """
                ALTER TABLE company
                ADD COLUMN IF NOT EXISTS embedding VECTOR(1536);
                """
            )

    except psycopg2.Error as e:
        logger.error(f"테이블 생성 오류: {e}")
        raise


def make_summary(data: dict) -> str:
    """
    회사의 설립 시기, 성장 단계, 조직 규모, 핵심 서비스, 주요 지표, 
    재무 성과, 투자 이력 등을 포함한 요약문 생성
    """
    base = data["base_company_info"]["data"]
    inv = data.get("investment", {})
    fin = data.get("finance", {}).get("data", [])
    mau = data.get("mau", {}).get("list", [])
    products = data.get("products", [])
    
    parts = []
    
    # 1. 설립 시기 & 성장 단계
    found = base.get("foundAt")
    stage = inv.get("lastInvestmentLevel")
    if found or stage:
        s = []
        if found:
            year = found.split("-")[0]
            s.append(f"{year}년 설립")
        if stage:
            s.append(f"{stage} 투자 단계")
        parts.append(", ".join(s))
    
    # 2. 조직 규모
    emp = base.get("empWholeVal")
    # (성장률은 생략하거나 조직 데이터에서 계산할 수 있음)
    if emp:
        parts.append(f"직원 수 약 {emp}명")
    
    # 3. 핵심 서비스·제품 특징
    intro = base.get("corpIntroKr") or base.get("corpIntroEn", "")
    prod_names = [p.get("name") for p in products if p.get("name")]
    if intro:
        parts.append(intro)
    if prod_names:
        parts.append(f"주요 제품/서비스: {', '.join(prod_names)}")
    
    # 4. 주요 지표 (MAU)
    if mau:
        # 첫 번째 상품의 최신 MAU
        latest = mau[0]["data"][-1]
        parts.append(f"MAU 약 {latest['value']:,}명 ({latest['referenceMonth']} 기준)")
    
    # 5. 재무 성과 요약
    if fin:
        last_fin = fin[-1]
        profit = last_fin.get("profit")
        net = last_fin.get("netProfit")
        year = last_fin.get("year")
        prof_s = f"{profit:,}원 매출" if profit is not None else ""
        net_s = f"순이익 {net:,}원" if net is not None else ""
        parts.append(f"{year}년 {prof_s}·{net_s}")
    
    # 6. 투자 이력 & 주요 투자자
    total_inv = inv.get("totalInvestmentAmount")
    iv_list = inv.get("data", [])
    if total_inv:
        # 상위 2개 투자자
        top_investors = []
        if iv_list:
            # 첫 행사 투자 데이터의 첫 2명
            top = iv_list[0].get("investor", [])[:2]
            top_investors = [i["name"] for i in top if i.get("name")]
        inv_s = f"총 투자 {total_inv:,}원"
        if top_investors:
            inv_s += " (주요 투자자: " + ", ".join(top_investors) + ")"
        parts.append(inv_s)
    
    return ". ".join(parts)


def load_company_data(file_path):
    """회사 데이터 파일 불러오기"""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
            # 파일 이름에서 회사 이름 추출 (예: company_ex1_비바리퍼블리카.json -> 비바리퍼블리카)
            company_name = os.path.basename(file_path).split("_")[-1].split(".")[0]
            return company_name, data
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.error(f"파일 로드 오류 ({file_path}): {e}")
        return None, None


def insert_company_data(conn, name, data):
    """회사 데이터를 데이터베이스에 삽입"""
    summary = make_summary(data)
    try:
        response = openai.embeddings.create(
            input=[summary],
            model="text-embedding-3-small"
        )
        embedding = response.data[0].embedding
    except Exception as e:
        logger.error(f"임베딩 생성에 실패했습니다.: {e}")
        sys.exit(1)

    try:
        with conn.cursor() as cursor:
        
            # 데이터 삽입
            cursor.execute(
                """
                INSERT INTO company (name, data, summary_text, embedding)
                VALUES (%s, %s::jsonb, %s, %s::vector)
                ON CONFLICT (name) DO UPDATE
                SET data = EXCLUDED.data,
                    summary_text = EXCLUDED.summary_text,
                    embedding = EXCLUDED.embedding;
                """,
                (name, json.dumps(data), summary, embedding),
            )
            logger.info(f"회사 '{name}'의 데이터가 성공적으로 삽입되었습니다.")
            return True
    except psycopg2.Error as e:
        logger.error(f"데이터 삽입 오류: {e}")
        conn.rollback()
        return False


def main():
    """메인 함수"""
    try:
        # 데이터베이스 연결
        conn = connect_to_db()

        # company 테이블 생성
        create_company_table(conn)

        # 회사 데이터 파일 찾기
        company_files = glob.glob(os.path.join("company_ex*.json"))
        logger.info(f"{len(company_files)}개의 회사 데이터 파일을 찾았습니다.")

        # 데이터 처리 및 삽입
        success_count = 0
        for file_path in sorted(company_files):
            company_name, company_data = load_company_data(file_path)
            if company_name and company_data:
                if insert_company_data(conn, company_name, company_data):
                    success_count += 1

        logger.info(f"총 {success_count}개의 회사 데이터가 성공적으로 삽입되었습니다.")

    except Exception as e:
        logger.error(f"예상치 못한 오류가 발생했습니다: {e}")
    finally:
        if "conn" in locals() and conn:
            conn.close()
            logger.info("데이터베이스 연결이 닫혔습니다.")


if __name__ == "__main__":
    main()
