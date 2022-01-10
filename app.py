from flask import Flask
from flask import jsonify
from flask import abort
from flask import make_response
from flask import url_for
from flask import request
from flask import render_template
from flask import redirect
from flask import session
from time import gmtime
from time import strftime
from flask_pymongo import PyMongo
import json
import sqlite3
import datetime
from flask_cors import CORS, cross_origin
from pymongo import MongoClient
import random
import bcrypt
from flask_mongoalchemy import MongoAlchemy

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR']= False
CORS(app)
app.config.from_object(__name__)
app.secret_key = 'key'

connection = MongoClient("mongodb://localhost:27017/")
app.config['MONGOALCHEMY_DATABASE'] = 'app'
app.config['MONGOALCHEMY_CONNECTION_STRING'] = 'mongodb://localhost:27017/'
app.config["MONGO_URI"] = 'mongodb://localhost:27017/'
mongo=PyMongo(app)

# Adding tweets
def add_tweet(new_tweet):
    api_list=[]
    print (new_tweet)
    db_user = connection.cloud_native.users
    db_tweet = connection.cloud_native.tweets

    user = db_user.find({"username":new_tweet['tweetedby']})
    for i in user:
        api_list.append(str(i))
    if api_list == []:
       abort(404)
    else:
        db_tweet.insert(new_tweet)
        return "Success"
        
# List specific tweet
def list_tweet(user_id):
    print (user_id)
    db = connection.cloud_native.tweets
    api_list=[]
    tweet = db.find({'id':user_id})
    for i in tweet:
        api_list.append(str(i))
    if api_list == []:
        abort(404)
    return jsonify({'tweet': api_list})
    
# List tweets
def list_tweets():

    api_list=[]
    db = connection.cloud_native.tweets
    for row in db.find():
        api_list.append(str(row))
    # print (api_list)
    return jsonify({'tweets_list': api_list})

# Deleting User
def del_user(del_user):
    db = connection.cloud_native.users
    api_list=[]
    for i in db.find({'username':del_user}):
        api_list.append(str(i))

    if api_list == []:
        abort(404)
    else:
       db.remove({"username":del_user})
       return "Success"

#update_user
def upd_user(user):
    api_list=[]
    print (user)
    db_user = connection.cloud_native.users
    users = db_user.find_one({"id":user['id']})
    for i in users:
        api_list.append(str(i))
    if api_list == []:
       abort(409)
    else:
        db_user.update({'id':user['id']},{'$set': user}, upsert=False )
        return "Success"
        
# Adding user
def add_user(new_user):
    api_list=[]
    print (new_user)
    db = connection.cloud_native.users
    user = db.find({'$or':[{"username":new_user['username']} ,{"email":new_user['email']}]})
    for i in user:
        print (str(i))
        api_list.append(str(i))

    # print (api_list)
    if api_list == []:
    #    print(new_user)
       db.insert(new_user)
       return "Success"
    else :
       abort(409)
       
# List specific users
def list_user(user_id):
    print (user_id)
    api_list=[]
    db = connection.cloud_native.users
    for i in db.find({'id':user_id}):
        api_list.append(str(i))

    if api_list == []:
        abort(404)
    return jsonify({'user_details':api_list})

# List users
def list_users():
    api_list=[]
    db = connection.cloud_native.users
    for row in db.find():
        api_list.append(str(row))
    # print (api_list)
    return jsonify({'user_list': api_list})

@app.route("/api/v1/info")
def home_index():
    api_list=[]
    db = connection.cloud_native.apirelease
    for row in db.find():
        api_list.append(str(row))
    return jsonify({'api_version': api_list}), 200

