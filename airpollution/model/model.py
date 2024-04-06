import argparse
import numbers
from pymongo import MongoClient

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.svm import SVR
from sklearn.neighbors import KNeighborsRegressor,KNeighborsClassifier
from sklearn.metrics import mean_squared_error, r2_score

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
def categorizeNumbers(x):
    return categorize(x, "value")

def categorizeCategories(x):
    return categorize(x, "key")

def categorize(x, returnValue):
    #classes according to https://waqi.info/
    categories = {
        "good" : 50,
        "moderate" : 100,
        "unhealthy-for-sensitve-groups" : 150,
        "unhealthy" : 200,
        "very-unhealthy" : 300
    }
    #chose first occuring category
    for key, category in categories.items():
        if x <= category:
            if returnValue == "key":
                return key
            if returnValue == "value":
                return x
    
    if returnValue == "key":
        return "hazardous"
    if returnValue == "value":
        return 400

lng = [lng["lng"] for lng in cleanStations]
lat = [lat["lat"] for lat in cleanStations]
scoreClasses = [int(score["score"]) for score in cleanStations]
categoryClasses = list(map(categorizeNumbers, scoreClasses))
dataX = list(zip(lat, lng))

models = { 
    "Linear Regression": LinearRegression(), 
    "Random Forest Regression": RandomForestRegressor(), 
    "Gradient Boosting Regression": GradientBoostingRegressor(), 
    "SVR": SVR(), 
    "KNR": KNeighborsRegressor(), 
    "KNN": KNeighborsClassifier()
}

def modelScoreComparer(name, mse, r2, testSize, modelSelect, model):
    if (modelSelect["bestMSE"] == -1 or modelSelect["bestMSE"] >= mse) and (modelSelect["bestR2"] == -1 or modelSelect["bestR2"] <= r2):
        modelSelect["bestMSE"] = mse
        modelSelect["bestR2"] = r2
        modelSelect["modelName"] = name
        modelSelect["testSize"] = testSize
        modelSelect["model"] = model
    return modelSelect

def modelSelector(x,y, models, randomState=50, testSizeStart = 0.01, testSizeEnd = 0.9, steps = 0.01):
    #do not allow to large testing data
    if testSizeEnd > 0.95:
        testSizeEnd = 0.95
    bestModel = {"modelName" : "", "bestMSE" : -1, "bestR2" : -1, "testSize": testSizeStart, "model" : -1}
    while testSizeStart <= testSizeEnd:
        bestModel = modelTypeComparer(x,y, models, testSize=testSizeStart, randomState=randomState, modelSelect=bestModel)
        testSizeStart = testSizeStart + steps
    return bestModel

def modelTypeComparer(x,y, models, modelSelect, testSize=0.1, randomState=50):
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=testSize, random_state=randomState)
    for name, model in models.items():
        model.fit(x_train, y_train)
        y_pred = model.predict(x_test)
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        modelSelect = modelScoreComparer(name, mse, r2, testSize, modelSelect, model)
    return modelSelect

scoreModelInfos = modelSelector(dataX, scoreClasses, models, randomState=300, testSizeStart = 0.1, testSizeEnd = 1, steps = 0.05)
scoreModel = scoreModelInfos["model"]

categoryModelInfos = modelSelector(dataX, categoryClasses, models, randomState=320, testSizeStart = 0.1, testSizeEnd = 1, steps = 0.05)
categoryModel = categoryModelInfos["model"]


#save the model
import pickle

# save the classifier
with open('score-model.pkl', 'wb') as fid:
    pickle.dump(scoreModel, fid)
    print(f'The following Model has been uploaded: {scoreModelInfos}')

with open('category-model.pkl', 'wb') as fid:
    pickle.dump(categoryModel, fid)
    print(f'The following Model has been uploaded: {categoryModelInfos}')

exit()

#define K
roundedRoot = round(pow(len(cleanStations), 0.5))
k = roundedRoot if roundedRoot % 2 == 0 else roundedRoot - 1


scoreKNN = KNeighborsClassifier(k)

scoreKNN.fit(data, scoreClasses)

new_geo = [46.757408, 8.756327]
new_lat = new_geo[0]
new_lng = new_geo[1]
new_point = [(new_lat, new_lng)]

scorePrediction = scoreKNN.predict(new_point)
print(f'https://api.waqi.info/feed/geo:{new_lat};{new_lng}/?token=<your_token>')
print(scorePrediction)


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
