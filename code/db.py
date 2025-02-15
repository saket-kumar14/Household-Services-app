from flask_sqlalchemy import SQLAlchemy 
from datetime import * 


db=SQLAlchemy()

#orm-object relational mapping(sqlalchemy)
class User(db.Model):
    _tablename_ = 'user'
    id = db.Column(db.Integer, primary_key=True)    
    user_name = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False) 
    name = db.Column(db.String(80), nullable=True)   
    address = db.Column(db.String(120), nullable=True)
    pincode = db.Column(db.Integer, nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    is_professional = db.Column(db.Boolean, default=False)
    is_customer = db.Column(db.Boolean, default=False)
    is_approved = db.Column(db.Boolean, default=False)
    is_rejected = db.Column(db.Boolean, default=False)
    overall_rating = db.Column(db.Float, default=0.0)
    rating_count = db.Column(db.Integer, default=0)
    pro_file = db.Column(db.String(80), nullable=True)
    pro_experience = db.Column(db.String(120), nullable=True)
    #Foreign key
    service_id = db.Column(db.Integer, db.ForeignKey('services.id', ondelete="SET NULL"), nullable=True)
    #Relationships
    service = db.relationship('Services', back_populates='professionals')
    customer_request = db.relationship('ServiceRequest', back_populates='customer', foreign_keys='ServiceRequest.customer_id')
    professional_request = db.relationship('ServiceRequest', back_populates='professional', foreign_keys='ServiceRequest.professional_id')


class Services(db.Model):
    _tablename_ = 'services'
    id = db.Column(db.Integer, primary_key=True)    
    service_name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(120), nullable=True)
    base_price = db.Column(db.Integer, nullable=True)
    time_duration = db.Column(db.String(80), nullable=True)
    #Relationships
    professionals = db.relationship('User', back_populates='service', cascade="all, delete")
    request = db.relationship('ServiceRequest', back_populates='service', cascade="all, delete-orphan")


class ServiceRequest(db.Model):
    _tablename_ = 'service_request'
    id = db.Column(db.Integer, primary_key=True)    
    request_type = db.Column(db.String(80), nullable=True) #private/public
    direction = db.Column(db.String(120), nullable=True)#Description of service
    status = db.Column(db.String(80), nullable=True)#pending/accepted/rejected/completed
    date_of_request = db.Column(db.Date, nullable=False, default=datetime.now().date())
    date_closed = db.Column(db.Date, nullable=True)
    rating_by_customer = db.Column(db.Float, default=0.0)
    review_by_customer = db.Column(db.String(120), nullable=True)
    #Foreign key
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    professional_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    #Relationships
    service = db.relationship('Services', back_populates='request')
    customer = db.relationship('User', back_populates='customer_request', foreign_keys=[customer_id])
    professional = db.relationship('User', back_populates='professional_request', foreign_keys=[professional_id])
