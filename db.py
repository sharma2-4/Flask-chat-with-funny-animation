from bson import ObjectId
from pymongo import DESCENDING, MongoClient
from werkzeug.security import generate_password_hash
from user import User
from datetime import datetime


client = MongoClient("mongodb+srv://HaiChat:haichat@cluster0.qjsvxia.mongodb.net/")

chat_db = client.get_database("HaiChat")
user_collection = chat_db.get_collection("users")
rooms_collection = chat_db.get_collection("rooms")
room_members_collection = chat_db.get_collection("room_members")
messages_collection = chat_db.get_collection("messages")

user_collection.create_index([('id', 1)], unique=True)

def save_user(username, email, password):
    password_hash = generate_password_hash(password)
    try:
        user_collection.insert_one({
            'id': username,
            'email': email,
            'password': password_hash,
        })
    except Exception as e:
        print(f"Error saving user: {e}")

def get_user(username):
    user_data = user_collection.find_one({'id': username})
    if user_data:
        return User(user_data['id'], user_data['email'], user_data['password'])
    else:
        return None

def save_room(room_name,created_by ):
    room_id = rooms_collection.insert_one({'name':room_name,'created_by':created_by,'created_at':datetime.now()}).inserted_id
    add_room_memeber(room_id,room_name,created_by,created_by,is_room_admin=True)
    return room_id

def update_room(room_id, room_name):
    rooms_collection.update_one({'_id': ObjectId(room_id)}, {'$set': {'name': room_name}})
    room_members_collection.update_many({'_id.room_id':ObjectId(room_id)},{'$set':{'room_name':room_name}})

def add_room_memeber(room_id,room_name,username,added_by,is_room_admin=False):
    room_members_collection.insert_one({'_id':{'room_id':ObjectId(room_id),'username':username},
                                        'added_by':added_by,'added_at':datetime.now(),
                                        'is_room_admin':is_room_admin,'room_name':room_name
                                        })
    
def add_room_members(room_id,room_name,usernames,added_by):
    room_members_collection.insert_many( [ {'_id':{'room_id':ObjectId(room_id),'username':username},
                                        'added_by':added_by,'added_at':datetime.now(),
                                        'is_room_admin':False,'room_name':room_name
                                        } for username in usernames ])
    
def get_room(room_id):
    return rooms_collection.find_one({'_id':ObjectId(room_id)})

def get_room_members(room_id):
  return list(room_members_collection.find({'_id.room_id':ObjectId(room_id)}))

def get_room_for_user(username):   
   return list(room_members_collection.find({'_id.username':username}))

def is_room_member(room_id,username):
    return room_members_collection.count_documents({'_id':{'room_id':ObjectId(room_id),"username":username}})

def is_room_admin(room_id,username):
       return room_members_collection.count_documents({'_id':{'room_id':ObjectId(room_id),"username":username},'is_room_admin':True})
 
def remove_room_members(room_id,usernames):
    room_members_collection.delete_many({'_id':{'$in': [{'room_id':room_id,'username':username} for username in usernames]}})

def save_message(room_id,text,sender):
    messages_collection.insert_one({'room_id':room_id,'text':text,'sender':sender,'created_at':datetime.now()})


MESSAGE_FETCH_LIMIT = 3

def get_messages(room_id, page=0):
    offset = page * MESSAGE_FETCH_LIMIT
    messages = list(
        messages_collection.find({'room_id': room_id}).sort('_id', DESCENDING).limit(MESSAGE_FETCH_LIMIT).skip(offset))
    for message in messages:
        message['created_at'] = message['created_at'].strftime("%d %b, %H:%M")
    return messages[::-1]