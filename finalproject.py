import httplib2
import json
import requests
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from flask import make_response
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item, User
from flask import Flask, render_template, request, redirect, url_for
from flask import jsonify, flash, session as login_session


CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Item catalog"

app = Flask(__name__)

engine = create_engine('sqlite:///categorywithusers.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # Return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:

        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        login_session['access_token'] = access_token
        response = make_response(json.dumps('Current user already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;'
    output += '-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    print access_token
    return output


# User Helper Functions
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session['credentials'].access_token
    # access_token  =login_session.get('access_token')
    print access_token
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    if access_token is None:
        print 'Access Token is None'
    	response = make_response(json.dumps('Current user not connected'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['credentials'].access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['credentials'].access_token
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        # return response
        return redirect('/catalog')
    else:
        response = make_response(json.dumps('Failed revoke token', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# JSON API
@app.route('/catalog/JSON/')
def catalogsJSON():
    catalogs = session.query(Category).all()
    return jsonify(catalogs=[i.serialize for i in catalogs])


@app.route('/catalog/<int:category_id>/JSON')
def categoryJSON(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    return jsonify(Category=category.serialize)


@app.route('/catalog/<int:category_id>/item/JSON')
def itemsJSON(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    menus = session.query(Item).filter_by(category_id=category_id).all()
    return jsonify(Items=[i.serialize for i in menus])


@app.route('/catalog/<int:category_id>/item/<int:item_id>/JSON')
def itemJSON(category_id, item_id):
    item = session.query(Item).filter_by(id=item_id).one()
    return jsonify(Item=item.serialize)


@app.route('/')
@app.route('/catalog/')
def catalogs():
    # return 'This Returns all categories'
    categories = session.query(Category).all()
    if 'username' not in login_session:
        return render_template('public_catalog.html', categories=categories)
    else:
        return render_template('catalogs.html', categories=categories,
                               user_id=login_session['user_id'])


@app.route('/catalog/new', methods=['GET', 'POST'])
def new_category():

    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        if request.form['name']:
            newCategory = Category(name=request.form['name'],
                                   user_id=login_session['user_id']
                                   )
            session.add(newCategory)
            session.commit()
            flash("new category created!")
            return redirect(url_for('catalogs'))
        else:
            return 'No data entered !'
    else:
        return render_template('new_category.html')


@app.route('/catalogs/<int:category_id>/edit/', methods=['GET', 'POST'])
def edit_category(category_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedCategory = session.query(Category).filter_by(id=category_id).one()
    # New check
    if editedCategory.user_id != login_session['user_id']:
        return redirect(url_for('catalogs'))
    if request.method == 'POST':
        if request.form['name']:
            editedCategory.name = request.form['name']
            session.add(editedCategory)
            session.commit()
            flash("catalog item edited!")
            return redirect(url_for('catalogs'))
        else:
            flash("No data edited !")
            return redirect(url_for('catalogs'))

    else:
        return render_template('edit_category.html',
                               category_id=category_id,
                               category=editedCategory)


@app.route('/catalogs/<int:category_id>/delete/', methods=['GET', 'POST'])
def delete_category(category_id):
    if 'username' not in login_session:
        return redirect('/login')
    categoryToDelete = session.query(Category).filter_by(id=category_id).one()
    # New check
    if categoryToDelete.user_id != login_session['user_id']:
        return redirect(url_for('catalogs'))
    if request.method == 'POST':
        session.delete(categoryToDelete)
        session.commit()
        flash("catalog item deleted!")
        return redirect(url_for('catalogs'))
    else:
        return render_template('delete_category.html',
                               category=categoryToDelete)


@app.route('/catalog/<int:category_id>/item/')
def item(category_id):
    category = session.query(Category).filter_by(id=category_id).one()

    creator = getUserInfo(category.user_id)
    items = session.query(Item).filter_by(category_id=category_id).all()
    if 'username' not in login_session or creator.id != login_session['user_id']:
        return render_template('public_items.html', items=items,
                               category=category, creator=creator)
    else:
        return render_template('menu.html', category=category,
                               items=items, category_id=category_id,
                               creator=creator)


@app.route('/catalog/<int:category_id>/item/new/', methods=['GET', 'POST'])
def new_item(category_id):
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        if request.form['name']:
            newItem = Item(name=request.form['name'],
                           description=request.form['description'],
                           category_id=category_id,
                           user_id=login_session['user_id'])
            session.add(newItem)
            session.commit()
            flash("new category item created!")
            return redirect(url_for('item', category_id=category_id))
        else:
            return 'Some primary data is missing'
    else:
        return render_template('new_item.html', category_id=category_id)


@app.route('/catalog/<int:category_id>/item/<int:item_id>/edit/',
           methods=['GET', 'POST'])
def editItem(category_id, item_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedItem = session.query(Item).filter_by(id=item_id).one()
    # New check
    if editedItem.user_id != login_session['user_id']:
        return redirect(url_for('item', category_id=category_id))
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        session.add(editedItem)
        session.commit()
        flash("category item edited!")
        return redirect(url_for('item', category_id=category_id))
    else:

        return render_template(
            'editmenuitem.html', category_id=category_id,
            item_id=item_id, item=editedItem)


@app.route('/catalog/<int:category_id>/menu/<int:item_id>/delete/',
           methods=['GET', 'POST'])
def deleteItem(category_id, item_id):
    if 'username' not in login_session:
        return redirect('/login')
    itemToDelete = session.query(Item).filter_by(id=item_id).one()
    # New check
    if itemToDelete.user_id != login_session['user_id']:
        return redirect(url_for('item', category_id=category_id))
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash("menu item deleted!")
        return redirect(url_for('item', category_id=category_id))
    else:
        return render_template('delete_menu.html',
                               item=itemToDelete,
                               category_id=category_id)

if __name__ == '__main__':
    app.debug = True
    app.secret_key = 'super_secret_key'
    app.run(host='0.0.0.0', port=5000)
