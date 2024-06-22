import sys
import os
import requests

UPLOAD_URL = 'http://192.168.56.107:5000/upload'
INSTALL_URL = 'http://192.168.56.107:5000/install'
CLEAR_URL = 'http://192.168.56.107:5000/clear'

def clear_upload_folder():
    try:
        response = requests.post(CLEAR_URL, timeout=10)
        if response.status_code == 200:
            print("Upload folder successfully cleared.")
        else:
            print(f"Failed to clear upload folder: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Exception during clearing upload folder: {e}")


def upload_files(files, url):
    with requests.Session() as session:
        for file in files:
            with open(file, 'rb') as f:
                print(f'Uploading {file} to {url}')
                try:
                    response = session.post(url, files={'file': f}, timeout=10)
                    if response.status_code == 200:
                        print(f"Successfully uploaded {file}")
                    else:
                        print(f"Failed to upload {file}: {response.status_code} - {response.text}")
                except requests.exceptions.RequestException as e:
                    print(f"Exception during upload: {e}")

def install_driver(url):
    try:
        print(f'Installing driver from {url}')
        response = requests.post(url, timeout=25)
        if response.status_code == 200:
            print("Driver successfully installed.")
        else:
            print(f"Failed to install driver: {response.status_code} - {response.json().get('error')}")
    except requests.exceptions.RequestException as e:
        print(f"Exception during installation: {e}")

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: python client.py <path_to_inf> <path_to_sys> <path_to_cat>")
        sys.exit(1)

    inf_path = sys.argv[1]
    sys_path = sys.argv[2]
    cat_path = sys.argv[3]

    files = [inf_path, sys_path, cat_path]

    clear_upload_folder()
    upload_files(files, UPLOAD_URL)
    install_driver(INSTALL_URL)