import os
import requests

# Function to handle file uploads
def upload_files(directory_path):
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        if os.path.isfile(file_path):
            print(f"Uploading {filename}...")
            upload_url = 'http://10.61.6.197:8001/api/v1/files/upload'
            try:
                with open(file_path, 'rb') as file:
                    files = {'file': (filename, file)}
                    response = requests.post(upload_url, files=files)
                    response.raise_for_status()
                    print(f"{filename} uploaded successfully.")
            except requests.HTTPError as e:
                print(f"HTTP error during file upload for {filename}: {e}")
                print(f"Response body: {response.text}")
            except Exception as e:
                print(f"Error during file upload for {filename}: {e}")