def create_mongodatabase():
    try:
        dbnames = connection.database_names()
        if 'cloud_native' not in dbnames:
            db = connection.cloud_native.users
            db_tweets = connection.cloud_native.tweets
            db_api = connection.cloud_native.apirelease

            db.insert({
            "email": "eric.strom@google.com",
            "id": 33,
            "full_name": "Eric stromberg",
            "password": "eric@123",
            "username": "eric.strom"
            })

            db_tweets.insert({
            "body": "New blog post,Launch your app with the AWS Startup Kit! #AWS",
            "id": 18,
            "timestamp": "2017-03-11T06:39:40Z",
            "tweetedby": "eric.strom"
            })

            db_api.insert( {
              "buildtime": "2017-01-01 10:00:00",
              "links": "/api/v1/users",
              "methods": "get, post, put, delete",
              "version": "v1"
            })
            db_api.insert( {
              "buildtime": "2017-02-11 10:00:00",
              "links": "api/v2/tweets",
              "methods": "get, post",
              "version": "2017-01-10 10:00:00"
            })
            print ("Database Initialize completed!")
        else:
            print ("Database already Initialized!")
    except:
        print ("Database creation failed!!")


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if request.method=='POST':
        users = connection.cloud_native.users
        api_list=[]
        existing_users = users.find({"username":session['logged_in']})
        for i in existing_users:
            # print (str(i))
            api_list.append(str(i))
        user = {}
        print (api_list)
        if api_list != []:
            print (request.form['email'])
            user['email']=request.form['email']
            user['name']= request.form['name']
            user['password']=request.form['pass']
            users.update({'username':session['logged_in']},{'$set': user} )
        else:
            return 'User not found!'
        return redirect(url_for('index'))
    if request.method=='GET':
        users = connection.cloud_native.users
        user=[]
        #print (session['username'])
        existing_user = users.find({"username":session['logged_in']})
        for i in existing_user:
            user.append(i)
        return render_template('profile.html', name=user[0]['name'], username=user[0]['username'], password=user[0]['password'], email=user[0]['email'])



