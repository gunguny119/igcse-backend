import os
from flask import Flask, request
from flask_cors import CORS
import pandas as pd
import firebase_admin
from firebase_admin import credentials
from firebase_admin import storage

from app.save_to_pdf import process_pdf

app = Flask(__name__)  #opening up app
CORS(app)

cred = credentials.Certificate('igcse-predict-c18eb87031fd.json')
firebase_admin.initialize_app(cred, {'storageBucket': 'igcse-predict.appspot.com'})

bucket = storage.bucket()

cur_path = os.path.dirname(__file__)
#load data
all_df = {}

for subject in ['chemistry', 'physics', 'biology']:
    df = pd.read_csv(f'{cur_path}/../data/{subject}_data.csv')
    df = df[~df['screenshot_path'].isna()]

    grade_threshold = pd.read_csv(f'{cur_path}/../data/{subject}_grade_thresholds.csv')
    grade_threshold[['A*', 'A', 'B', 'C', 'D', 'E', 'F', 'G'
                    ]] = grade_threshold[['A*', 'A', 'B', 'C', 'D', 'E', 'F', 'G']] / 200
    grade_threshold = grade_threshold[['A*', 'A', 'B', 'C', 'D', 'E', 'F', 'G']].mean()

    all_df[subject] = {'df': df, 'grade_threshold': grade_threshold}

#https://www, if we have /generate, send our data to the url
APP_ROOT = os.getenv('APP_ROOT', '/generate')


@app.route(APP_ROOT, methods=["POST"])
def generate_pastpaper():
    data = request.json
    topic_list = data.get('topics')
    options = data.get('options')  # 21, 41, 61...
    subject = data.get('subject')

    df = all_df[subject.lower()]['df']
    grade_threshold = all_df[subject.lower()]['grade_threshold']

    topic_df = df[df['topic'].isin(topic_list) | (df['component'] == options[2])]

    component2 = topic_df[topic_df['component'] == options[0]]
    component4 = topic_df[topic_df['component'] == options[1]]
    component6 = topic_df[topic_df['component'] == options[2]]

    component2_questions = []
    for i in range(1, 41):
        q = component2[component2['question number'] == i]
        if len(q) == 0:
            continue
        component2_questions.append(q.sample(1))

    component4_questions = []
    for i in range(1, 12):
        q = component4[component4['question number'] == i]
        if len(q) == 0:
            continue
        component4_questions.append(q.sample(1))

    component6_questions = []
    for i in range(1, 5):
        q = component6[component6['question number'] == i]
        if len(q) == 0:
            continue
        component6_questions.append(q.sample(1))

    component2 = pd.concat(component2_questions)
    component4 = pd.concat(component4_questions)
    component6 = pd.concat(component6_questions)

    images = {
        'component2': component2['screenshot_path'].to_list(),
        'component4': component4['screenshot_path'].to_list(),
        'component6': component6['screenshot_path'].to_list()
    }

    component2_pdf, num_questions = process_pdf(images['component2'], bucket, subject,
                                                topic_list, options[0])
    component4_pdf, _ = process_pdf(images['component4'], bucket, subject, topic_list,
                                    options[1])
    component6_pdf, _ = process_pdf(images['component6'], bucket, subject, topic_list,
                                    options[2])

    component2_ms = component2['answer'].to_list()
    component4_ms, _ = process_pdf(component4['ms_path'].to_list(),
                                   bucket,
                                   subject,
                                   topic_list,
                                   options[1],
                                   ms=True)
    component6_ms, _ = process_pdf(component6['ms_path'].to_list(),
                                   bucket,
                                   subject,
                                   topic_list,
                                   options[2],
                                   ms=True)

    pdfs = {
        'component2': component2_pdf,
        'component4': component4_pdf,
        'component6': component6_pdf,
    }

    marking_schemes = {
        'component2': component2_ms,
        'component4': component4_ms,
        'component6': component6_ms,
    }

    marks = {
        'component2': num_questions,
        'component4': component4["marks"].sum(),
        'component6': component6["marks"].sum(),
    }

    total_marks = marks['component2'] * 1.5 + marks['component4'] * 1.25 + marks[
        'component6']
    threshold = grade_threshold * total_marks

    rounded = []
    for n in threshold:
        rounded.append(round(n))

    response = {
        'pdfs': pdfs,
        'grade_thresholds': rounded,
        'marking_schemes': marking_schemes
    }

    return response
