# Household-Services-app
##Description
It is a multi-user app (requires one admin and other service professionals/ customers) which
acts as platform for providing comprehensive home servicing and solutions. It is capable of
performing CRUD operations with role-based authentications, and it uses Flask in Backend,
SQLite in Database & HTML CSS JS in Frontend.

##Frameworks Used
Backend – Python-Flask , flask_sqlalchemy, matplotlib
Database - SQLite
Frontend - HTML, CSS, JS
Jinja2 Render_template – for rendering HTML pages,
Redirect - redirecting, url_for - for HTML templates,
Request - to fetch data from forms/input fields,
Session - for login sessions

##API Design
CRUD: Implementation of all 3 tables - User, Services, ServiceRequest.
 With Role Based Authentication –
 Services – Create, Edit, Delete (Exclusive for Admin).
ServiceRequest - Customer/Professional
GET - Read, POST - Create, UPDATE, DELETE
