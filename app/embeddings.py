import os
from openai import OpenAI
import psycopg2
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set your OpenAI API key
client =  OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Connect to PostgreSQL
connection = psycopg2.connect(os.getenv("DATABASE_URL"))

cursor = connection.cursor()

# 1. Fetch all rows from your existing 'documents' table
cursor.execute("SELECT mta.id, mta.name, mta.description, d.name as destination_name FROM must_travel_activity mta JOIN destination d ON mta.destination_id = d.id;")
rows = cursor.fetchall()

for row in rows:
    doc_id = row[0]
    name = row[1]
    description = row[2]
    destination_name = row[3]

    print("name: ", name)
    print("description: ", description)
    print("destination_name: ", destination_name)

    # 2. Generate embedding for the content
    response = client.embeddings.create(
        input=[f"{name}, {description} in {destination_name}"],
        model="text-embedding-ada-002"
    )

    embedding_vector = response.data[0].embedding  # This is a list of floats

    # 3. Update the 'documents' table with the embedding
    #    or insert into the dedicated 'document_embeddings' table
    #    For example, if the embedding column is on the same table:
    sql_update = """
        UPDATE must_travel_activity
        SET embedding = %s
        WHERE id = %s
    """
    cursor.execute(sql_update, (embedding_vector, doc_id))

# Commit changes and close connection
connection.commit()
cursor.close()
connection.close()
