from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import openai
import os
from app.db import SessionLocal
from typing import List

router = APIRouter()

class QueryRequest(BaseModel):
    query: str

class QueryResult(BaseModel):
    sql: str
    result: List[dict]

# Initialize OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_sql(natural_language_query: str) -> List[str]:
    """Generate SQL from natural language using OpenAI"""
    prompt = f"""Convert the following natural language query into one or more SQL queries:
    
    Database schema:
    - region (id, region)
    - pair (id, destination_pair)
    - destination (id, name, code, description, region_id, pair_id)
    - location (id, name, description, destination_id)
    - travel_group (id, name, code, description)
    - travel_theme (id, name, code, description)
    - location_group_theme (id, location_id, travel_group_id, travel_theme_id, rating)
    - hotel (id, name, description, location, location_id, star, rating)
    - must_travel_activity (id, name, code, description, destination_id)
    - recommended_activity (id, name, code, description, destination_id)
    - must_activity_group_theme (id, must_travel_activity_id, travel_group_id, travel_theme_id, rating)
    - recommend_activity_group_theme (id, recommend_activity_id, travel_group_id, travel_theme_id, rating)

    Query: {natural_language_query}
    
    Return only the SQL queries separated by semicolons. Do not include any explanations.
    SQL:"""
    
    response = openai.chat.completions.create(
        model='gpt-4o-mini',
        messages=[{
            "role": "system",
            "content": prompt
        }],
        max_tokens=1000,
        temperature=0
    )
    
    # Split multiple SQL queries
    sql_queries = [q.strip() for q in response.choices[0].message.content.strip().split(';') if q.strip()]
    return sql_queries

def execute_sql(sql_query: str, db):
    """Execute a single SQL query and return results"""
    try:
        result = db.execute(sql_query)
        return {
            "sql": sql_query,
            "result": [dict(row) for row in result.fetchall()]
        }
    except Exception as e:
        return {
            "sql": sql_query,
            "error": str(e)
        }

@router.post("/query")
async def execute_query(query_request: QueryRequest):
    """Execute natural language query using SQL agent"""
    try:
        # Generate SQL queries
        sql_queries = generate_sql(query_request.query)
        
        # Execute each query
        db = SessionLocal()
        results = []
        try:
            for sql in sql_queries:
                result = execute_sql(sql, db)
                results.append(result)
            return {"queries": results}
        finally:
            db.close()
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
