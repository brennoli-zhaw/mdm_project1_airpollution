import argparse
import json
import os
from concurrent.futures import ProcessPoolExecutor

from pymongo import MongoClient


def to_document(base_dir, item):
    try:
        return item
            
    except Exception as e:
        print("Could not read {}".format(item["files"][0]), e)
        return None


class JsonLinesImporter:

    def __init__(self, file, mongo_uri, batch_size=30, db='airpollutionStations', collection='airpollutionStations'):
        self.file = file
        self.base_dir = os.path.dirname(file)
        self.batch_size = batch_size
        self.client = MongoClient(mongo_uri)
        self.db = db
        self.collection = collection

    def read_lines(self):
        with open(self.file, encoding='UTF-8') as f:
            batch = []
            for line in f:
                batch.append(json.loads(line))
                if len(batch) == self.batch_size:
                    yield batch
                    batch.clear()
            yield batch

    def save_to_mongodb(self):
        db = self.client[self.db]
        collection = db[self.collection]
        #only "live" data is relevant 
        collection.delete_many({})
        for idx, batch in enumerate(self.read_lines()):
            print("inserting batch", idx)
            collection.insert_many(self.prepare_documents(batch))

    def prepare_documents(self, batch):
        documents = []
        with ProcessPoolExecutor() as executor:
            for document in executor.map(to_document, [self.base_dir] * len(batch), batch):
                if document is not None:
                    documents.append(document)
        return documents


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--uri', required=True, help="mongodb uri with username/password")
    parser.add_argument('-i', '--input', required=True, help="input file in JSON Lines format")
    parser.add_argument('-c', '--collection', required=True, help="name of the mongodb collection where the airpollutionStations should be stored")
    args = parser.parse_args()
    importer = JsonLinesImporter(args.input, collection=args.collection, mongo_uri=args.uri)
    importer.save_to_mongodb()
