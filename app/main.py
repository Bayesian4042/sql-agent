from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import openai
import os
# from app.db import SessionLocal
from typing import Any, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
import json
import gradio as gr
from dotenv import load_dotenv
import psycopg2

load_dotenv()

# Initialize OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

itineary = {
  "packageName": "Dubai Standard Package",
  "rating": 4.8,
  "duration": "4 Nights & 5 Days",
  "inclusions": {
    "airfare": "Return Economy Airfare",
    "accommodation": "4-star hotel for 4 nights",
    "meals": "4 breakfasts at the hotel",
    "transportation": {
      "airportTransfers": "Return private airport transfers",
      "cityTour": "Half Day Dubai City Tour with shared transfer",
      "desertSafari": "Standard Desert Safari with shared transfer (Falcon Camp or Similar)",
      "burjKhalifa": "At the Top Burj Khalifa (124 & 125 Floors - Non Prime Time) with shared transfer",
      "creekCruise": "Dubai Creek Cruise with shared transfer"
    },
    "insurance": "Travel Insurance",
    "taxes": "GST and TCS"
  },
  "itinerary": [
    {
      "day": 1,
      "title": "Arrival in Dubai",
      "description": "Meet and greet at the airport, transfer to the hotel (standard check-in time is 3 PM). Day at leisure. Overnight at the hotel."
    },
    {
      "day": 2,
      "title": "Dubai City Tour and Desert Safari",
      "description": "Buffet breakfast at the hotel. Half-day Dubai City Tour with return shared transfer. Standard Desert Safari with return shared transfer. Overnight at the hotel."
    },
    {
      "day": 3,
      "title": "Dubai Creek Cruise and Burj Khalifa",
      "description": "Buffet breakfast at the hotel. Dubai Creek Cruise with shared transfer. Visit 'At the Top Burj Khalifa' (124 & 125 Floors - Non Prime Time) with return shared transfer. Overnight at the hotel."
    },
    {
      "day": 4,
      "title": "Free Day for Exploration",
      "description": "Buffet breakfast at the hotel. The day is free for you to customize as per your interest. Holiday Tribe can assist with planning if needed. Overnight at the hotel."
    },
    {
      "day": 5,
      "title": "Departure from Dubai",
      "description": "Buffet breakfast at the hotel. Departure transfer to Dubai airport. Return flight back to India."
    }
  ],
  "exclusions": [
    "Visa cost",
    "Seat selection and meals cost on low-cost carriers",
    "Sightseeing not mentioned in the itinerary",
    "Meals other than mentioned",
    "Early check-in at the hotel",
    "Local taxes (if any)",
    "Tips and gratuities",
    "Anything else not mentioned in the inclusions"
  ],
  "contactDetails": {
    "phone": "+91-9205553343",
    "email": "contact@holidaytribe.com",
    "social": "@holidaytribeworld"
  }
}

conversations = {
}

