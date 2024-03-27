# python -m flask --debug --app backend run (works also in PowerShell)

import os
import pickle

#from dotenv import load_dotenv
#import pandas as pd
from azure.storage.blob import BlobServiceClient
from flask import Flask, jsonify, request, send_file

# Another way to load environment variables using an .env file
#load_dotenv()

# Access the API key using the variable name defined in the .env file
#connectionString = os.getenv("azureConnectionString")
def getModelByContainerName(containerName):
    # get modelDirpaths
    modelDirPathString = "../model/"
    workingDirectory = os.getcwd()
    currentPath = os.path.dirname(os.path.realpath(__file__))
    os.chdir(currentPath)
    if not os.path.isdir(modelDirPathString):
        os.mkdir(modelDirPathString)
    os.chdir(modelDirPathString)
    modelDirPath = os.getcwd()
    #reset workingDirectory
    os.chdir(workingDirectory)

    # init app, load model from storage
    print("*** Init and load model ***")
    # using .env variable 
    #if connectionString:
    if 'AZURE_STORAGE_CONNECTION_STRING' in os.environ:
        connectionString = os.environ['AZURE_STORAGE_CONNECTION_STRING']
        blob_service_client = BlobServiceClient.from_connection_string(connectionString)

        print("fetching blob containers...")
        containers = blob_service_client.list_containers(include_metadata=True)
        for container in containers:
            existingContainerName = container['name']
            print("checking container " + existingContainerName)
            if existingContainerName.startswith(containerName):
                parts = existingContainerName.split("-")
                print(parts)
                suffix = 1
                if (len(parts) == 3):
                    newSuffix = int(parts[-1])
                    if (newSuffix > suffix):
                        suffix = newSuffix

        container_client = blob_service_client.get_container_client(containerName + "-" + str(suffix))
        blob_list = container_client.list_blobs()
        for blob in blob_list:
            print("\t" + blob.name)

        # Download the blob to a local file
        if not os.path.isdir(modelDirPath):
            os.mkdir(modelDirPath)
        #Path("../model").mkdir(parents=True, exist_ok=True)
        download_file_path = os.path.join(modelDirPath, containerName + ".pkl")
        print("\nDownloading blob to \n\t" + download_file_path)

        with open(file=download_file_path, mode="wb") as download_file:
            download_file.write(container_client.download_blob(blob.name).readall())

    else:
        print("CANNOT ACCESS AZURE BLOB STORAGE - Please set connection string as env variable")

    modelFilePath = f'{modelDirPath}/{containerName}.pkl'

    with open(modelFilePath, 'rb') as fid:
        model = pickle.load(fid)
    return model

#get models
#better to create the models beforehand, instead of creating them with every request
categoryModel = getModelByContainerName("category-knn")
scoreModel = getModelByContainerName("score-knn")

print("*** Init Flask App ***")
app = Flask(__name__, static_url_path='/', static_folder='../frontend')

@app.route("/")
def indexPage():
     return send_file("../frontend/index.html")  

@app.route("/api/predict")
def predict():
    lat = request.args.get('lat', default = 0, type = float)
    lng = request.args.get('lng', default = 0, type = float)
    if lat < -90 or lat > 90:
        return jsonify({
            'error' : 'latitude has to be between -90 and 90'
        })
    if lng < -180 or lng > 180:
        return jsonify({
            'error' : 'longitude has to be between -180 and 180'
        })
    newPoint = [(lat, lng)]
    
    categoryPrediction = categoryModel.predict(newPoint)
    scorePrediction = scoreModel.predict(newPoint)

    return jsonify({
        'category': categoryPrediction[0],
        'score': scorePrediction[0],
        'lat' : lat,
        'lng' : lng
    })