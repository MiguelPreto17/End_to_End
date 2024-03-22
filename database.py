import os
import requests

# Function to handle file uploads

def upload_latest_file(directory_path):
    files = os.listdir(directory_path)
    if not files:
        print("No files found in the directory.")
        return

    # Ordena os arquivos por data de modificação
    files.sort(key=lambda x: os.path.getmtime(os.path.join(directory_path, x)), reverse=True)

    latest_file = files[0]
    file_path = os.path.join(directory_path, latest_file)

    print(f"Uploading {latest_file}...")
    upload_url = 'http://10.61.6.197:8001/api/v1/files/upload'
    try:
        with open(file_path, 'rb') as file:
            files = {'file': (latest_file, file)}
            response = requests.post(upload_url, files=files)
            response.raise_for_status()
            print(f"{latest_file} uploaded successfully.")
    except requests.HTTPError as e:
        print(f"HTTP error during file upload for {latest_file}: {e}")
        print(f"Response body: {response.text}")
    except Exception as e:
        print(f"Error during file upload for {latest_file}: {e}")

"""def upload_files(directory_path):
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
                print(f"Error during file upload for {filename}: {e}")"""