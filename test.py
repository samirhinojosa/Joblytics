import requests
# from bs4 import BeautifulSoup

title = "Data Engineer"
location = "Paris"

list_url = "https://www.linkedin.com/jobs/search?keywords=Data%20Engineer&location=France&position=1&pageNum=0"
response = requests.get(list_url)

print(response.text)
