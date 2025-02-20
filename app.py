import os   
from flask import *
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


from db import *
from config import *

app = Flask(__name__)
app.config.from_object(Config)


#Initialize Database
db.init_app(app)
app.app_context().push()



#function to create admin
def create_admin():
    with app.app_context():
        admin_user = User.query.filter_by(is_admin=True).first()
        if not admin_user:
            admin_user = User(user_name='admin', password=generate_password_hash('admin123'), is_admin=True, is_approved=True)
            db.session.add(admin_user)
            db.session.commit()
            print('Admin created successfully')

with app.app_context():
    db.create_all()
    create_admin()

#average rating function
def update_overall_rating(professional_id):
    # Query to fetch all ratings for the given professional_id
    ratings = db.session.query(ServiceRequest.rating_by_customer).filter(
        ServiceRequest.professional_id == professional_id,
        ServiceRequest.rating_by_customer > 0  # Exclude ratings that are zero or invalid
    ).all()

    # Calculate the average rating and rating count
    if ratings:
        rating_count = len(ratings)
        average_rating = round(sum(r[0] for r in ratings) / rating_count, 2)
    else:
        rating_count = 0
        average_rating = 0.0  # Default to 0.0 if no ratings exist

    # Update the professional's overall_rating in the User table
    professional = User.query.filter_by(id=professional_id).first()
    if professional: 
        professional.overall_rating = average_rating
        professional.rating_count = rating_count
        db.session.commit()
        

@app.route('/', methods=['GET', 'POST'])
def index():
    services = Services.query.join(User).filter(User.is_approved == True).all()
    return render_template('index.html', services=services)

#route for login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(user_name=username).first()
        admin = User.query.filter_by(is_admin=True ,user_name=username).first()
        if admin and check_password_hash(admin.password, password):
            session['username'] = username
            session['is_admin'] = True
            flash('Login successful. Welcome, Admin!', 'success')
            return redirect('/admin_dashboard')
        if user and check_password_hash(user.password, password):  
            session['user_id'] = user.id
            session['username'] = user.user_name
            session['is_customer'] = user.is_customer
            session['is_professional'] = user.is_professional
            if user.is_professional:
                user_type = 'professional'
                if user.is_approved==False and user.is_rejected==False:  
                    flash('Please wait for admin approval.', 'danger') 
                    return redirect('/login')
                if user.is_approved==False and user.is_rejected==True:
                    flash('Your registration has been rejected. Please reach out to admin at "admin@gmail.com".', 'danger')
                    return redirect('/login')
                if user.service_id==None:
                    flash('Your service is not available now. Please create a new account with other service.', 'danger')
                    return redirect('/login')
                return redirect('/'+user_type+'_dashboard')
            if user.is_customer:
                user_type = 'customer'
                flash('Login successful. Welcome, {}'.format(user.name), 'success')
                return redirect('/'+user_type+'_dashboard') 
        flash('Invalid username or password. Please try again.', 'danger')
    return render_template('login.html')




#route for professional registration
@app.route('/professional_register', methods=['GET', 'POST'])
def Professional_register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']
        address = request.form['address']
        pincode = request.form['pincode']
        pro_file = request.files['pro_file']
        pro_experience = request.form['pro_experience']
        service = request.form['service']
        #debug print
        print("File received:", pro_file.filename)
        print("File type:", pro_file.content_type)
        print("File extensions allowed:", app.config['UPLOAD_EXTENSIONS'])

        service_id = Services.query.filter_by(service_name=service).first().id
        user = User.query.filter_by(user_name=username).first()
        if user:
            flash('Username already exists. Please choose a different username.', 'danger')
            return redirect('/professional_register')
        file_name = secure_filename(pro_file.filename)
        if file_name != '':
            file_ext=os.path.splitext(file_name)[1]
            renamed_file_name = username+file_ext
            if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                abort(400)
            pro_file.save(os.path.join(app.config['UPLOAD_PATH'], renamed_file_name))
        else:
            renamed_file_name = None
            flash('No file selected', 'danger')
            return redirect('/professional_register')
        user = User(user_name=username, password=generate_password_hash(password), name=name, address=address, pincode=pincode, pro_file=renamed_file_name, pro_experience=pro_experience, service_id=service_id, is_professional=True,) 
        db.session.add(user)
        db.session.commit()
        flash('Registration successful. Please wait for approval.', 'success')
        return redirect('/login')
    services = Services.query.all()
    return render_template('professional_register.html', services=services)      
            

