import requests
from pprint import pprint

response = requests.post("https://igcse-predict.herokuapp.com/generate",
                         json={
                             "topics": [
                                 "1 The particulate nature of matter",
                                 "2 Experimental techniques",
                                 "3 Atoms, elements and compounds",
                             ],
                             "options": [22, 42, 62],
                         },
                         timeout = 600)
pprint(response.json())