@app.route("/logout")
def logout():
    session['logged_in'] = False
    return redirect(url_for('home'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method=='POST':
        users = connection.cloud_native.users
        api_list=[]
        existing_user = users.find({'$or':[{"username":request.form['username']} ,{"email":request.form['email']}]})
        for i in existing_user:
            # print (str(i))
            api_list.append(str(i))

        # print (api_list)
        if api_list == []:
            users.insert({
            "email": request.form['email'],
            "id": random.randint(1,1000),
            "name": request.form['name'],
            #"password": bcrypt.hashpw(request.form['pass'].encode('utf-8'), bcrypt.gensalt()),
            "password": request.form['pass'],
            "username": request.form['username']
            })
            session['username'] = request.form['username']
            return redirect(url_for('home'))

        return 'That user already exists'
    else :
        return render_template('signup.html')

@app.route('/login', methods=['POST'])
def do_admin_login():
	users = connection.cloud_native.users
	api_list=[]
	login_user = users.find({'username': request.form['username']})
	for i in login_user:
		api_list.append(i)
	print (api_list)
	if api_list != []:
		#if api_list[0]['password'].decode('utf-8') == bcrypt.hashpw(request.form['password'].encode('utf-8'), api_list[0]['password']).decode('utf-8'):
		# print (api_list[0]['password'].decode('utf-8'), bcrypt.hashpw(request.form['password'].encode('utf-8'), api_list[0]['password']).decode('utf-8'))
		#if api_list[0]['password'] == bcrypt.hashpw(request.form['password'].encode('utf-8'), api_list[0]['password'].encode('utf-8')).decode('utf-8'):
		if api_list[0]['password'] == request.form['password'] :
			session['logged_in'] = api_list[0]['username']
			return redirect(url_for('index'))
		return 'Invalide username/password!'
	else:
		flash("Invalid Authentication")

	return 'Invalid User!'

@app.route('/')
def home():
	if not session.get('logged_in'):
		return render_template('login.html')
	else:
		return render_template('index.html', session = session['username'])

@app.route('/index')
def index():
	return render_template('index.html')

#batas mengerjakan ch1-ch3
@app.route('/clear')
def clearsession():
 # Clear the session
 session.clear()
 # Redirect the user to the main page
 return redirect(url_for('main'))

@app.route('/addname')
def addname():
 if request.args.get('yourname'):
  session['name'] = request.args.get('yourname')
  # And then redirect the user to the main page
  return redirect(url_for('main'))
 else:
  return render_template('addname.html', session=session)

@app.route('/')
def main():
 return render_template('main.html')

@app.route('/addtweets')
def addtweetjs():
 return render_template('addtweets.html')
 
@app.route('/adduser')
def adduser():
    return render_template('adduser.html')

@app.route('/api/v2/tweets/<int:id>', methods=['GET'])
def get_tweet(id):
    return list_tweet(id)

#def list_tweet(user_id):
#    print (user_id)
#    conn = sqlite3.connect('mydb1.db')
#    print ("Opened database successfully");
#    api_list=[]
#    cursor=conn.cursor()
#    cursor.execute("SELECT * from tweets  where id=?",(user_id,))
#    data = cursor.fetchall()
#    print (data)
#    if len(data) == 0:
#        abort(404)
#    else:
#
#        user = {}
#        user['id'] = data[0][0]
#        user['username'] = data[0][1]
#        user['body'] = data[0][2]
#        user['tweet_time'] = data[0][3]
#
#    conn.close()
#    return jsonify(user)

@app.route('/api/v2/tweets', methods=['POST'])
def add_tweets():

    user_tweet = {}
    if not request.json or not 'username' in request.json or not 'body' in request.json:
        abort(400)
    user_tweet['tweetedby'] = request.json['username']
    user_tweet['body'] = request.json['body']
    user_tweet['timestamp']=strftime("%Y-%m-%dT%H:%M:%SZ", gmtime())
    user_tweet['id'] = random.randint(1,1000)

    return  jsonify({'status': add_tweet(user_tweet)}), 201

#@app.route('/api/v2/tweets', methods=['POST'])
#def add_tweets():
#    user_tweet = {}
#    if not request.json or not 'username' in request.json or not 'body' in request.json:
#        abort(400)
#    user_tweet['username'] = request.json['username']
#    user_tweet['body'] = request.json['body']
#    user_tweet['created_at']=strftime("%Y-%m-%dT%H:%M:%SZ", gmtime())
#    print (user_tweet)
#    return  jsonify({'status': add_tweet(user_tweet)}), 200

#def add_tweet(new_tweets):
#    conn = sqlite3.connect('mydb1.db')
#    print ("Opened database successfully");
#    cursor=conn.cursor()
#    cursor.execute("SELECT * from users where username=? ",(new_tweets['username'],))
#    data = cursor.fetchall()
#    if len(data) == 0:
#        abort(404)
#    else:
#       cursor.execute("INSERT into tweets (username, body, tweet_time) values(?,?,?)",(new_tweets['username'],new_tweets['body'], new_tweets['created_at']))
#       conn.commit()
#       return "Success"

@app.route('/api/v2/tweets', methods=['GET'])
def get_tweets():
    return list_tweets()

#def list_tweets():
#    conn = sqlite3.connect('mydb1.db')
#    print ("Opened database successfully");
#    api_list=[]
#    cursor=conn.cursor()
#    cursor.execute("SELECT username, body, tweet_time, id from tweets")
#    data = cursor.fetchall()
#    if data != 0:
#        for row in data:
#            tweets = {}
#            tweets['Tweet By'] = row[0]
#            tweets['Body'] = row[1]
#            tweets['Timestamp'] = row[2]
#            tweets['id'] = row[3]
#            api_list.append(tweets)
#    else :
#        return api_list
#    conn.close()
#    return jsonify({'tweets_list': api_list})

@app.route('/api/v1/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = {}
    # if not request.json:
    #     abort(400)
    user['id']=user_id
    key_list = request.json.keys()
    for i in key_list:
        user[i] = request.json[i]
    print (user)

    return jsonify({'status': upd_user(user)}), 200
    
#def upd_user(user):
#    conn = sqlite3.connect('mydb1.db')
#    print ("Opened database successfully");
#    cursor=conn.cursor()
#    cursor.execute("SELECT * from users where id=? ",(user['id'],))
#    data = cursor.fetchall()
#    print (data)
#    if len(data) == 0:
#        abort(404)
#    else:
#        key_list=user.keys()
#        for i in key_list:
#            if i != "id":
#                print (user, i)
                # cursor.execute("UPDATE users set {0}=? where id=? ", (i, user[i], user['id']))
 #               cursor.execute("""UPDATE users SET {0} = ? WHERE id = ?""".format(i), (user[i], user['id']))
#                conn.commit()
#    return "Success"

@app.route('/api/v1/users', methods=['DELETE'])
def delete_user():
    if not request.json or not 'username' in request.json:
        abort(400)
    user=request.json['username']
    return jsonify({'status': del_user(user)}), 200
    
#def del_user(del_user):
#    conn = sqlite3.connect('mydb1.db')
#    print ("Opened database successfully");
#    cursor=conn.cursor()
#    cursor.execute("SELECT * from users where username=? ",(del_user,))
#    data = cursor.fetchall()
#    print ("Data" ,data)
#    if len(data) == 0:
#        abort(404)
#    else:
#       cursor.execute("delete from users where username==?",(del_user,))
#       conn.commit()
#       return "Success"

@app.errorhandler(409)
def user_found(error):
    return make_response(jsonify({'error': 'Conflict! Record exist'}), 409)
    
@app.errorhandler(400)
def invalid_request(error):
    return make_response(jsonify({'error': 'Bad Request'}), 400)

@app.route('/api/v1/users', methods=['POST'])
def create_user():
    if not request.json or not 'username' in request.json or not 'email' in request.json or not 'password' in request.json:
        abort(400)
    user = {
        'email': request.json['email'],
        'full_name': request.json.get('full_name',""),
        'password': request.json['password'],
        'username': request.json['username'],
        'id': random.randint(1,1000)
    }
    return jsonify({'status': add_user(user)}), 201

#def add_user(new_user):
#    conn = sqlite3.connect('mydb1.db')
#    print ("Opened database successfully");
#    api_list=[]
#    cursor=conn.cursor()
#    cursor.execute("SELECT * from users where username=? or email=?",(new_user['username'],new_user['email']))
#    data = cursor.fetchall()
    #return new_user
#    if len(data) != 0:
#        abort(409)
#    else:
#       cursor.execute("insert into users (username, email, password, full_name) values(?,?,?,?)",(new_user['username'],new_user['email'], new_user['password'], new_user['full_name']))
#       conn.commit()
       
#    conn.close()
#    return "Success"
#    return jsonify(a_dict)

@app.route('/api/v1/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    return list_user(user_id)

#def list_user(user_id):
#    conn = sqlite3.connect('mydb1.db')
#    print ("Opened database successfully");
#    api_list=[]
#    cursor=conn.cursor()
#    cursor.execute("SELECT * from users where id=?",(user_id, ))
#    data = cursor.fetchall()
#    print (data)
#    if len(data) == 0:
#        abort(404)
#    else:
#
#        user = {}
#        user['username'] = data[0][0]
#        user['full_name'] = data[0][1]
#        user['email'] = data[0][2]
#        user['password'] = data[0][3]
#        user['id'] = data[0][4]
#        conn.close()
#        return jsonify(user)

@app.errorhandler(404)
def resource_not_found(error):
    return make_response(jsonify({'error': 'Resource not found!'}), 404)


@app.route('/api/v1/users', methods=['GET'])
def get_users():
    return list_users()

# def list_users():
#     conn = sqlite3.connect('mydb1.db')
#     print ("Opened database successfully");
#     api_list=[]
#     cursor = conn.execute("SELECT username, full_name,  email, password, id from users")
#     for row in cursor:
#         a_dict = {}
#         a_dict['username'] = row[0]
#         a_dict['email'] = row[1]
#         a_dict['password'] = row[2]
#         a_dict['full_name'] = row[3]
#         a_dict['id'] = row[4]
#         api_list.append(a_dict)
#     conn.close()
#     return jsonify({'user_list': api_list})

# @app.route("/api/v1/info")
# def home_index():
#     conn = sqlite3.connect('mydb1.db')
#     print ("Opened database successfully");
#     api_list=[]
#     cursor = conn.execute("SELECT buildtime, version,methods, links from apirelease")
#     for row in cursor:
#         a_dict = {}
#         a_dict['version'] = row[0]
#         a_dict['buildtime'] = row[1]
#         a_dict['methods'] = row[2]
#         a_dict['links'] = row[3]
#         api_list.append(a_dict)
#         conn.close()
#         return jsonify({'api_version': api_list}), 200

# Main Function
if __name__ == '__main__':
    create_mongodatabase()
    app.run(host='0.0.0.0', port=5000, debug=True)



 
