from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import openai
import os
from app.db import SessionLocal
from typing import Any, List
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
import json

router = APIRouter()

class QueryRequest(BaseModel):
    query: str
    itineary: Any

class QueryResult(BaseModel):
    sql: str
    result: List[dict]

# Initialize OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_user_intentions(natural_language_query: str, complete_itinerary: str) -> List[str]:
    """Router Agent"""
    prompt = f""" You are a manager agent of travelling company. Your main task is to understand
    customer query and based on that create intention of the user. You will be provided with complete_itinerary as well to understand the user query.

    For example: If user ask to reduce the number of days in the trip, you should understand that user and create intention in below JSON format:
     ```
     {{
            "intention": "modify_itinerary",
            "action": "reduce_trip_duration",
            "parameters": {{
                "current_duration": 7,
                "new_duration": 5,
                "days_removed": ["Day 3: Free Day for Self Exploration", "Day 6: Benoa Water Sports"],
                "reason": "User wants a shorter trip to fit their schedule."
            }},
            "forward_to": "itinerary_agent",
            "priority": "high",
            "notes": "Ensure affected activities canceled and the cost is adjusted."
        }}
     ```
    
    Availabe User intentions are:
        1. add_free_day: 
            - Adds a free day to the itinerary for personal leisure or exploration.
            - user query example: add free day added for self-exploration in Seminyak
        2. replace_free_day
            - Removes a free day from the itinerary.
            - user query example: replace free day with an activity: Nusa Penida Tour.
        3. remove_free_day
            - Removes a free day from the itinerary.
            - user query example: remove free day from the itinerary.
        3. add_activity
            - Adds a new activity to the itinerary.
            - user query example: add a new activity: Snorkeling at Nusa Dua.
        4. remove_activity
            - Removes an activity from the itinerary.
            - user query example: remove activity: Ubud Monkey Forest.
        5. reorder_activities
            - Changes the order of activities on a specific day or across days.
            - user query example: move snorkeling to the first day.
        6. change_accommodation
            - Updates the accommodation to a different location or hotel.
            - user query example: change accommodation to Villa Seminyak Estate & Spa
        7. upgrade_accommodation
            - Upgrades the accommodation to a higher category or luxury hotel.
            - user query example: upgrade hotel to Four Seasons Resort Bali at Sayan
        8. downgrade_accommodation
            - Downgrades the accommodation to a more budget-friendly option
            - user query example: downgrade hotel to The Kayon Resort by Pramana
        9. approve_final_itinerary
            - Confirms and approves the final itinerary for the trip.
    
    Important Note:
        - on user query can have multiple intentions.
    
    complete_itinerary: [complete_itinerary]
    """
    
    response = openai.chat.completions.create(
        model='gpt-4o-mini',
        messages=[{
            "role": "system",
            "content": prompt.replace("[complete_itinerary]", complete_itinerary)
        }, {
            "role": "user",
            "content": f"user query: ${natural_language_query}. Return only the list of user intentions in JSON format."
        }],
        max_tokens=1000,
        temperature=0
    )
    
    # Split multiple SQL queries
    result = response.choices[0].message.content.replace("```", "").replace('json', '')
    print('result', result)
    return result

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
        print(query_request.query)
        result = generate_user_intentions(query_request.query, json.dumps(query_request.itineary))

        return result
    
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")