tools = [
        {
            "type": "function",
            "function": {
                "name": "update_itinerary",
                "description": "Update the existing itinerary based on user changes",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "itinerary": {
                            "type": "string",
                            "description": "The complete itinerary in JSON in str format",
                        },
                        "updated_changes": {
                            "type": "string",
                            "description": "The updated changes from the user in str format",
                        }
                    },
                    "required": ["itinerary", "updated_changes"],
                },
            }
        },
        {
            "type": "function",
            "function": {
                "name": "add_free_day",
                "description": "Adds a free day to the itinerary for personal leisure or exploration",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            }
        },
        # {
        #     "type": "function",
        #     "function": {
        #         "name": "replace_free_day",
        #         "description": "Replaces an existing free day with a new activity",
        #         "parameters": {
        #         "type": "object",
        #         "properties": {
        #             "activity": {
        #             "type": "string",
        #             "description": "The new activity to replace the free day with"
        #             }
        #         },
        #         "required": ["activity"]
        #         }
        #     }   
        # },
        {
            "type": "function",
            "function": {
                "name": "remove_free_day",
                "description": "Removes a previously scheduled free day from the itinerary",
                "parameters": {
                "type": "object",
                "properties": {},
                "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "add_activity",
                "description": "Adds a new activity to the itinerary for the given destination",
                "parameters": {
                "type": "object",
                "properties": {
                    "activity": {
                    "type": "string",
                    "description": "The name or description of the activity to add"
                    },
                    "destination": {
                    "type": "string",
                    "description": "The destination of this trip"
                    },
                },
                "required": ["activity", "destination"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "remove_activity",
                "description": "Removes an activity from the itinerary",
                "parameters": {
                "type": "object",
                "properties": {
                    "activity": {
                    "type": "string",
                    "description": "The name or description of the activity to remove"
                    }
                },
                "required": ["activity"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "reorder_activities",
                "description": "Changes the order of activities on a specific day or across days",
                "parameters": {
                "type": "object",
                "properties": {
                    "activity": {
                    "type": "string",
                    "description": "The name or description of the activity to reorder"
                    },
                    "day": {
                    "type": "string",
                    "description": "The day on which the activity is scheduled"
                    }
                },
                "required": ["activity", "day"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "change_accommodation",
                "description": "Updates the accommodation to a different location or hotel",
                "parameters": {
                "type": "object",
                "properties": {
                    "accommodation": {
                    "type": "string",
                    "description": "The name or description of the new accommodation"
                    }
                },
                "required": ["accommodation"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "upgrade_accommodation",
                "description": "Upgrades the accommodation to a higher category or luxury hotel",
                "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                    "type": "string",
                    "description": "The new category or type of accommodation"
                    }
                },
                "required": ["category"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "downgrade_accommodation",
                "description": "Downgrades the accommodation to a more budget-friendly option",
                "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                    "type": "string",
                    "description": "The new category or type of accommodation"
                    }
                },
                "required": ["category"]
                }
            }
        },
    ]


def generate_user_intentions(natural_language_query: str, complete_itinerary: str, userId: str) -> List[str]:
    """Router Agent"""
    prompt = f""" You are a manager agent of travelling company. Your main task is to understand
    customer query and based on that you should reply back to the customer. 
    You will be provided with complete_itinerary as well to understand the user query.

    For example: If user ask to reduce the number of days in the trip, you should understand that user wants to shorten the trip duration and then you should gather, how many days customer wants for a trip and so on...
    
    User many ask for the following queries:
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
        - You can provide user with brief summary of the itinerary and ask for the changes required.
        - If user ask to add the activity, ask user which day they want to add the activity or extend the trip.
        - Use tools provided to you, only after the confirmation from the user.
    
    complete_itinerary: [complete_itinerary]
    """

    if userId not in conversations:
        conversations[userId] = [{
            "role": "system",
            "content": prompt.replace("[complete_itinerary]", complete_itinerary)
        }]
    
    conversations[userId].append({
        "role": "user",
        "content": f"{natural_language_query}."
    })

    
    response = openai.chat.completions.create(
        model='gpt-4o',
        messages=conversations[userId],
        max_tokens=2000,
        temperature=0,
        tools=tools,
    )
    
    response_message = response.choices[0].message
    result = response_message.content

    if response_message.tool_calls:
        for tool_call in response_message.tool_calls:
            function_name = tool_call.function.name
            if function_name == "update_itinerary":
                function_args = json.loads(tool_call.function.arguments)
                updated_itinerary = update_itinerary(function_args["itinerary"], function_args["updated_changes"])
                print("Updated Itinerary: ", updated_itinerary)

                conversations[userId].append({
                    "role": "assistant",
                    "content": updated_itinerary
                })
            elif function_name == "add_free_day":
                conversations[userId].append({
                    "role": "assistant",
                    "content": "calling add_free_day"
                })
            elif function_name == "replace_free_day":
                conversations[userId].append({
                    "role": "assistant",
                    "content": "calling replace_free_day"
                })
            elif function_name == "remove_free_day":
                conversations[userId].append({
                    "role": "assistant",
                    "content": "calling remove_free_day"
                })
            elif function_name == "add_activity":
                print("calling add_activity")
                function_args = json.loads(tool_call.function.arguments)
                activities = get_acitivities(function_args["activity"], function_args["destination"])
                conversations[userId].append({
                    "role": "assistant",
                    "content": json.dumps(activities)
                })
            elif function_name == "remove_activity":
                conversations[userId].append({
                    "role": "assistant",
                    "content": "calling remove_activity"
                })
            elif function_name == "reorder_activities":
                conversations[userId].append({
                    "role": "assistant",
                    "content": "calling reorder_activities"
                })
            elif function_name == "change_accommodation":
                conversations[userId].append({
                    "role": "assistant",
                    "content": "calling change_accommodation"
                })
            elif function_name == "upgrade_accommodation":
                conversations[userId].append({
                    "role": "assistant",
                    "content": "calling upgrade_accommodation"
                })
            elif function_name == "downgrade_accommodation":
                conversations[userId].append({
                    "role": "assistant",
                    "content": "calling downgrade_accommodation"
                })
            
    else:
        print("No tool calls found in the response.")
        conversations[userId].append({
            "role": "assistant",
            "content": result
        })

    # update conversation to this format [{"user": "query"}, {"assistant": "response"}]
    conversation_history = [(c["role"], c["content"]) if c["role"] == "user" or c["role"] == "assistant" else () for c in conversations[userId]]

    # remove empty objects from the conversation
    conversation_history = [c for c in conversation_history if c]
    return conversation_history

def get_acitivities(acitivity: str, location: str) -> List[str]:
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        cursor = conn.cursor()
        cursor = conn.cursor()

        print("location", location)
        response = openai.embeddings.create(
            input=[f"{acitivity} in {location}"],
            model="text-embedding-ada-002"
         )

        query_embedding = response.data[0].embedding
        query_vector_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

        # get location id
        cursor.execute(f"SELECT id FROM destination WHERE name ILIKE '{location}'")
        row = cursor.fetchone()
        location_id = row[0]

        print("location_id", location_id)

        threshold = 0.5  # Set your desired threshold
        sql = """
            SELECT 
                id, 
                name, 
                description,
                -(embedding <#> %s::vector) as similarity
            FROM must_travel_activity 
            WHERE 
                destination_id = %s 
                AND -(embedding <#> %s::vector) > 0.85  -- Cosine similarity threshold
            ORDER BY similarity DESC
            LIMIT 5;
        """

        cursor.execute(sql, (
            query_vector_str,
            location_id,
            query_vector_str
        ))

        rows = cursor.fetchall()
        activities = []

        for row in rows:
            print(row)
            activity_id = row[0]
            activity_name = row[1]
            activity_desc = row[2]
            distance = row[3]
            print(f"Activity: {activity_name}, Distance: {distance}")
            activities.append(activity_name)

        cursor.close()
        conn.close()
        return activities

def update_itinerary(itinerary: str, updated_response: str) -> str:
    prompt = f"""You are helpful AI assistant for a travel company. 
    Your main task is to understand the itinerary and changes that has been done in the itinerary as "updated_response".
    Update the itinerary based on the user response and provide the updated itinerary to the user.

    original_itinerary: {itinerary}
    changes_required: {updated_response}
    
    updated_itinerary:
    """

    response = openai.chat.completions.create(
        model='gpt-4o',
        messages=[{
            "role": "system",
            "content": prompt
        }],
        max_tokens=1000,
        temperature=0
    )

    return response.choices[0].message.content

def chatbot_interface(user_input, chat_history):
    # Get the response from the backend function
    conversation_history = generate_user_intentions(user_input, json.dumps(itineary), "123")
    print('conversation_history', conversation_history)
    # Update the chat history
    chat_history = conversation_history
    
    # Return updated chat history
    return chat_history, chat_history


custom_css = """
.container {
    max-width: 1200px !important;
    margin: auto;
    padding: 20px;
}
.chatbot-container {
    height: 600px !important;
    overflow-y: auto;
}
.message-box {
    height: 100px !important;
    font-size: 16px !important;
}
"""

with gr.Blocks(css=custom_css) as demo:
    with gr.Column(elem_classes="container"):
        # Header
        gr.Markdown(
            """
            # AI Travel Assistant
            Welcome to your personal travel planning assistant. How can I help you today?
            """
        )
        
        # Chat interface
        with gr.Row():
            with gr.Column(scale=12):
                chatbot = gr.Chatbot(
                    label="Conversation",
                    elem_classes="chatbot-container",
                    height=500,
                    show_label=False,
                )
                
                with gr.Row():
                    # Message input
                    message = gr.Textbox(
                        label="Your message",
                        placeholder="Type your message here...",
                        elem_classes="message-box",
                        show_label=False,
                    )
                    # Send button
                    send_button = gr.Button(
                        "Send",
                        variant="primary",
                        size="lg",
                        scale=0.15,
                    )
        
        # Clear button
        clear_button = gr.Button("Clear Conversation", size="sm")
        
        # Initialize chat history
        chat_history = gr.State([])
        
        # Function to clear chat history
        def clear_chat() -> Tuple[str, List[Tuple[str, str]]]:
            return "", []
        
        # Event handlers
        msg_submit = message.submit(
            chatbot_interface,
            inputs=[message, chat_history],
            outputs=[chatbot, chat_history],
        ).then(
            lambda: "",  # Clear input box after sending
            None,
            message,
        )
        
        send_button.click(
            chatbot_interface,
            inputs=[message, chat_history],
            outputs=[chatbot, chat_history],
        ).then(
            lambda: "",  # Clear input box after sending
            None,
            message,
        )
        
        clear_button.click(
            clear_chat,
            outputs=[message, chatbot],
            show_progress=False,
        )

# Launch the app
if __name__ == "__main__":
    demo.launch()