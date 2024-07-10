import requests

url = 'http://127.0.0.1:8000/enrol_users_from_csv/'
files = {'file': open('path/to/estudiantes_validados.csv', 'rb')}

response = requests.post(url, files=files)

print(response.json())