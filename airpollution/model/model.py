import argparse
import numbers
from pymongo import MongoClient

parser = argparse.ArgumentParser(description='Create Model')
parser.add_argument('-u', '--uri', required=True, help="mongodb uri with username/password")
args = parser.parse_args()

mongo_uri = args.uri
mongo_db = "airpollutionStations"
mongo_collection = "airpollutionStations"

client = MongoClient(mongo_uri)
db = client[mongo_db]
collection = db[mongo_collection]

cleanStations = []
keysToCheck = ["geo", "current-score"]
# fetch all documents
stations = collection.find({})
countStations = 0
for station in stations:
    countStations = countStations + 1
    #check keys
    if not all(key in station for key in keysToCheck):
        continue
    #invalid value
    if station["current-score"] == "-":
        continue
    #check "sub"-keys
    if type(station["geo"]) is not dict and "lat" not in station["geo"] and "lng" not in station["geo"]:
        continue
    lat = station["geo"]["lat"]
    lng = station["geo"]["lng"]
    #invalid values
    if not isinstance(lat, numbers.Number) and not isinstance(lng, numbers.Number):
        continue
    #check for impossible extremes
    #latitude can only be between -90 and 90
    #longitude can only be between -180 and 180
    if (lat < -90 or lat > 90) or lng < -180 or lng > 180:
        continue 
    #cleansed data store
    cleanStations.append({"score" : station["current-score"], "lat" : lat, "lng" : lng})

filteredStations = countStations - len(cleanStations)
print(f'filtered {filteredStations} out of {countStations} Stations')

#model
#Three lines to make our compiler able to draw:
import sys
import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
from sklearn.neighbors import KNeighborsClassifier

lng = [lng["lng"] for lng in cleanStations]
lat = [lat["lat"] for lat in cleanStations]
scoreClasses = [score["score"] for score in cleanStations]

roundedRoot = round(pow(len(cleanStations), 0.5))
k = roundedRoot if roundedRoot % 2 == 0 else roundedRoot - 1

data = list(zip(lat, lng))
scoreKNN = KNeighborsClassifier(k)

scoreKNN.fit(data, scoreClasses)

new_geo = [46.757408, 8.756327]
new_lat = new_geo[0]
new_lng = new_geo[1]
new_point = [(new_lat, new_lng)]

scorePrediction = scoreKNN.predict(new_point)
print(f'https://api.waqi.info/feed/geo:{new_lat};{new_lng}/?token=6209ace39368f2a7b8e4aedd47087ac650dc4b04')
print(scorePrediction)

def categorize(x):
    #classes according to https://waqi.info/
    categories = {
        "good" : 50,
        "moderate" : 100,
        "unhealthy-for-sensitve-groups" : 150,
        "unhealthy" : 200,
        "very-unhealthy" : 300
    }
    for key, category in categories.items():
        if int(x) <= category:
            return key
    return "hazordous"

categoryClasses = list(map(categorize, scoreClasses))
categoryKNN = KNeighborsClassifier(k)
categoryKNN.fit(data, categoryClasses)
categoryPrediction = categoryKNN.predict(new_point)
print(categoryPrediction)
"""
plt.scatter(lng + [new_lng], lat + [new_lat], c=scoreClasses + [scorePrediction[0]])
plt.text(x=new_lng-1.7, y=new_lat-0.7, s=f"new point, class: {scorePrediction[0]}")
plt.show()

#Two  lines to make our compiler able to draw:
plt.savefig(sys.stdout.buffer)
sys.stdout.flush()
"""
#save the model
import pickle

# save the classifier
with open('score-knn.pkl', 'wb') as fid:
    pickle.dump(scoreKNN, fid) 

with open('category-knn.pkl', 'wb') as fid:
    pickle.dump(categoryKNN, fid)
