from flask import Flask, render_template, flash, request, redirect, url_for, session
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, RadioField, IntegerField
from wtforms.validators import InputRequired, Email, Length, EqualTo, NumberRange
from dbconnect import connection
from MySQLdb import escape_string as thwart
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ShshhhYouCannotTellAnyone'
Bootstrap(app)

class LoginForm(FlaskForm):
	username = StringField('Username')
	password = PasswordField('Password')

class RegisterForm(FlaskForm):
	name = StringField('Name', validators = [InputRequired()])
	username = StringField('Username', validators=[InputRequired(), Length(min=4, max=15)])
	email = StringField('Email', validators=[InputRequired(), Email(message='Invalid email.'), Length(max=50)])
	security_question = StringField('(Security question) Who is your favorite cartoon character?', validators=[InputRequired(), Length(max=100)])
	age = IntegerField('Age', validators=[InputRequired(), NumberRange(min=7, max=77, message='Field must be between 7 to 77 years old.')])
	password = PasswordField('Password', validators=[InputRequired(), Length(min=8, max=80)])
	confirm_password = PasswordField('Confirm password', validators=[InputRequired(), EqualTo('password')])

class ForgotPasswordForm(FlaskForm):
	username = StringField('Username')
	security_question = StringField('(Security question) Who is your favorite cartoon character?')
	new_password = PasswordField('New password', validators=[InputRequired(), Length(min=8, max=80)])
	confirm_password = PasswordField('Confirm password', validators=[InputRequired(), EqualTo('new_password', message='Field must be equal to new password.')])

class QuizForm(FlaskForm):
	quiz = RadioField(choices=[], validators=[InputRequired()])

class EditProfileForm(FlaskForm) :
	name = StringField('Name', validators = [InputRequired()])
	email = StringField('Email', validators = [InputRequired(), Email(message='Invalid email.'), Length(max=50)])
	security_question = StringField('(Security question) Who is your favorite cartoon character?', validators=[InputRequired(), Length(max=100)])
	age = IntegerField('Age', validators=[InputRequired(), NumberRange(min=7, max=77, message='Age must be between 7 to 77 years.')])
	password = PasswordField('Current password')
	new_password = PasswordField('New password(optional)')

quizn={'quiz1':'Doraemon','quiz2':'Shinchan', 'quiz3':'Chhota Bheem','quiz4':'Ninja Hattori'}

@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
	session.pop('user', None)
	form = LoginForm(request.form)
	if request.method == "POST" and form.validate_on_submit():
		username = form.username.data
		password = form.password.data
		c, conn = connection()
		row = c.execute("SELECT * FROM users WHERE username = \"%s\"" % (thwart(username)))
		if int(row) == 1 :
			row = c.fetchone()
			if str(password) == row[6] :
				c.close()
				conn.close()
				session['user'] = username
				return redirect(url_for('dashboard'))
			else :
				flash("Incorrect Password!")
				return render_template('login.html', form=form)
		else :
			flash("Invalid Username!")
			return render_template('login.html', form=form)
	return render_template('login.html', form=form)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
	form = RegisterForm(request.form)
	if request.method == "POST" and form.validate_on_submit():
		name = form.name.data
		username = form.username.data
		email = form.email.data
		security_question = form.security_question.data
		age = form.age.data
		password = form.password.data
		confirm_password = form.confirm_password.data
		c, conn = connection()
		row = c.execute("SELECT * FROM users WHERE username = \"%s\"" % (thwart(username)))
		if int(row) > 0:
			flash("Username already taken, please choose another!")
			return render_template('signup.html', form=form)
		else :
			session['user']=username
			c.execute("INSERT INTO users (name, username, email, security_question, age, password) VALUES (\"%s\", \"%s\", \"%s\", \"%s\", %d, \"%s\")" % (thwart(name), thwart(username), thwart(email), thwart(security_question), age, thwart(password)))
			c.execute("CREATE TABLE %s (quizname VARCHAR(20), score INTEGER(1), timing DECIMAL(7,3))" % session['user'])
			conn.commit()
			c.close()
			conn.close()
			return redirect(url_for('dashboard'))
	return render_template('signup.html', form=form)

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
	form = ForgotPasswordForm()
	if request.method == "POST" and form.validate_on_submit():
		username = form.username.data
		security_question = form.security_question.data
		new_password = form.new_password.data
		confirm_password = form.confirm_password.data
		c, conn = connection()
		row = c.execute("SELECT * FROM users WHERE username = \"%s\"" % (thwart(username)))
		if int(row) == 1:
			row = c.fetchone()
			if str(security_question) == row[4] :
				c.execute("UPDATE users SET password = \"%s\" WHERE username = \"%s\"" % (thwart(new_password), thwart(username)))
				conn.commit()
				c.close()
				conn.close()
				return redirect(url_for('login'))
			else :
				flash("Invalid answer to security question!")
				return render_template('forgot_password.html', form=form)
		else :
			flash("Invalid username!")
			return render_template('forgot_password.html', form=form)
	return render_template('forgot_password.html', form=form)

