#!/usr/bin/python3

import jwt
from flask import *

app = Flask(__name__)
secret = '<secret_key>'

def verify_jwt(token,key):
	try:
		username=jwt.decode(token,key,algorithms=['HS256',])['username']
		if username:
			return True
		else:
			return False
	except:
		return False

@app.route("/", methods=["GET","POST"])
def index():
	if request.method=="POST":
		if request.form['username']=="admin" and request.form['password']=="admin":
			res = make_response()
			username=request.form['username']
			token=jwt.encode({"username":"admin"},secret,algorithm="HS256")
			res.set_cookie("auth",token)
			res.headers['location']='/home'
			return res,302
		else:
			return render_template('index.html')
	else:
		return render_template('index.html')

@app.route("/home")
def home():
	if verify_jwt(request.cookies.get('auth'),secret):
		return render_template('home.html')
	else:
		return redirect('/',code=302)

@app.route("/track",methods=["GET","POST"])
def track():
	if request.method=="POST":
		if verify_jwt(request.cookies.get('auth'),secret):
			return render_template('track.html',message=True)
		else:
			return redirect('/',code=302)
	else:
		return render_template('track.html')

@app.route('/order',methods=["GET","POST"])
def order():
	if verify_jwt(request.cookies.get('auth'),secret):
		if request.method=="POST":
			costume=request.form["costume"]
			message = '''
			Your order of "{}" has been placed successfully.
			'''.format(costume)
			tmpl=render_template_string(message,costume=costume)
			return render_template('order.html',message=tmpl)
		else:
			return render_template('order.html')
	else:
		return redirect('/',code=302)
app.run(debug='true')
