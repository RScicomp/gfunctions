from google.cloud import secretmanager
from google.cloud import secretmanager

def access_secret():
    client = secretmanager.SecretManagerServiceClient()
    secret_name = "projects/874307578992/secrets/openai_api_key/versions/latest"#f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    
    # Access the secret version
    response = client.access_secret_version(name=secret_name)
    # Return the secret payload
    return response.payload.data.decode('UTF-8')

def access_youtube_secret():
    client = secretmanager.SecretManagerServiceClient()
    secret_name = f"projects/874307578992/secrets/youtube_api_key/versions/latest"
    response = client.access_secret_version(name=secret_name)
    return response.payload.data.decode('UTF-8')
