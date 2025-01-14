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

load_dotenv()

# Initialize OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

itineary = {
    "inclusions": {
        "airfare": "Return Economy",
        "hotel_stay": "6 Nights in Ubud & Seminyak (****hotel)",
        "meals": "6 Breakfasts",
        "transfers": {
            "airport": "Return private airport transfers",
            "surface_travel": "By AC vehicle",
            "intercity": "Private transfer from Ubud to Seminyak"
        },
        "tours": [
            "Kintamani volcano tour",
            "Tanah Lot and Uluwatu tour",
            "Benoa water sports"
        ],
        "insurance": "Travel Insurance",
        "taxes": [
            "GST",
            "TCS"
        ]
    },
    "itinerary": {
        "day_1": {
            "description": "Arrival in Bali",
            "activities": [
                "Meet and Greet at the airport",
                "Transfer to hotel in Ubud",
                "Day at leisure depending on flight arrival",
                "Overnight at hotel"
            ]
        },
        "day_2": {
            "description": "Kintamani Volcano Tour",
            "activities": [
                "Buffet breakfast at the hotel",
                "Kintamani Volcano Tour with Ubud Village (Private Transfer)",
                "Overnight at hotel"
            ]
        },
        "day_3": {
            "description": "Free Day for Self Exploration",
            "activities": [
                "Buffet breakfast at the hotel",
                "Day is free for customization",
                "Holiday Tribe assistance available for planning the day",
                "Overnight at hotel"
            ]
        },
        "day_4": {
            "description": "Transfer from Ubud to Seminyak",
            "activities": [
                "Buffet breakfast at the hotel",
                "Private transfer from Ubud hotel to Seminyak hotel",
                "Overnight at hotel"
            ]
        },
        "day_5": {
            "description": "Tanah Lot and Uluwatu Tour",
            "activities": [
                "Buffet breakfast at the hotel",
                "Tanah Lot Tour followed by Uluwatu Sunset Tour (Private Transfer)",
                "Overnight at hotel"
            ]
        },
        "day_6": {
            "description": "Benoa Water Sports",
            "activities": [
                "Buffet breakfast at the hotel",
                "Benoa Water Sports Tour (Half Day, Private Transfer)",
                "Overnight at hotel"
            ]
        },
        "day_7": {
            "description": "Departure",
            "activities": [
                "Buffet breakfast at the hotel",
                "Private departure transfer to Bali airport",
                "Return flight to India"
            ]
        }
    },
    "tour_highlights": [
        "Benoa water sports",
        "Kintamani Volcano tour",
        "Tanah Lot & Uluwatu tour"
    ],
    "contact_details": {
        "phone": "+91-9205553343",
        "email": "contact@holidaytribe.com",
        "social_media": "@holidaytribeworld"
    },
    "exclusions": [
        "Seat selection and meal costs on low-cost flights",
        "Visa cost",
        "Sightseeing not mentioned in the itinerary",
        "Meals other than mentioned in the itinerary",
        "Early hotel check-in",
        "Local taxes (if any)",
        "Tips and gratuities",
        "Anything else not mentioned in the itinerary and inclusions",
        "Shared SIC transfers (vehicle shared with other travelers)",
        "Point-to-point private transfers (not car at disposal)"
    ],
    "hotel_details": [
        "Ashoka Tree Resort",
        "d'primahotel Petitenget",
        "Hula Hula Resort Ao Nang, Krabi (on similar basis)"
    ]
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
        }
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
        - Use tool update_itinerary only after taking confirmation of changes in the itinerary.
    
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
        model='gpt-4o-mini',
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