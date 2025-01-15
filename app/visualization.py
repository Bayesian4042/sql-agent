import psycopg2
import numpy as np
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import pandas as pd
import plotly.express as px
import os
from dotenv import load_dotenv
import ast

load_dotenv()

def parse_postgres_array(array_str):
    """
    Parse a PostgreSQL array string into a numpy array.
    Handles both {1,2,3} format and [1,2,3] format.
    """
    # Remove any 'array' prefix if present
    array_str = array_str.replace('array', '')
    
    # Convert string to list
    try:
        # Try parsing as a regular string representation of a list
        array_str = array_str.strip('{}[]')
        values = [float(x.strip()) for x in array_str.split(',') if x.strip()]
        return np.array(values)
    except ValueError:
        # If that fails, try using ast.literal_eval
        try:
            return np.array(ast.literal_eval(array_str))
        except:
            raise ValueError(f"Could not parse array string: {array_str}")

def visualize_embeddings(
    db_params,
    table_name,
    embedding_column,
    label_column=None,
    reduction_method='pca',
    n_components=2
):
    """
    Visualize embeddings stored in PostgreSQL using dimensionality reduction.
    
    Parameters:
    - db_params: dict with keys 'dbname', 'user', 'password', 'host', 'port'
    - table_name: name of the table containing embeddings
    - embedding_column: name of the column containing the embedding arrays
    - label_column: optional column name for color-coding points
    - reduction_method: 'pca' or 'tsne'
    - n_components: number of dimensions to reduce to (2 or 3)
    """
    # Connect to PostgreSQL
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cursor = conn.cursor()
    
    # Fetch embeddings and labels
    if label_column:
        cursor.execute(f"SELECT {embedding_column}, {label_column} FROM {table_name}")
        rows = cursor.fetchall()
        embeddings = []
        labels = []
        for emb_str, label in rows:
            try:
                embeddings.append(parse_postgres_array(emb_str))
                labels.append(label)
            except ValueError as e:
                print(f"Skipping malformed embedding: {e}")
    else:
        cursor.execute(f"SELECT {embedding_column} FROM {table_name}")
        rows = cursor.fetchall()
        embeddings = []
        labels = None
        for (emb_str,) in rows:
            try:
                embeddings.append(parse_postgres_array(emb_str))
            except ValueError as e:
                print(f"Skipping malformed embedding: {e}")
    
    # Convert embeddings to numpy array
    X = np.array(embeddings)
    
    # Apply dimensionality reduction
    if reduction_method.lower() == 'pca':
        reducer = PCA(n_components=n_components)
    else:  # t-SNE
        reducer = TSNE(n_components=n_components, random_state=42, perplexity=2)
    
    reduced_embeddings = reducer.fit_transform(X)
    
    # Create DataFrame for plotting
    plot_data = pd.DataFrame(
        reduced_embeddings,
        columns=[f'Component {i+1}' for i in range(n_components)]
    )
    
    if labels:
        plot_data['Label'] = labels
    
    # Create interactive plot
    if n_components == 3:
        fig = px.scatter_3d(
            plot_data,
            x='Component 1',
            y='Component 2',
            z='Component 3',
            color='Label' if labels else None,
            title=f'Embedding Visualization using {reduction_method.upper()}'
        )
    else:
        fig = px.scatter(
            plot_data,
            x='Component 1',
            y='Component 2',
            color='Label' if labels else None,
            title=f'Embedding Visualization using {reduction_method.upper()}'
        )
    
    # Close database connection
    cursor.close()
    conn.close()
    
    return fig

# Example usage:
if __name__ == "__main__":
    db_params = {
        'dbname': 'your_database',
        'user': 'your_username',
        'password': 'your_password',
        'host': 'localhost',
        'port': '5432'
    }
    
    fig = visualize_embeddings(
        db_params=db_params,
        table_name='must_travel_activity',
        embedding_column='embedding',
        label_column='name',  # Optional
        reduction_method='tsne',   # or 'tsne'
        n_components=3          # or 3 for 3D visualization
    )
    
    # Display the plot
    fig.show()