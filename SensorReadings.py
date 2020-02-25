import json
from bson import json_util
import bottle
from bottle import post, request
from pymongo import MongoClient


connection = MongoClient('localhost',27017)
db = connection['remotesensor']
collection = db['readings']

@post('/reading')
def enter_reading():
  data = request.json
  q_result_id = collection.insert_one(data).inserted_id
  if collection.find_one({"_id":q_result_id}) == None:
    return "<p>Error entering reading<p>\n"
  else:
    return "<p>Reading Entered<>p>\n"

if __name__ == '__main__':
  #app.run(debug=True)
  run(host='192.168.0.231', port=8080)