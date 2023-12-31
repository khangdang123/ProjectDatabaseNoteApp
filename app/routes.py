import os

from werkzeug.utils import secure_filename

from app import app
from flask import render_template, flash, redirect, request, url_for, send_file
from app.forms import LoginForm, RegistrationForm, CreateNote, EditNoteForm, CommentForm, ResetPasswordForm, ReTitleForm
from flask_login import current_user, login_user, logout_user
from app.models import User, Note, Comment
from app import db
import json, requests

# Create an array for variable 'notes'
notes = []

# Define Mediastack API endpoint key
MEDIASTACK_API_KEY = 'YOUR_MEDIASTACK_API_KEY'
# Define Mediastack API endpoint URL
MEDIASTACK_API_URL = 'http://api.mediastack.com/v1/news'


@app.route('/')
def home():
    # Renders the 'home.html' template when users in the Root URL.
    return render_template('home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    # Check if the current user is authenticated(Check username and password) and redirect the user to the index page
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    # Create an instance of the LoginForm
    form = LoginForm()

    # If the form has been submitted with all fields are filled, attempt to log in
    if form.validate_on_submit():
        # Query the User Table for a user with the specified name.
        user = User.query.filter_by(username=form.username.data).first()
        # If the user doesn't exist or the user enterting invalid password of the account
        if user is None or not user.check_password(form.password.data):
            # Print message
            flash('Invalid username or password')
            # Redirect to login page
            return redirect(url_for('login'))
        # If the user exist and entered valid password, redirect to index page
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('index'))
    # Renders the 'login.html' template when users in the login page
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    # Log out the user and redirect user to login page
    logout_user()
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    # Check if the current user is authenticated(Check username and password) and redirect the user to the index page
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    # Create an instance of the RegistrationForm
    form = RegistrationForm()
    # If the form has been submitted and is valid
    if form.validate_on_submit():
        # Create a new User object with the data in the form and add it to the database
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        # Print message if success
        flash('Congratulations, you are now a registered user!')
        # Redirect to the login page after created the account
        return redirect(url_for('login'))
    # Renders the 'register.html' template when users in the register page
    return render_template('register.html', title='Register', form=form)


@app.route('/index')
def index():
    # Create the database tables if they do not exist
    db.create_all()
    # Query all notes from the Note model
    notes = Note.query.all()
    # Call the function load_notes
    load_notes()
    # Renders the 'index.html' template when users in the index page
    return render_template('index.html', notes=notes)


@app.route('/create_note', methods=['GET', 'POST'])
def create_note():
    # Create an instance of the CreateNote form
    form = CreateNote()

    # If the form has been submitted and is valid
    if form.validate_on_submit():
        # Extract the data from the form
        title = form.title.data
        note_content = form.note.data

        attachment = form.attachment.data
        # Create a new instance of the Note model with the form data
        if attachment:
            attachment_filename = secure_filename(attachment.filename)
            print(secure_filename(attachment.filename))
            picture_path = os.path.join(app.root_path, 'static', attachment_filename)
            attachment.save(picture_path)
            attachment_data = attachment.read()
        else:
            attachment_filename = None
            attachment_data = None

        new_note = Note(title=title, content=note_content, attachment_path=attachment_filename, image=attachment_data)

        # Add and commit new note to the database
        db.session.add(new_note)
        db.session.commit()

        # Print message
        flash('Note created successfully!', 'success')
        # Redirect to the index page after creating the note
        return redirect(url_for('index'))

    # Renders the 'create.html' template if form has not been submitted
    return render_template('create.html', title='Create Note', form=form)


@app.route('/delete_note/<int:id>', methods=['GET', 'POST'])
def delete_note(id):
    # Check if the request method is POST
    if request.method == 'POST':
        # Retrieve the note with the specified ID or return a 404 error if not found
        note_to_delete = Note.query.get_or_404(id)

        # Delete the note from the database
        db.session.delete(note_to_delete)
        # Commit the change of notes to the database
        db.session.commit()
    # Redirect to the index page after deleted the note
    return redirect(url_for('index'))


def load_notes():
    # Use the 'global' keyword to access the 'notes' variable outside the function
    global notes
    try:
        # Try to open and read the 'notes.json' file
        with open('notes.json', 'r') as file:
            # Attempt to load JSON data from the file
            notes = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        notes = []
    #  Return the loaded notes
    return notes


@app.route('/edit_note/<int:note_id>', methods=['GET', 'POST'])
def edit_note(note_id):
    # Query the note with the specified ID from the database
    note = Note.query.get(note_id)

    # If note doesn't exist, print message
    if not note:
        return "Note not found", 404

    # Create an instance of the EditNoteForm
    form = EditNoteForm(obj=note)

    # Check if the request method is POST and the form is valid
    if request.method == 'POST' and form.validate_on_submit():
        # Update the note object with the form data
        form.populate_obj(note)

        # Commit the changes to the database
        db.session.commit()

        # Print message if note updated succesfully
        flash('Note updated successfully!', 'success')
        # Redirect to the index page after updating the note
        return redirect(url_for('index'))

    # Render the 'edit_note.html' template with the form and note data
    return render_template('edit_note.html', form=form, note=note)


