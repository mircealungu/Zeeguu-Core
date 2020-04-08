import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from elasticsearch import Elasticsearch
from pandasticsearch import Select

list_of_paths = ['cake_30_users_english.csv', 'topics_only_30_users.csv', 'user_30_test_sentence_english.csv',
                 'user_30_test_trump_danish.csv']

for path in list_of_paths:
    df = pd.read_csv(path)
    df = df.loc[(df['Difficulty'] == 5)]
    df = df.groupby(['Index', 'Asked for articles'])['Time in MS'].mean().reset_index()
    df.to_csv(path + str(1), encoding='utf-8', index=False)
