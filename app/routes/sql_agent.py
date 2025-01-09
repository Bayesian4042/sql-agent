from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import openai
import os
from app.db import SessionLocal
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

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
    prompt = f"""Convert the following natural language query into an SQL query. Our goal
    is to retrieve data of activities, hotels, and locations for travel groups and themes based on the given natural language query.
    
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
    
    Database Tables (Sample Data):
        - Region can either be 'Asia', 'Europe', 'North America', 'Middle East'
    
    Important Note:
        - First, we need to identify the region name, destination name, location name, travel group name, and travel theme name.
        - Region has values like 'Asia', 'Europe', 'North America', 'Middle East'.
        - Destination has values like 'Tokyo', 'Paris', 'New York', 'Dubai'.
        - Location has values like 'Shibuya', 'Shinjuku', 'Champs Elysees', 'Times Square', 'Burj Khalifa'.
        - If any of the above information is missing, we will start the query with the available information. In this order: region -> destination -> location -> travel group -> travel theme.
        - If travel group and travel theme are not provided, we will return all travel groups and themes.
        - In natural language queries, there may be some missing information, for example, the region name may not be provided, in such cases, we start the query with destination and so on.

    Tools to use:
        - execute_sql(sql_query: str, db: Session) -> dict: Execute a single SQL query and return results.
    Query: {natural_language_query}
    
    Return only the SQL query. Do not include any explanations.
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
    sql_query = response.choices[0].message.content.replace("```", "").replace('sql', '').replace('SQL', '').split(';')
    return sql_query

def execute_sql(sql_query: str, db: Session):
    """Execute a single SQL query and return results"""
    try:
        result = db.execute(text(sql_query))
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
        sql_queries: List[str] = generate_sql(query_request.query)

        if not sql_queries:
            raise HTTPException(status_code=400, detail="No SQL queries generated.")

        # Execute each query
        results = []
        with SessionLocal() as db:
            for sql_query in sql_queries:
                if not isinstance(sql_query, str):
                    raise HTTPException(status_code=400, detail="Invalid SQL query format.")
                result = execute_sql(sql_query, db)
                results.append(result)

        return {"queries": results}
    
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")