@app.route('/dashboard')
def dashboard():
	if 'user' in session :
		return render_template('dashboard.html')
	return "YOU MUST LOGIN!"


@app.route('/profile')
def profile():
	c, conn = connection()
	c.execute("SELECT * from users where username = \"%s\" " % thwart(session.get('user')))
	row = c.fetchone()
	about_me = [row[1], row[2], row[3], row[5], row[4]]
	c.execute("SELECT * from %s" % session.get('user'))
	rows = c.fetchall()
	c.execute("select username, sum(score),sum(timing) from scoreboard group by username order by sum(score) desc, sum(timing) asc")
	rank=c.fetchone()
	i = 0
	while rank is not None:
		i +=1
		if (rank[0]==session['user']):
			about_me.append(i)
		rank=c.fetchone()

	c.execute("select count(*) from %s" %session['user'])
	about_me.append(c.fetchone()[0])
	conn.commit()
	c.close()
	conn.close()
	if 'user' in session :
		return render_template('profile.html', about_me=about_me, rows = rows)
	return "YOU MUST LOGIN!"

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
	c, conn = connection()
	c.execute("SELECT * from users where username = \"%s\" " % thwart(session.get('user')))
	row = c.fetchone()
	form = EditProfileForm(name = row[1], email = row[3], security_question = row[4], age = row[5])
	if request.method == "POST" and form.validate_on_submit():
		name = form.name.data
		email = form.email.data
		security_question = form.security_question.data
		age = form.age.data
		password = form.password.data
		new_password = form.new_password.data
		if (str(password) == row[6] or str(password)=='') :
			c.execute("UPDATE users SET name = \"%s\", ehttps://perfect-chipmunk-30.localtunnel.memail = \"%s\", security_question = \"%s\", age = %s WHERE username = \"%s\"" % (thwart(name), thwart(email), thwart(security_question), age, thwart(session.get('user'))))
			if new_password != '' :
				if len(new_password)>=8 and len(new_password)<=80 :
					c.execute("UPDATE users SET password= \"%s\" WHERE username = \"%s\"" % (thwart(new_password), thwart(session.get('user'))))
				else:
					flash('New password must be between 8 and 80 characters long!')
					return render_template('edit_profile.html', form=form)
			conn.commit()
			c.close()
			conn.close()
			return redirect(url_for('profile'))
		else :
			flash('Incorrect password!')
			return render_template('edit_profile.html', form=form)
	if 'user' in session :
		return render_template('edit_profile.html', form=form)
	return "YOU MUST LOGIN!"

