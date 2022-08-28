import requests
from pprint import pprint

response = requests.post(
    "https://dev-igcse-backend-gunguny119.endpoint.ainize.ai/generate",
    json={
        "subject":
            "Chemistry",
        "topics": [
            "1 The particulate nature of matter",
            "2 Experimental techniques",
            "3 Atoms, elements and compounds",
            "11 Air and water",
            "14 Organic chemistry",
        ],
    },
    timeout=600)
pprint(response.json())