@app.route('/ReTitle_note/<int:note_id>', methods=['GET', 'POST'])
def ReTitle_note(note_id):
    # Query the note with the specified ID from the database
    note = Note.query.get(note_id)

    # If note doesn't exist, print message
    if not note:
        return "Note not found", 404

    # Create an instance of the EditNoteForm
    form = ReTitleForm(obj=note)

    # Check if the request method is POST and the form is valid
    if request.method == 'POST' and form.validate_on_submit():
        # Update the note object with the form data
        form.populate_obj(note)

        # Commit the changes to the database
        db.session.commit()

        # Print message if note updated succesfully
        flash('Note updated successfully!', 'success')
        # Redirect to the index page after updating the note
        return redirect(url_for('index'))

    # Render the 'edit_note.html' template with the form and note data
    return render_template('ReTitle.html', form=form, note=note)


@app.route('/index/', methods=['GET', 'POST'])
def sort():
    # Create the database tables if they do not exist
    db.create_all()
    # Query all notes from the Note model
    notes = Note.query.all()

    # If the request method is POST
    if request.method == 'POST':
        # if the 'sort_button' is present in the form data
        if 'sort_button' in request.form:
            # Retrieve the selected sort option from the form data
            sort_option = request.form['sort_option']

            # Perform sorting based on the selected option
            if sort_option == 'title':
                notes = sorted(notes, key=lambda x: x.title)
            elif sort_option == 'content':
                notes = sorted(notes, key=lambda x: x.content)
            elif sort_option == 'id':
                notes = sorted(notes, key=lambda x: x.id)

    # Render the 'index.html' template with the sorted notes
    return render_template('index.html', notes=notes)


@app.route('/note/<int:note_id>', methods=['GET', 'POST'])
def show_detail(note_id):
    # Query the note with the specified ID from the database
    note = Note.query.get(note_id)

    # if the note exists
    if not note:
        return "Note not found", 404

    # Create an instance of the CommentForm
    comment_form = CommentForm()

    # If the request method is POST and the comment form is valid
    if request.method == 'POST' and comment_form.validate_on_submit():
        # Create a new comment associated with the current note
        new_comment = Comment(text=comment_form.text.data, note=note)
        # Add the new comment to the database
        db.session.add(new_comment)
        # Commit the new comment to the database
        db.session.commit()
        # Print message if comment added successfully
        flash('Comment added successfully!', 'success')

    # Render the 'note.html' template with the note and comment form data
    return render_template('note.html', note=note, comment_form=comment_form)


@app.route('/news', methods=['GET', 'POST'])
def news():
    # Function to search by keywork in the MediaStack API 
    if request.method == 'POST':
        search_term = request.form.get('search_term', '')
    else:
        search_term = request.args.get('search_term', '')

    # Define parameters for the API request (Access key, countries, sort, and keywords)
    params = {
        'access_key': 'cf3b6b3d28b18a7f0b380d7a89b5ea30',
        'countries': 'us',
        'sort': 'published_desc',
        'keywords': search_term,
    }

    # Make a GET request to the MediaStack API with the specified parameters
    response = requests.get(MEDIASTACK_API_URL, params=params)

    # Check if the API request was successful (status code 200)
    if response.status_code == 200:
        # Parse the JSON data from the API response
        data = response.json()

        # Call the parse_articles function to extract relevant information
        articles = parse_articles(data)

        # Render the 'news.html' template with the extracted articles and search term
        return render_template('news.html', articles=articles, search_term=search_term, notes=notes)


# Function to parse the articles from the API response data
def parse_articles(data):
    # Define an array for variable 'articles'
    articles = []
    # Counter to keep track of the number of parsed articles
    counter = 0

    # Loop through the data and extract relevant information for up to 4 articles
    while len(articles) < 4 and counter < len(data.get("data", [])):
        if "image" in data["data"][counter] and data["data"][counter]["image"]:
            # Extract author, title, image URL, and article URL
            author = data["data"][counter]["author"]
            title = data["data"][counter]["title"]
            img = data["data"][counter]["image"]
            url = data["data"][counter]["url"]

            # Create a dictionary with the extracted information and append it to the list
            article = {"author": author, "title": title, "img": img, "url": url}
            articles.append(article)
        # Increment the counter
        counter += 1
    # Return the list of parsed articles
    return articles


@app.route('/reset_password', methods=['GET', 'POST'])
# Ensures that the user is logged in
def reset_password():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    form = ResetPasswordForm()

    if form.validate_on_submit():
        # Verify the user's current password before allowing a reset
        if current_user.check_password(form.current_password.data):
            # Set the user's new password and commit the change to the database
            current_user.set_password(form.new_password.data)
            db.session.commit()

            flash('Congratulations! Your password has been reset.')
            return redirect(url_for('index'))
        else:
            flash('Incorrect current password. Please try again.', 'error')

    return render_template('reset_password.html', form=form)


@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query')

    if query:
        # Use the Note model to query the database for notes containing the search query
        notes = Note.query.filter(
            (Note.title.ilike(f"%{query}%")) | (Note.content.ilike(f"%{query}%"))
        ).all()
    else:
        # If no query is provided, return all notes
        notes = Note.query.all()

    previous_page = request.referrer

    return render_template('search_results.html', query=query, notes=notes, previous_page=previous_page)