@app.route('/leaderboard')
def leaderboard():
	quizname = ['Doraemon', 'Shinchan', 'Chhota Bheem', 'Ninja Hattori' ]
	c, conn = connection()
	m = {}
	for name in quizname :
		quiz = c.execute("SELECT username,score,timing from scoreboard where quizname = \'%s\' ORDER BY score DESC, timing ASC" %thwart(name))
		data = c.fetchall()
		m[name]=data
	c.close()
	conn.close()
	if 'user' in session :
		return render_template('leaderboard.html', m = m, column=['Rank','Username','Score','Time'])
	return "YOU MUST LOGIN!"

@app.route('/leaderboard2')
def leaderboard2():
	c, conn = connection()
	c.execute("select username, sum(score),sum(timing) from scoreboard group by username order by sum(score) desc, sum(timing) asc")
	data = c.fetchall()
	c.close()
	conn.close()
	if 'user' in session :
		return render_template('leaderboard2.html', data=data, len=len(data),column=['Rank','Username','Total Score','Total Time'])
	return "YOU MUST LOGIN!"


@app.route('/quiz1about')
def quiz1about():
	if 'user' in session :
		session['quiz']="quiz1"
		return render_template('quiz1about.html')
	return "YOU MUST LOGIN!"

@app.route('/quiz2about')
def quiz2about():
	if 'user' in session :
		session['quiz']="quiz2"
		return render_template('quiz2about.html')
	return "YOU MUST LOGIN!"

@app.route('/quiz3about')
def quiz3about():
	if 'user' in session :
		session['quiz']="quiz3"
		return render_template('quiz3about.html')
	return "YOU MUST LOGIN!"

@app.route('/quiz4about')
def quiz4about():
	if 'user' in session :
		session['quiz']="quiz4"
		return render_template('quiz4about.html')
	return "YOU MUST LOGIN!"

i = 0
correct = 0
score = 0
x = []
start = 0
stop = 0
quizname = ""

@app.route('/quiz1', methods=['GET', 'POST'])
def quiz1():
	global i, correct, score, x, start, stop, quizname
	x.append(time.time())
	c, conn = connection()
	form = QuizForm(request.form)
	row = c.execute("SELECT * FROM %s" %session['quiz'])
	row = c.fetchall()
	form.quiz.label = row[i][1]
	form.quiz.choices = [(row[i][j], row[i][j]) for j in range(2, 6)]
	answer = form.quiz.data
	if answer == row[i][6] :
		correct += 1
	if request.method == "POST" and form.validate_on_submit():
		if i < 4 :
			i += 1
			return redirect(url_for('quiz1'))
		else :
			c.close()
			conn.close()
			score = correct
			start = x[0]
			stop = time.time()
			quizname = quizn[session['quiz']]
			i = 0
			correct = 0
			x = []
			return redirect(url_for('scorecard'))
	if 'user' in session :
		return render_template('quiz1.html', form=form,quizname=quizn[session['quiz']])
	return "YOU MUST LOGIN!"

@app.route('/scorecard')
def scorecard():
	flash("You scored %s out of 5!" % score)
	flash("You took %s seconds to complete this quiz!" % str(stop - start))
	c, conn = connection()
	row = c.execute("SELECT * FROM scoreboard WHERE username = \"%s\" AND quizname = \"%s\"" % (thwart(session.get('user')), thwart(quizname)))
	if int(row) > 0:
		c.execute("UPDATE scoreboard SET score = %d, timing = %.3f WHERE username = \"%s\" AND quizname = \"%s\"" % (score, (stop - start), thwart(session.get('user')), thwart(quizname)))
	else :
		c.execute("INSERT INTO scoreboard (username, quizname, score, timing) VALUES (\"%s\", \"%s\", %d, %.3f)" % (thwart(session.get('user')), thwart(quizname), score, (stop - start)))
	c.execute("INSERT INTO %s VALUES (\"%s\", %d, %.3f)" % (thwart(session.get('user')), thwart(quizname) , score, (stop-start)))
	conn.commit()
	c.close()
	conn.close()
	if 'user' in session :
		return render_template('scorecard.html')
	return

if __name__=='__main__':
	app.run(debug=True)