#route for customer registration
@app.route('/customer_register', methods=['GET', 'POST'])
def Customer_register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']
        address = request.form['address']
        pincode = request.form['pincode']
        user = User.query.filter_by(user_name=username).first()
        if user:
            flash('Username already exists. Please choose a different username.', 'danger')
            return redirect('/customer_register')
        else:
            user = User(user_name=username, password=generate_password_hash(password), name=name, address=address, pincode=pincode, is_customer=True, is_approved=True)
            db.session.add(user)
            db.session.commit()
            flash('Registration successful. Please login.', 'success')
            return redirect('/login')
    return render_template('customer_register.html')

#route for logout
@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('is_admin', None)
    session.pop('is_professional', None)
    session.pop('is_customer', None)
    flash('You have been logged out.', 'success')
    return redirect('/')

#admin_dashboard and related routes starts    
#route for admin dashboard
@app.route('/admin_dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if not session.get('is_admin'):
        flash('Session over. Login to access this page.', 'danger')
        return redirect('/login')
    services = Services.query.all()
    requests = ServiceRequest.query.all()
    unapproved_professionals = User.query.filter_by(is_professional=True, is_approved=False, is_rejected=False).all()
    return render_template('admin_dashboard.html', unapproved_professionals=unapproved_professionals, requests=requests, services=services, admin_name=session.get('username'))

#search functionality  for admin
@app.route('/admin_search', methods=['GET'])
def admin_search():
    query = request.args.get('search_query', '').strip()  # Get the search query from the URL
    if query:
        # Perform a case-insensitive search on service name or description
        result_1 = Services.query.filter(
            (Services.service_name.ilike(f'%{query}%')) |
            (Services.description.ilike(f'%{query}%'))
        ).all()

        result_2 = User.query.filter_by(is_professional=True).filter(
            (User.name.ilike(f'%{query}%')) |
            (User.user_name.ilike(f'%{query}%')) |
            (User.pincode.ilike(f'%{query}%'))
        )

        result_3 = User.query.filter_by(is_customer=True).filter(
            (User.name.ilike(f'%{query}%')) |
            (User.user_name.ilike(f'%{query}%')) |
            (User.pincode.ilike(f'%{query}%'))
        )
    else:
        result_1 = Services.query.all()
        result_2 = User.query.filter_by(is_professional=True).all()
        result_3 = User.query.filter_by(is_customer=True).all()
    return render_template('admin_search.html', search_query=query, services=result_1, professionals=result_2, customers=result_3)

@app.route('/admin_dashboard/create_service', methods=['GET', 'POST'])
def create_service():
    if not session.get('is_admin'):
        flash('Session over. Login to access this page.', 'danger')
        return redirect('/login')
    if request.method == 'POST':
        service_name = request.form['service_name']
        description = request.form['description']
        base_price = request.form['base_price']
        time_duration = request.form['time_duration']
        new_service = Services(service_name=service_name, description=description, base_price=base_price, time_duration=time_duration)
        db.session.add(new_service)
        db.session.commit()
        flash('New service created', 'success')
        return redirect('/admin_dashboard')
    return render_template('create_service.html')

@app.route('/admin_dashboard/edit_service/<int:service_id>', methods=['GET', 'POST'])
def edit_service(service_id):
    if not session.get('is_admin'):
        flash('Session over. Login to access this page.', 'danger')
        return redirect('/login')
    service = Services.query.get_or_404(service_id)
    if request.method == 'POST':
        service.description = request.form['description']
        service.base_price = request.form['base_price']
        service.time_duration = request.form['time_duration']
        db.session.commit()
        flash('Service updated', 'success')
        return redirect('/admin_dashboard')
    return render_template('edit_service.html', service=service)

@app.route('/admin_dashboard/delete_service/<int:service_id>', methods=['GET','POST'])
def delete_service(service_id):
    if not session.get('is_admin'):
        flash('Session over. Login to access this page.', 'danger')
        return redirect('/login')
    service = Services.query.get_or_404(service_id)
    approved_professionals = User.query.filter_by(is_professional=True, is_approved=True, service_id=service_id).all()
    for professional in approved_professionals:
        professional.is_approved = None       
    db.session.delete(service)
    db.session.commit()
    flash('Service deleted', 'success')
    return redirect('/admin_dashboard')

@app.route('/admin_dashboard/professional_details/<int:professional_id>', methods=['GET', 'POST'])
def professional_details(professional_id):
    if not session.get('is_admin'):
        flash('Session over. Login to access this page.', 'danger')
        return redirect('/login')
    professional = User.query.get_or_404(professional_id)
    return render_template('professional_details.html', professional=professional)

@app.route('/admin_dashboard/approve_professional/<int:professional_id>', methods=['GET', 'POST'])
def approve_professional(professional_id):
    if not session.get('is_admin'):
        flash('Session over. Login to access this page.', 'danger')
        return redirect('/login')
    professional = User.query.get_or_404(professional_id)
    professional.is_approved = True
    db.session.commit()
    flash('Professional approved', 'success')
    return redirect('/admin_dashboard')

@app.route('/admin_dashboard/reject_professional/<int:professional_id>', methods=['GET', 'POST'])
def reject_professional(professional_id):
    if not session.get('is_admin'):
        flash('Session over. Login to access this page.', 'danger')
        return redirect('/login')
    professional = User.query.get_or_404(professional_id)
    pdf_file = professional.pro_file
    if pdf_file:
        pdf_path = os.path.join(app.config['UPLOAD_PATH'], pdf_file)
        if os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
                print("File deleted:")
            except Exception as e:
                print("Error deleting file:", e)
        else:
            print("File not found:")
    professional.is_approved = False
    professional.is_rejected = True
    db.session.commit()
    flash('Professional rejected', 'success')
    return redirect('/admin_dashboard')    

@app.route('/admin_dashboard/review_professional/<int:professional_id>', methods=['GET', 'POST'])
def review_professional(professional_id):
    if not session.get('is_admin'):
        flash('Session over. Login to access this page.', 'danger')
        return redirect('/login')
    professional = User.query.get_or_404(professional_id)
    service_request = ServiceRequest.query.filter_by(professional_id=professional_id).all()
    services = Services.query.filter_by(id=professional.service_id).first()
    return render_template('review_professional.html', professional=professional, service_request=service_request, services=services)

@app.route('/admin_dashboard/block_professional/<int:professional_id>', methods=['GET', 'POST'])
def block_professional(professional_id):
    if not session.get('is_admin'):
        flash('Session over. Login to access this page.', 'danger')
        return redirect('/login')
    professional = User.query.get_or_404(professional_id)
    professional.is_approved = False
    professional.is_rejected = True
    db.session.commit()
    flash('Professional blocked', 'success')
    return redirect('/admin_dashboard')

@app.route('/admin_dashboard/unblock_professional/<int:professional_id>', methods=['GET', 'POST'])
def unblock_professional(professional_id):
    if not session.get('is_admin'):
        flash('Session over. Login to access this page.', 'danger')
        return redirect('/login')
    professional = User.query.get_or_404(professional_id)
    professional.is_approved = True
    professional.is_rejected = False
    db.session.commit()
    flash('Professional unblocked', 'success')
    return redirect('/admin_dashboard')

@app.route('/admin_dashboard/review_customer/<int:customer_id>', methods=['GET', 'POST'])
def review_customer(customer_id):
    if not session.get('is_admin'):
        flash('Session over. Login to access this page.', 'danger')
        return redirect('/login')
    customer = User.query.get_or_404(customer_id)
    service_request = ServiceRequest.query.filter_by(customer_id=customer_id).all()
    #services = Services.query.filter_by(id=customer.service_id).first()
    services = Services.query.join(User).filter(User.is_approved == True).all()
    service_history = ServiceRequest.query.filter_by(customer_id=customer.id).all()
    return render_template('review_customer.html', customer=customer, service_request=service_request, services=services, service_history=service_history)

@app.route('/admin_dashboard/block_customer/<int:customer_id>', methods=['GET', 'POST'])
def block_customer(customer_id):
    if not session.get('is_admin'):
        flash('Session over. Login to access this page.', 'danger')
        return redirect('/login')
    customer = User.query.get_or_404(customer_id)
    customer.is_approved = False
    customer.is_rejected = True
    db.session.commit()
    flash('Customer blocked', 'success')
    return redirect('/admin_dashboard')

@app.route('/admin_dashboard/unblock_customer/<int:customer_id>', methods=['GET', 'POST'])
def unblock_customer(customer_id):  
    if not session.get('is_admin'):
        flash('Session over. Login to access this page.', 'danger')
        return redirect('/login')
    customer = User.query.get_or_404(customer_id)
    customer.is_approved = True
    customer.is_rejected = False
    db.session.commit()
    flash('Customer unblocked', 'success')
    return redirect('/admin_dashboard')

@app.route('/admin_dashboard/admin_summary', methods=['GET', 'POST'])
def admin_summary():
    if not session.get('is_admin'):
        flash('Session over. Login to access this page.', 'danger')
        return redirect('/login')
    service_counts = {}
    services = Services.query.join(ServiceRequest, Services.id == ServiceRequest.service_id).filter(ServiceRequest.status == 'completed').all()
    for service in services:
        service_counts[service.service_name] = ServiceRequest.query.filter_by(service_id=service.id, status='completed').count()
    

    summary = os.path.join(curr_dir, 'static', 'image', 'summary.png')

    plt.figure(figsize=(6, 4))
    plt.pie(service_counts.values(), labels=service_counts.keys(), autopct='%1.1f%%')
    plt.title('Most Services Used')
    plt.savefig(summary, format='png')
    plt.close()

    completed = ServiceRequest.query.filter_by(status='completed').count()
    accepted = ServiceRequest.query.filter_by(status='accepted').count()
    rejected = ServiceRequest.query.filter_by(status='rejected').count()
    pending = ServiceRequest.query.filter_by(status='pending').count()


    summary1 = os.path.join(curr_dir, 'static', 'image', 'summary1.png')

    status = ['Completed', 'Accepted', 'Rejected', 'Pending']
    counts = [completed, accepted, rejected, pending]

    plt.figure(figsize=(6, 4))
    plt.bar(x=status, height=counts)
    plt.title('Service Request Status')
    plt.xlabel('Status Type')
    plt.ylabel('Count')
    plt.savefig(summary1, format='png')
    plt.close()

    return render_template('admin_summary.html', services=services, service_counts=service_counts, completed=completed, accepted=accepted, rejected=rejected, pending=pending)




#admin_dashboard and relate routes ends


#professional_dashboard and related routes starts
@app.route('/professional_dashboard', methods=['GET', 'POST'])
def professional_dashboard():
    if not session.get('is_professional'):
        flash('Session over. Login to access this page.', 'danger')
        return redirect('/login')
    pro_id=User.query.filter_by(user_name=session.get('username')).first().id
    professional = User.query.filter_by(id=pro_id).first()
    if professional.is_approved==False and professional.is_rejected==False:  
        flash('Please wait for admin approval. Thank you!', 'danger') 
        return redirect('/login')
    if professional.is_approved==False and professional.is_rejected==True:
        flash('Your registration has been rejected. Please reach out to admin at "admin@gmail.com".', 'danger')
        return redirect('/login')
    pending_requests = ServiceRequest.query.filter_by(professional_id=pro_id, status='pending', request_type='private').all()
    accepted_requests = ServiceRequest.query.filter_by(professional_id=pro_id, status='accepted').all() 
    completed_requests = ServiceRequest.query.filter_by(professional_id=pro_id, status='completed').all()
    return render_template('professional_dashboard.html', pending_requests=pending_requests, accepted_requests=accepted_requests, completed_requests=completed_requests, professional=professional)

@app.route('/professional_dashboard/accept_request/<int:request_id>', methods=['GET', 'POST'])
def accept_request(request_id):
    if not session.get('is_professional'):
        flash('Session over. Login to access this page.', 'danger')
        return redirect('/login')
    request = ServiceRequest.query.get_or_404(request_id)
    request.status = 'accepted'
    db.session.commit()
    flash('Request accepted', 'success')
    return redirect('/professional_dashboard')

@app.route('/professional_dashboard/reject_request/<int:request_id>', methods=['GET', 'POST'])
def reject_request(request_id):
    if not session.get('is_professional'):
        flash('Session over. Login to access this page.', 'danger')
        return redirect('/login')
    request = ServiceRequest.query.get_or_404(request_id)
    request.status = 'rejected'
    db.session.commit()
    flash('Request rejected', 'success')
    return redirect('/professional_dashboard')

@app.route('/professional_dashboard/professional_summary', methods=['GET', 'POST'])
def professional_summary():
    if not session.get('is_professional'):
        flash('Session over. Login to access this page.', 'danger')
        return redirect('/login')
    
    completed = ServiceRequest.query.filter_by( professional_id=session.get('user_id'), status='completed').count()
    accepted = ServiceRequest.query.filter_by( professional_id=session.get('user_id'), status='accepted').count()
    rejected = ServiceRequest.query.filter_by( professional_id=session.get('user_id'), status='rejected').count()
    pending = ServiceRequest.query.filter_by( professional_id=session.get('user_id'), status='pending').count()


    summary2 = os.path.join(curr_dir, 'static', 'image', 'summary2.png')

    status = ['Completed', 'Accepted', 'Rejected', 'Pending']
    counts = [completed, accepted, rejected, pending]

    plt.figure(figsize=(6, 4))
    plt.bar(x=status, height=counts)
    plt.title('Service Request Status')
    plt.xlabel('Status Type')
    plt.ylabel('Count')
    plt.savefig(summary2, format='png')
    plt.close()

    return render_template('professional_summary.html', completed=completed, accepted=accepted, rejected=rejected, pending=pending)

#professional_dashboard and relate routes ends


#customer_dashboard and related routes starts
@app.route('/customer_dashboard', methods=['GET', 'POST'])
def customer_dashboard():
    if not session.get('is_customer'):
        flash('Session over. Login to access this page.', 'danger')
        return redirect('/login')
    customer = User.query.filter_by(user_name=session.get('username')).first()
    services = Services.query.join(User).filter(User.is_approved == True).all()
    service_history = ServiceRequest.query.filter_by(customer_id=customer.id).all()
    return render_template('customer_dashboard.html', services=services, service_history=service_history, customer=customer)

@app.route('/customer_search', methods=['GET'])
def customer_search():
    query = request.args.get('search_query', '').strip()  # Get the search query from the URL
    if query:
        # Perform a case-insensitive search on service name or description
        result_1 = Services.query.filter(
            (Services.service_name.ilike(f'%{query}%')) |
            (Services.description.ilike(f'%{query}%'))
        ).all()

        result_2 = User.query.filter_by(is_professional=True).filter(
            (User.name.ilike(f'%{query}%')) |
            (User.user_name.ilike(f'%{query}%')) |
            (User.pincode.ilike(f'%{query}%'))
        )
    else:
        result_1 = Services.query.all()
        result_2 = User.query.filter_by(is_professional=True).all()

    
    return render_template('customer_search.html', search_query=query, services=result_1, professionals=result_2)

@app.route('/customer_dashboard/search', methods=['GET', 'POST'])
def custom_search():
    if not session.get('is_customer'):
        flash('Session over. Login to access this page.', 'danger')
        return redirect('/login')
    customer = User.query.filter_by(user_name=session.get('username')).first()
    search_type = request.args.get('search_type')
    search_query = request.args.get('search_query')

    if search_query:
        if search_type == 'pincode':
            services = Services.query.join(User).filter(User.is_approved == True, User.pincode.like("%"+search_query+"%")).all()
        elif search_type == 'service_name':
            services = Services.query.filter(Services.service_name.like("%"+search_query+"%")).all()
        elif search_type == 'address':
            services = Services.query.join(User).filter(User.is_approved == True, User.address.like("%"+search_query+"%")).all()
    else:
        services = Services.query.join(User).filter(User.is_approved == True).all()

    return render_template('custom_search.html', customer=customer, services=services)


@app.route('/customer_dashboard/create_request/<int:service_id>', methods=['GET', 'POST'])
def create_request(service_id):
    if not session.get('is_customer'):
        flash('Session over. Login to access this page.', 'danger')
        return redirect('/login')
    professional = User.query.filter_by(is_professional=True, is_approved=True, service_id=service_id).all()
    if request.method == 'POST':
        professional = request.form.get('professional')
        direction = request.form.get('direction')
        pid = User.query.filter_by(user_name=professional).first().id
        customer = User.query.filter_by(user_name=session.get('username')).first()
        service_request = ServiceRequest(customer_id=customer.id, professional_id=pid, service_id=service_id, direction=direction, status='pending', request_type='private')
        db.session.add(service_request)
        db.session.commit()
        flash('Service Booked', 'success')
        return redirect('/customer_dashboard')   
    service = Services.query.get_or_404(service_id) 
    return render_template('create_request.html', service=service , professional=professional)

@app.route('/customer_dashboard/edit_request/<int:service_request_id>', methods=['GET', 'POST'])
def edit_request(service_request_id):
    if not session.get('is_customer'):
        flash('Session over. Login to access this page.', 'danger')
        return redirect('/login')
    customer = User.query.filter_by(user_name=session.get('username')).first()
    service = Services.query.filter_by(id=customer.service_id).first()
    service_request = ServiceRequest.query.get_or_404(service_request_id)
    professional = User.query.filter_by(id=service_request.professional_id).all()
    if request.method == 'POST':
        direction = request.form['direction']
        service_request.direction = direction
        date_of_request_str = request.form['date_of_request']
        date_of_request = datetime.strptime(date_of_request_str, '%Y-%m-%d').date()
        service_request.date_of_request = date_of_request
        db.session.commit()
        flash('Request updated', 'success')
        return redirect('/customer_dashboard')   
    return render_template('edit_request.html', service_request=service_request, service=service, customer=customer, professional=professional)

@app.route('/customer_dashboard/delete_request/<int:service_request_id>', methods=['GET', 'POST'])
def delete_request(service_request_id):
    if not session.get('is_customer'):
        flash('Session over. Login to access this page.', 'danger')
        return redirect('/login')
    service_request = ServiceRequest.query.get_or_404(service_request_id)
    db.session.delete(service_request)
    db.session.commit()
    flash('Request deleted', 'success')
    return redirect('/customer_dashboard')

@app.route('/customer_dashboard/close_request/<int:service_request_id>', methods=['GET', 'POST'])
def close_request(service_request_id):
    if not session.get('is_customer'):
        flash('Session over. Login to access this page.', 'danger')
        return redirect('/login')
    service_request = ServiceRequest.query.get_or_404(service_request_id)
    customer = User.query.filter_by(user_name=session.get('username')).first()
    if not service_request:
        flash('Request not found', 'danger')
        return redirect('/customer_dashboard')
    professional = User.query.filter_by(id=service_request.professional_id).first()
    service =  Services.query.filter_by(id=customer.service_id).first()
    if request.method == 'POST':
        rating_by_customer = request.form['rating']
        review_by_customer = request.form['review']
        service_request.rating_by_customer = rating_by_customer
        service_request.review_by_customer = review_by_customer
        service_request.status = 'completed'
        db.session.commit()

        # Update the professional's overall_rating
        update_overall_rating(service_request.professional_id)

        flash('Request closed', 'success')
        return redirect('/customer_dashboard')
    
    return render_template('rating.html', service_request=service_request, professional=professional, customer=customer, service=service)

@app.route('/customer_dashbooard/professional_profile/<int:professional_id>', methods=['GET', 'POST'])
def professional_profile(professional_id):
    if not session.get('is_customer'):
        flash('Session over. Login to access this page.', 'danger')
        return redirect('/login')
    professional = User.query.get_or_404(professional_id)
    reviews = ServiceRequest.query.filter_by(professional_id=professional_id, status='completed').all()
    return render_template('professional_profile.html', professional=professional, reviews=reviews)

@app.route('/customer_dashboard/customer_summary', methods=['GET', 'POST'])
def customer_summary():
    if not session.get('is_customer'):
        flash('Session over. Login to access this page.', 'danger')
        return redirect('/login')
    
    

    completed = ServiceRequest.query.filter_by(customer_id=session.get('user_id'), status='completed').count()
    accepted = ServiceRequest.query.filter_by(customer_id=session.get('user_id'), status='accepted').count()
    rejected = ServiceRequest.query.filter_by(customer_id=session.get('user_id'), status='rejected').count()
    pending = ServiceRequest.query.filter_by(customer_id=session.get('user_id'), status='pending').count()

    summary3 = os.path.join(curr_dir, 'static', 'image', 'summary3.png')

    status = ['Completed', 'Accepted', 'Rejected', 'Pending']
    counts = [completed, accepted, rejected, pending]

    plt.figure(figsize=(6, 4))
    plt.bar(x=status, height=counts)
    plt.title('Service Request Status')
    plt.xlabel('Status Type')
    plt.ylabel('Count')
    plt.savefig(summary3, format='png')
    plt.close()

    return render_template('customer_summary.html', completed=completed, accepted=accepted, rejected=rejected, pending=pending)


#customer_dashboard and relate routes ends
    


#Profile Settings for professional/customer
@app.route('/profile_settings', methods=['GET', 'POST'])
def profile_settings():
    if not session.get('is_customer') and not session.get('is_professional'):
        flash('Session over. Login to access this page.', 'danger')
        return redirect('/login')
    user = User.query.get_or_404(session.get('user_id'))
    if request.method == 'POST':
        if session.get('is_customer'):
            user.name = request.form['name']
            user.address = request.form['address']
            user.pincode = request.form['pincode']
        elif session.get('is_professional'):
            user.name = request.form['name']
            user.address = request.form['address']
            user.pincode = request.form['pincode']
            # Add any additional fields for professional update here
        db.session.commit()
        flash('Profile updated', 'success')
        return redirect('/profile_settings')
    return render_template('profile_settings.html', user=user)



if __name__=="__main__":
    app.run(debug=True)
