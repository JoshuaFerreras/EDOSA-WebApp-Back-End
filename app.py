#IMPORTS FROM
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, jwt_required
from dotenv import load_dotenv
from passlib.hash import bcrypt
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from passlib.hash import bcrypt
from sqlalchemy import func
from prediction import prediction
from flask_migrate import Migrate
from sqlalchemy import desc
from flask import Flask, request, jsonify
from sqlalchemy import join


#IMPORTS
import sqlite3
import concurrent.futures
import os
import uuid
import datetime





load_dotenv()

app = Flask(__name__)
executor = concurrent.futures.ThreadPoolExecutor()
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(
    minutes=180)  # Change the expiration time as needed
jwt = JWTManager(app)
CORS(app)

# Configure the SQLAlchemy database URL
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/edosa_db2'
db = SQLAlchemy(app)
migrate = Migrate(app, db)


# Define your database models
class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role_id = db.Column(db.Integer, default=2)  # Default role_id
    UserID = db.Column(db.String(6), unique=True, nullable=False)
    appointments = db.relationship('Appointments', back_populates='user', lazy=True)
    profile = db.relationship('Profile', back_populates='user', uselist=False)
    survey = db.relationship('Surveys', back_populates='user', uselist=False)

class Appointments(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    status = db.Column(db.String(50))
    date = db.Column(db.Date)
    time = db.Column(db.Time)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('Users', back_populates='appointments')
    doctor_id = db.Column(db.Integer)

class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lname = db.Column(db.String(255), nullable=False)
    fname = db.Column(db.String(255), nullable=False)
    mname = db.Column(db.String(255), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    height = db.Column(db.Float, nullable=False)
    weight = db.Column(db.Float, nullable=False)
    birthdate = db.Column(db.Date, nullable=False)
    address = db.Column(db.String(255), nullable=False)
    civilStatus = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    mobileNumber = db.Column(db.String(11), unique=True, nullable=False)
    emergencyContact = db.Column(db.String(11))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('Users', back_populates='profile', uselist=False)

class Surveys(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    snoring = db.Column(db.Boolean, nullable=False)
    tired = db.Column(db.Boolean, nullable=False)
    observed = db.Column(db.Boolean, nullable=False)
    pressure = db.Column(db.Boolean, nullable=False)
    bmi = db.Column(db.Boolean, nullable=False)
    testage = db.Column(db.Boolean, nullable=False)
    neck = db.Column(db.Boolean, nullable=False)
    testgender = db.Column(db.Boolean, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('Users', back_populates='survey', uselist=False)


######################### APP ROUTES ###################################
# GET routes for user that have role 1
@app.route('/get_users_with_role_1', methods=['GET'])
def get_users_with_role_1():
    users = Users.query.filter_by(role_id=1).all()
    if not users:
        return jsonify({'message': 'No users with role_id 1 found'})

    user_data = []
    for user in users:
        user_data.append({
            'id' : user.profile.user_id,
            'gender': user.profile.gender,
            'firstname': user.profile.fname,
            'lastname': user.profile.lname,
            'age': user.profile.age,
            'email': user.profile.email,
            'contact_no': user.profile.emergencyContact
        })

    return jsonify({'users': user_data})

@app.route('/get_users_subset', methods=['POST'])
def get_users_subset():
    data = request.json
    start_index = data.get('start', 0)  # default start index is 0
    end_index = data.get('end', 2)  # default end index is 2 (inclusive)

    users = Users.query.filter_by(role_id=1).slice(start_index, end_index + 1).all()
    if not users:
        return jsonify({'message': 'No users with role_id 1 found'})

    user_data = []
    for user in users:
        user_data.append({
            'id' : user.profile.user_id,
            'gender': user.profile.gender,
            'firstname': user.profile.fname,
            'lastname': user.profile.lname,
            'age': user.profile.age,
            'email': user.profile.email,
            'contact_no': user.profile.emergencyContact
        })

    return jsonify({'users': user_data})
########################################################################
@app.route('/appointments/<int:appointment_id>', methods=['GET'])
@jwt_required()
def show_appointment_by_id(appointment_id):
    try:
        # Query appointment based on the provided appointment_id
        appointment = Appointments.query.get(appointment_id)

        if appointment:
            # Fetch profile associated with the user_id of the appointment
            profile = Profile.query.filter_by(user_id=appointment.user_id).first()

            if profile:
                response_object = {
                    'status': 'success',
                    'appointment': {
                        'id': appointment.id,
                        'user_id': appointment.user_id,
                        'profile': {
                            'id': profile.id,
                            'lname': profile.lname,
                            'fname': profile.fname,
                            'mname': profile.mname,
                            'age': profile.age,
                            'gender': profile.gender,
                            'height': profile.height,
                            'weight': profile.weight,
                            'birthdate': profile.birthdate.strftime('%Y-%m-%d'),
                            'address': profile.address,
                            'civilStatus': profile.civilStatus,
                            'email': profile.email,
                            'mobileNumber': profile.mobileNumber,
                            'emergencyContact': profile.emergencyContact
                        }
                    }
                }
            else:
                response_object = {
                    'status': 'error',
                    'message': 'Profile not found'
                }
        else:
            response_object = {
                'status': 'error',
                'message': 'Appointment not found'
            }

    except Exception as e:
        print(e)
        response_object = {
            'status': 'error',
            'message': 'Failed to fetch appointment or profile'
        }

    return jsonify(response_object)
########################################################################
@app.route('/survey/<int:appointment_id>', methods=['GET'])
@jwt_required()  # Assuming you're using JWT for authentication
def get_survey_results(appointment_id):
    try:
        # Query appointment based on the provided appointment_id
        appointment = Appointments.query.get(appointment_id)

        if appointment:
            # Fetch survey associated with the appointment
            survey = Surveys.query.filter_by(user_id=appointment.user_id).first()

            if survey:
                response_object = {
                    'status': 'success',
                    'survey': {
                        'snoring': survey.snoring,
                        'tired': survey.tired,
                        'observed': survey.observed,
                        'pressure': survey.pressure,
                        'bmi': survey.bmi,
                        'testage': survey.testage,
                        'neck': survey.neck,
                        'testgender': survey.testgender,
                        'user_id': survey.user_id
                    }
                }
            else:
                response_object = {
                    'status': 'error',
                    'message': 'Survey not found for this appointment'
                }
        else:
            response_object = {
                'status': 'error',
                'message': 'Appointment not found'
            }

    except Exception as e:
        print(e)
        response_object = {
            'status': 'error',
            'message': 'Failed to fetch appointment or survey'
        }

    return jsonify(response_object)
########################################################################
# GET routes for total appointments
@app.route('/patient-dashboard/appointments/count', methods=['GET'])
@jwt_required()
def count_appointments():
    try:
        user_id = get_jwt_identity()
        user_role = Users.query.filter_by(id=user_id).first()

        if user_role.role_id == 2:
            total_appointments = Appointments.query.filter_by(user_id=user_id).count()
        else:
            total_appointments = Appointments.query.filter_by(doctor_id=user_id).count()

        response_object = {
            'status': 'success',
            'total_appointments': total_appointments
        }

    except Exception as e:
        print(e)
        response_object = {
            'status': 'error',
            'message': 'Failed to fetch total appointments'
        }

    return jsonify(response_object)
##########################################################################
# GET routes for accepted appointments
@app.route('/patient-dashboard/appointments/accepted/count', methods=['GET'])
@jwt_required()
def count_accepted_appointments():
    try:
        user_id = get_jwt_identity()
        user_role = Users.query.filter_by(id=user_id).first()

        if user_role.role_id == 2:
            total_accepted_appointments = Appointments.query.filter_by(user_id=user_id, status='accepted').count()
        else:
            total_accepted_appointments = Appointments.query.filter_by(doctor_id=user_id, status='accepted').count()

        response_object = {
            'status': 'success',
            'total_accepted_appointments': total_accepted_appointments
        }

    except Exception as e:
        print(e)
        response_object = {
            'status': 'error',
            'message': 'Failed to fetch total accepted appointments'
        }

    return jsonify(response_object)

# GET routes for pending appointments
@app.route('/patient-dashboard/appointments/pending/count', methods=['GET'])
@jwt_required()
def count_pending_appointments():
    try:
        user_id = get_jwt_identity()
        user_role = Users.query.filter_by(id=user_id).first()

        if user_role.role_id == 2:
            total_pending_appointments = Appointments.query.filter_by(user_id=user_id, status='pending').count()
        else:
            total_pending_appointments = Appointments.query.filter_by(doctor_id=user_id, status='pending').count()

        response_object = {
            'status': 'success',
            'total_pending_appointments': total_pending_appointments
        }

    except Exception as e:
        print(e)
        response_object = {
            'status': 'error',
            'message': 'Failed to fetch total accepted appointments'
        }

    return jsonify(response_object)
    
# GET routes for rejected appointments
@app.route('/patient-dashboard/appointments/rejected/count', methods=['GET'])
@jwt_required()
def count_rejected_appointments():
    try:
        user_id = get_jwt_identity()
        user_role = Users.query.filter_by(id=user_id).first()

        if user_role.role_id == 2:
            total_rejected_appointments = Appointments.query.filter_by(user_id=user_id, status='rejected').count()
        else:
            total_rejected_appointments = Appointments.query.filter_by(doctor_id=user_id, status='rejected').count()

        response_object = {
            'status': 'success',
            'total_rejected_appointments': total_rejected_appointments
        }

    except Exception as e:
        print(e)
        response_object = {
            'status': 'error',
            'message': 'Failed to fetch total rejected appointments'
        }

    return jsonify(response_object)



########################################################################
# GET method to retrieve role_id of the logged-in user
@app.route('/role', methods=['GET'])
@jwt_required()  # This ensures that a valid JWT token is present
def get_role():
    try:
        # Get the user_id from the JWT token
        current_user_id = get_jwt_identity()

        # Query the user by user_id
        user = Users.query.get(current_user_id)

        if user:
            return jsonify({'role_id': user.role_id}), 200
        else:
            return jsonify({'message': 'User not found'}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500
########################################################################
# GET and POST routes for profiles
@app.route('/profile', methods=['GET', 'POST'])
@jwt_required()
def get_or_create_profile():
    if request.method == 'GET':
        try:
            user_id = get_jwt_identity()  # Get the user_id from the JWT token

            # Query the profile for the current user
            profile = Profile.query.filter_by(user_id=user_id).first()
            user = Users.query.filter_by(id=user_id).first()

            if profile:
                response_object = {
                    'status': 'success',
                    'profile': {
                        'id': profile.id,
                        'lname': profile.lname,
                        'fname': profile.fname,
                        'mname': profile.mname,
                        'age': profile.age,
                        'gender': profile.gender,
                        'height': profile.height,
                        'weight': profile.weight,
                        'birthdate': profile.birthdate.strftime('%Y-%m-%d'),
                        'address': profile.address,
                        'civilStatus': profile.civilStatus,
                        'email': profile.email,
                        'mobileNumber': profile.mobileNumber,
                        'emergencyContact': profile.emergencyContact,
                        'user_id': profile.user_id,
                        'user_Id': user.UserID,
                        'role_id': user.role_id  # Include the role_id here
                    }
                }
            else:
                response_object = {
                    'status': 'error',
                    'message': 'Profile not found'
                }
        except Exception as e:
            print(e)
            response_object = {
                'status': 'error',
                'message': 'Failed to fetch profile'
            }

        return jsonify(response_object)

    elif request.method == 'POST':
        try:
            from datetime import datetime  # Import datetime explicitly
            user_id = get_jwt_identity()  # Get the user_id from the JWT token

            # Check if a profile already exists for the user
            existing_profile = Profile.query.filter_by(user_id=user_id).first()

            if existing_profile:
                response_object = {
                    'status': 'error',
                    'message': 'Profile already exists'
                }
            else:
                data = request.get_json()
                lname = data.get('lname')
                fname = data.get('fname')
                mname = data.get('mname')
                age = data.get('age')
                gender = data.get('gender')
                height = data.get('height')
                weight = data.get('weight')
                birthdate_str = data.get('birthdate')
                birthdate = datetime.strptime(birthdate_str, '%Y-%m-%d').date()  # Use datetime.strptime with the correct import
                address = data.get('address')
                civilStatus = data.get('civilStatus')
                email = data.get('email')
                mobileNumber = data.get('mobileNumber')
                emergencyContact = data.get('emergencyContact')

                # Create a new profile record
                profile = Profile(
                    lname=lname,
                    fname=fname,
                    mname=mname,
                    age=age,
                    gender=gender,
                    height=height,
                    weight=weight,
                    birthdate=birthdate,
                    address=address,
                    civilStatus=civilStatus,
                    email=email,
                    mobileNumber=mobileNumber,
                    emergencyContact=emergencyContact,
                    user_id=user_id
                )

                db.session.add(profile)
                db.session.commit()

                response_object = {
                    'status': 'success',
                    'message': 'Profile created successfully',
                    'profile_id': profile.id
                }

        except Exception as e:
            print(e)
            response_object = {
                'status': 'error',
                'message': 'Failed to create profile'
            }

        return jsonify(response_object)

# PUT route to update profile
@app.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    try:
        from datetime import datetime  # Import datetime explicitly
        data = request.get_json()
        user_id = get_jwt_identity()  # Get the user_id from the JWT token

        # Query the profile for the current user
        profile = Profile.query.filter_by(user_id=user_id).first()

        if profile:
            # Update the profile fields
            profile.lname = data.get('lname', profile.lname)
            profile.fname = data.get('fname', profile.fname)
            profile.mname = data.get('mname', profile.mname)
            profile.age = data.get('age', profile.age)
            profile.gender = data.get('gender', profile.gender)
            profile.height = data.get('height', profile.height)
            profile.weight = data.get('weight', profile.weight)

            # Parse birthdate string and update profile.birthdate
            birthdate_str = data.get('birthdate', profile.birthdate.strftime('%Y-%m-%d'))
            birthdate_datetime = datetime.strptime(birthdate_str, '%Y-%m-%d')
            profile.birthdate = birthdate_datetime.date()

            profile.address = data.get('address', profile.address)
            profile.civilStatus = data.get('civilStatus', profile.civilStatus)
            profile.email = data.get('email', profile.email)
            profile.mobileNumber = data.get('mobileNumber', profile.mobileNumber)
            profile.emergencyContact = data.get('emergencyContact', profile.emergencyContact)

            db.session.commit()

            response_object = {
                'status': 'success',
                'message': 'Profile updated successfully',
                'profile_id': profile.id
            }
        else:
            response_object = {
                'status': 'error',
                'message': 'Profile not found'
            }

    except Exception as e:
        print(e)
        response_object = {
            'status': 'error',
            'message': 'Failed to update profile'
        }

    return jsonify(response_object)
#########################################################################
@app.route('/survey', methods=['GET', 'POST'])
@jwt_required()
def get_or_create_survey():
    if request.method == 'GET':
        try:
            user_id = get_jwt_identity()  # Get the user_id from the JWT token

            # Query the survey for the current user
            survey = Surveys.query.filter_by(user_id=user_id).first()

            if survey:
                response_object = {
                    'status': 'success',
                    'survey': {
                        'id': survey.id,
                        'snoring': survey.snoring,
                        'tired': survey.tired,
                        'observed': survey.observed,
                        'pressure': survey.pressure,
                        'bmi': survey.bmi,
                        'testage': survey.testage,
                        'neck': survey.neck,
                        'testgender': survey.testgender,
                        'user_id': survey.user_id
                    }
                }
            else:
                response_object = {
                    'status': 'error',
                    'message': 'Survey not found'
                }
        except Exception as e:
            print(e)
            response_object = {
                'status': 'error',
                'message': 'Failed to fetch survey'
            }

        return jsonify(response_object)

    elif request.method == 'POST':
        try:
            user_id = get_jwt_identity()  # Get the user_id from the JWT token

            # Check if a survey already exists for the user
            existing_survey = Surveys.query.filter_by(user_id=user_id).first()

            if existing_survey:
                response_object = {
                    'status': 'error',
                    'message': 'Survey already exists'
                }
            else:
                data = request.get_json()
                snoring = data.get('snoring')
                tired = data.get('tired')
                observed = data.get('observed')
                pressure = data.get('pressure')
                bmi = data.get('bmi')
                testage = data.get('testage')
                neck = data.get('neck')
                testgender = data.get('testgender')

                # Create a new survey record
                survey = Surveys(
                    snoring=snoring,
                    tired=tired,
                    observed=observed,
                    pressure=pressure,
                    bmi=bmi,
                    testage=testage,
                    neck=neck,
                    testgender=testgender,
                    user_id=user_id
                )

                db.session.add(survey)
                db.session.commit()

                response_object = {
                    'status': 'success',
                    'message': 'Survey created successfully',
                    'survey_id': survey.id
                }

        except Exception as e:
            print(e)
            response_object = {
                'status': 'error',
                'message': 'Failed to create survey'
            }

        return jsonify(response_object)

@app.route('/survey', methods=['PUT'])
@jwt_required()
def update_survey():
    try:
        data = request.get_json()
        user_id = get_jwt_identity()  # Get the user_id from the JWT token

        # Query the survey for the current user
        survey = Surveys.query.filter_by(user_id=user_id).first()

        if survey:
            # Update the survey fields
            survey.snoring = data.get('snoring', survey.snoring)
            survey.tired = data.get('tired', survey.tired)
            survey.observed = data.get('observed', survey.observed)
            survey.pressure = data.get('pressure', survey.pressure)
            survey.bmi = data.get('bmi', survey.bmi)
            survey.testage = data.get('testage', survey.testage)
            survey.neck = data.get('neck', survey.neck)
            survey.testgender = data.get('testgender', survey.testgender)

            db.session.commit()

            response_object = {
                'status': 'success',
                'message': 'Survey updated successfully',
                'survey_id': survey.id
            }
        else:
            response_object = {
                'status': 'error',
                'message': 'Survey not found'
            }

    except Exception as e:
        print(e)
        response_object = {
            'status': 'error',
            'message': 'Failed to update survey'
        }

    return jsonify(response_object)
#########################################################################
# Add a new route to show appointments based on user_id
@app.route('/patient-dashboard/<int:user_id>/appointments', methods=['GET'])
@jwt_required()
def show_user_appointments(user_id):
    try:
        # Query appointments for the specified user_id in descending order by date and time
        appointments_data = Appointments.query.filter_by(user_id=user_id).order_by(
            desc(Appointments.date), desc(Appointments.time)).all()

        appointments = []
        for appointment in appointments_data:
            appointments.append({
                'id': appointment.id,
                'name': appointment.name,
                'status': appointment.status,
                'date': appointment.date.strftime('%Y-%m-%d'),
                'time': appointment.time.strftime('%H:%M'),
                'user_id': appointment.user_id
            })

        response_object = {
            'status': 'success',
            'appointments': appointments
        }

    except Exception as e:
        print(e)
        response_object = {
            'status': 'error',
            'message': 'Failed to fetch appointments'
        }

    return jsonify(response_object)

# The GET and POST routes to the patient dashboard
@app.route('/patient-dashboard', methods=['GET', 'POST'])
@jwt_required()
def show_or_add_appointments():
    if request.method == 'GET':
        try:
            user_id = get_jwt_identity()  # Get the user_id from the JWT token

            user_role = Users.query.filter_by(id=user_id).first()
            if (user_role.role_id == 2):

                # Query appointments for the current user in descending order by date and time
                appointments_data = Appointments.query.filter_by(user_id=user_id).order_by(
                    desc(Appointments.date), desc(Appointments.time)).all()

                appointments = []
                for appointment in appointments_data:
                    appointments.append({
                        'id': appointment.id,
                        'name': appointment.name,
                        'status': appointment.status,
                        'date': appointment.date.strftime('%Y-%m-%d'),
                        'time': appointment.time.strftime('%H:%M'),
                        'user_id': appointment.user_id
                    })

                response_object = {
                    'status': 'success',
                    'appointments': appointments
                }
            else:
                appointments_data = Appointments.query.filter_by(doctor_id=user_id).order_by(
                    desc(Appointments.date), desc(Appointments.time)).all()

                appointments = []
                for appointment in appointments_data:
                    patient = Profile.query.filter_by(user_id=appointment.user_id).first()
                    name = patient.fname + ' ' + patient.mname + ' ' + patient.lname

                    appointments.append({
                        'id': appointment.id,
                        'name': name,
                        'status': appointment.status,
                        'date': appointment.date.strftime('%Y-%m-%d'),
                        'time': appointment.time.strftime('%H:%M'),
                        'user_id': appointment.user_id
                    })

                response_object = {
                    'status': 'success',
                    'appointments': appointments
                }
                
        except Exception as e:
            print(e)
            response_object = {
                'status': 'error',
                'message': 'Failed to fetch appointments'
            }

        return jsonify(response_object)

    elif request.method == 'POST':
        try:
            data = request.get_json()
            nameid = data.get('name')
            name = nameid.split(',')[0]
            doctorid = int(nameid.split(',')[1])
            status = data.get('status')
            date_str = data.get('date')
            time_str = data.get('time')
            date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            time_obj = datetime.datetime.strptime(time_str, '%H:%M').time()
            appointment_id = str(uuid.uuid4())
            user_id = get_jwt_identity()  # Get the user_id from the JWT token
            
            # Query appointments for the current user in descending order by date and time
            appointments_data = Appointments.query.filter_by(user_id=user_id).order_by(
                desc(Appointments.date), desc(Appointments.time)).all()

            appointments = Appointments(
                id=appointment_id, name=name, status=status, date=date, time=time_obj, user_id=user_id, doctor_id=doctorid)

            db.session.add(appointments)
            db.session.commit()

            response_object = {
                'status': 'success',
                'message': 'Appointment added successfully',
                'appointment_id': appointment_id
            }

        except Exception as e:
            print(e)
            response_object = {
                'status': 'error',
                'message': 'Failed to add appointment'
            }

        return jsonify(response_object)


# The PUT and DELETE routes to the patient dashboard
@app.route('/patient-dashboard/<string:appointment_id>', methods=['PUT', 'DELETE'])
def update_or_delete_appointment(appointment_id):
    if request.method == 'PUT':
        try:
            # Get the data from the PUT request
            data = request.get_json()

            # Extract the relevant information from the data
            name = data.get('name')
            status = data.get('status')
            date_str = data.get('date')
            time_str = data.get('time')
            IsDoctor = data.get('IsDoctor')

            # Convert date string to datetime object
            date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()

            # Convert time string to time object
            time_obj = datetime.datetime.strptime(time_str, '%H:%M').time()

            # Query the appointment to be updated
            appointment = Appointments.query.get(appointment_id)

            if appointment:
                # Update the appointment fields
                if not IsDoctor:
                    appointment.name = name
                appointment.status = status
                appointment.date = date
                appointment.time = time_obj

                # Commit the changes to the database
                db.session.commit()

                response_object = {
                    'status': 'success',
                    'message': 'Appointment updated successfully',
                    'appointment_id': appointment_id
                }
            else:
                response_object = {
                    'status': 'error',
                    'message': 'Appointment not found'
                }

        except Exception as e:
            print(e)
            response_object = {
                'status': 'error',
                'message': 'Failed to update appointment'
            }

        return jsonify(response_object)

    elif request.method == 'DELETE':
        try:
            # Query the appointment to be deleted
            appointment = Appointments.query.get(appointment_id)

            if appointment:
                # Delete the appointment from the database
                db.session.delete(appointment)

                # Commit the changes to the database
                db.session.commit()

                response_object = {
                    'status': 'success',
                    'message': 'Appointment deleted successfully',
                    'appointment_id': appointment_id
                }
            else:
                response_object = {
                    'status': 'error',
                    'message': 'Appointment not found'
                }

        except Exception as e:
            print(e)
            response_object = {
                'status': 'error',
                'message': 'Failed to delete appointment'
            }

        return jsonify(response_object)

########################################################################
# POST route request for Signup
@app.route("/signup", methods=["POST"])
def signup():
    try:
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")
        confirm_password = data.get("confirm_password")
        role_id = data.get("role_id", 2)  # Default role_id

        # Check if password and confirm_password match
        if password != confirm_password:
            return jsonify({"error": "Password and confirm password do not match"}), 400

        # Generate a unique UserID for the user
        user_id = str(uuid.uuid4())[:6]

        # Hash the password
        hashed_password = bcrypt.hash(password)

        # Check if email already exists
        existing_user = Users.query.filter_by(email=email).first()

        if existing_user:
            return jsonify({"error": "Email already exists"}), 400

        # Create a new user with the generated UserID
        new_user = Users(
            email=email, password=hashed_password, role_id=role_id, UserID=user_id
        )

        db.session.add(new_user)
        db.session.commit()

        return (
            jsonify({"message": "User registered successfully", "UserID": user_id}),
            201,
        )

    except IntegrityError as e:
        db.session.rollback()
        return jsonify({"error": "Email already exists"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# POST routes request for Signin
@app.route('/signin', methods=['POST'])
def signin():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        # Query the user by email
        user = Users.query.filter_by(email=email, role_id=2).first()

        if user:
            stored_hashed_password = user.password
            is_valid_password = bcrypt.verify(password, stored_hashed_password)

            if is_valid_password:
                access_token = create_access_token(identity=user.id)
                return jsonify({
                    'message': 'Login successful',
                    'user_Id': user.UserID,
                    'access_token': access_token
                }), 200
            else:
                return jsonify({'message': 'Invalid credentials'}), 401
        else:
            return jsonify({'message': 'User not found'}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# POST routes request for Login
@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        # Query the user by email
        user = Users.query.filter_by(email=email, role_id=1).first()

        if user:
            stored_hashed_password = user.password
            is_valid_password = bcrypt.verify(password, stored_hashed_password)

            if is_valid_password:
                access_token = create_access_token(identity=user.id)
                return jsonify({
                    'message': 'Login successful',
                    'access_token': access_token
                }), 200
            else:
                return jsonify({'message': 'Invalid credentials'}), 401
        else:
            return jsonify({'message': 'User not found'}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500

#########################################################################################

@app.route("/insert", methods=["POST"])
def insert_data():
    try:
        data = request.get_json()  # Get the JSON data from the request
        conn = sqlite3.connect(
            r"F:\ProjectDesign2_Website\Current n Backup\Current\flask-vue-edosa\resultsbackend\SensorReadings.db"
        )
        cursor = conn.cursor()

        # Begin a transaction
        conn.execute("BEGIN TRANSACTION")

        cursor.execute(
            """
            INSERT INTO SensorReadings (UserID, Therm, ECG, Airflow, Snore, SpO2, HR, TimeIn, TimeOut, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                data["UserID"],
                data["Temp"],
                data["ECG"],
                data["AirFlow"],
                data["Snore"],
                data["SpO2"],
                data["PulseRate"],
                data["TimeIn"],
                data["TimeOut"],
                data["Timestamp"],
            ),
        )

        # Commit the transaction if all insertions are successful
        conn.commit()
        conn.close()
        executor.submit(prediction_task, data)
        print("Data inserted")
        return "Data inserted"
    except Exception as e:
        # Rollback the transaction if an error occurs
        conn.rollback()
        conn.close()
        print("Error", e)
        return "Data not inserted"


def prediction_task(data):
    try:
        print("prediction starting")
        result = prediction(data)
        print("prediction end")
        print("Data inserting...")
        conn = sqlite3.connect(
            r"F:\ProjectDesign2_Website\Current n Backup\Current\flask-vue-edosa\resultsbackend\SensorReadings.db"
        )
        cursor = conn.cursor()

        # Begin a transaction
        conn.execute("BEGIN TRANSACTION")

        cursor.execute(
            """
            INSERT INTO AHI_table (Severity, AHI, TimeIn, TimeOut, UserID, Normal, Apnea, Hypopnea)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                result["Severity"],
                result["AHI"],
                result["TimeIn"],
                result["TimeOut"],
                result["UserID"],
                result["Normal"],
                result["Apnea"],
                result["Hypopnea"],
            ),
        )

        # Commit the transaction if all insertions are successful
        conn.commit()
        conn.close()
        print("Data inserted")
    except Exception as e:
        # Rollback the transaction if an error occurs
        conn.rollback()
        conn.close()
        print("Error", e)


@app.route("/retrieveUserData", methods=["POST"])
def getUser_data():
    try:
        data = request.get_json()  # Get the JSON data from the request
        conn = sqlite3.connect(
            r"F:\ProjectDesign2_Website\Current n Backup\Current\flask-vue-edosa\resultsbackend\SensorReadings.db"
        )
        cursor = conn.cursor()

        # Begin a transaction
        conn.execute("BEGIN TRANSACTION")

        cursor.execute("SELECT UserID, TimeIn, TimeOut FROM SensorReadings WHERE UserID=? ORDER BY TimeIn DESC, TimeOut DESC",
        (data["UserID"],),)

        # Fetch all the rows from the result
        rows = cursor.fetchall()

        if rows:
            # Create a list to store the retrieved data
            data_list = []
            for row in rows:
                UserID, TimeIn, TimeOut = row
                time_dict = {
                    "TimeIn": TimeIn,
                    "TimeOut": TimeOut,
                }
                data_list.append(time_dict)

            # Create a dictionary to store the final response
            response_dict = {
                "UserID": data["UserID"],
                "Time": data_list,
            }

            conn.commit()
            conn.close()
            print("Data retrieved")
            return jsonify(response_dict), 200

        conn.commit()
        conn.close()
        print("Data unavailable")
        return "No data found for the given UserID", 404

    except Exception as e:
        # Rollback the transaction if an error occurs
        conn.rollback()
        conn.close()
        print("Error", e)
        return str(e), 500


@app.route("/retrieveUserInstance", methods=["POST"])
def getInstance_data():
    try:
        data = request.get_json()  # Get the JSON data from the request
        conn = sqlite3.connect(
            r"F:\ProjectDesign2_Website\Current n Backup\Current\flask-vue-edosa\resultsbackend\SensorReadings.db"
        )
        cursor = conn.cursor()

        # Begin a transaction
        conn.execute("BEGIN TRANSACTION")

        cursor.execute(
            "SELECT * FROM SensorReadings WHERE UserID=? AND TimeIn=? AND TimeOut=?",
            (data["UserID"], data["TimeIn"], data["TimeOut"]),
        )

        # Fetch the row from the result
        row = cursor.fetchone()

        if row is not None:
            # Extract the values from the row
            (
                id_,
                UserID,
                Therm,
                ECG,
                Airflow,
                Snore,
                SpO2,
                HR,
                TimeIn,
                TimeOut,
                timestamp,
            ) = row

            # Create a dictionary to store the retrieved data
            data_dict2 = {
                "UserID": UserID,
                "Therm": Therm,
                "ECG": ECG,
                "Airflow": Airflow,
                "Snore": Snore,
                "SpO2": SpO2,
                "HR": HR,
                "TimeIn": TimeIn,
                "TimeOut": TimeOut,
                "Timestamp": timestamp,
            }

            # Retrieve data from AHI_table
            cursor.execute(
                "SELECT Severity, AHI, Normal, Apnea, Hypopnea, MT, avg_HR, lowest_HR, highest_HR, ODI3, ODI4, lowest_SpO2, avg_SpO2, highest_SpO2, repeat_study, recommendations FROM AHI_table WHERE UserID=? AND TimeIn=? AND TimeOut=?",
                (data["UserID"], data["TimeIn"], data["TimeOut"]),
            )

            # Fetch the row from the result
            ahi_row = cursor.fetchone()

            if ahi_row is not None:
                # Extract the values from the AHI row
                Severity, AHI, Normal, Apnea, Hypopnea, MT, avg_HR, lowest_HR, highest_HR, ODI3, ODI4, lowest_SpO2, avg_SpO2, highest_SpO2, repeat_study, recommendations = ahi_row

                # Create a dictionary to store the retrieved data from AHI_table
                ahi_dict = {
                    "Severity": Severity,
                    "AHI": AHI,
                    "Normal": Normal,
                    "Apnea": Apnea,
                    "Hypopnea": Hypopnea,
                    "MT": MT,
                    "avg_HR": avg_HR,
                    "lowest_HR": lowest_HR,
                    "highest_HR": highest_HR,
                    "ODI3": ODI3,
                    "ODI4": ODI4,
                    "lowest_SpO2": lowest_SpO2,
                    "avg_SpO2": avg_SpO2,
                    "highest_SpO2": highest_SpO2,
                    "repeat_study": repeat_study,
                    "recommendations": recommendations,
                }

                # Combine the data dictionaries
                data_dict2.update(ahi_dict)

            conn.commit()
            conn.close()
            print("Data retrieved")
            return jsonify(data_dict2), 200

        conn.commit()
        conn.close()
        print("Data unavailable")
        return "row does not exist", 404

    except Exception as e:
        # Rollback the transaction if an error occurs
        conn.rollback()
        conn.close()
        print("Error", e)
        return str(e), 500

###########################################################################

@app.route("/retrieveAHItable", methods=["POST"])
def getInstance_AHIdata():
    try:
        data = request.get_json()  # Get the JSON data from the request
        conn = sqlite3.connect(
            r"F:\ProjectDesign2_Website\Current n Backup\Current\flask-vue-edosa\resultsbackend\SensorReadings.db"
        )
        cursor = conn.cursor()

        # Begin a transaction
        conn.execute("BEGIN TRANSACTION")

        # Retrieve data from AHI_table
        cursor.execute(
            "SELECT Severity, AHI, Normal, Apnea, Hypopnea FROM AHI_table WHERE UserID=? AND TimeIn=? AND TimeOut=?",
            (data["UserID"], data["TimeIn"], data["TimeOut"]),
        )

        # Fetch the row from the result
        ahi_row = cursor.fetchone()
        
        if ahi_row is not None:
            # Extract the values from the AHI row
            Severity, AHI, Normal, Apnea, Hypopnea = ahi_row

            # Create a dictionary to store the retrieved data from AHI_table
            ahi_dict = {
                "Severity": Severity,
                "AHI": AHI,
                "Normal": Normal,
                "Apnea": Apnea,
                "Hypopnea": Hypopnea
            }

            print("ahi_dict: ", ahi_dict)
            
            conn.commit()
            conn.close()
            print("Data retrieved")
            return jsonify(ahi_dict), 200       


        conn.commit()
        conn.close()
        print("Data unavailable")
        return "row does not exist", 404

    except Exception as e:
        # Rollback the transaction if an error occurs
        conn.rollback()
        conn.close()
        print("Error", e)
        return str(e), 500


if __name__ == "__main__":
    app.run(debug=True)