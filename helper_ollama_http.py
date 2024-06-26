import requests

def get_ollama_models(server_url):
    """
    Retrieve the list of models available in Ollama using its HTTP API.

    Args:
    - server_url (str): The URL of the Ollama server (e.g., http://localhost:11434)

    Returns:
    - list: A list of dictionaries containing model details.
    - None: If an error occurs during the request.
    """
    ollama_api_url = f"{server_url}/api/tags"
    
    try:
        # Send a GET request to the API endpoint
        response = requests.get(ollama_api_url)
        # Raise an exception for HTTP errors
        response.raise_for_status()
        
        # Parse the JSON response
        data = response.json()
        models = data.get('models', [])
        return models
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except Exception as err:
        print(f"An error occurred: {err}")
    return None

def get_ollama_model_names(server_url):
    """
    Retrieve the list of model names available in Ollama using its HTTP API.

    Args:
    - server_url (str): The URL of the Ollama server (e.g., http://localhost:11434)

    Returns:
    - list: A list of model names.
    - None: If an error occurs during the request.
    """
    models = get_ollama_models(server_url)
    if models is not None:
        return [model['name'] for model in models]
    return None

# Example usage:
server_url = "http://localhost:11434"  # Replace with the actual address of the Ollama server

# Get detailed model information
models = get_ollama_models(server_url)
if models is not None:
    print("List of models:")
    for model in models:
        print(f"Name: {model['name']}")
        print(f"Model: {model['model']}")
        print(f"Modified At: {model['modified_at']}")
        print(f"Size: {model['size']}")
        print(f"Digest: {model['digest']}")
        print("Details:")
        for key, value in model['details'].items():
            print(f"  {key}: {value}")
        print("\n")
else:
    print("Failed to retrieve models.")

