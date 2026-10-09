# **_Student Database — Flask CRUD Project_**

Hello, I'm Srikrishna and the project I built is a Student Database Management System using Flask.

The core idea of this project is to create a simple web application for managing student records.
It allows us to store student details such as name, roll number, age, department, and email, and perform the four basic CRUD operations: Create, Read, Update, and Delete.

The project is built to understand how Flask works with a database and how a complete web application handles data from the frontend to the database.

# **_Steps involved in building the project:_**

1) Created a Flask project and set up a virtual environment.
2) Installed Flask and Flask-SQLAlchemy.
3) First tested Flask with a simple Hello World application.
4) Connected Flask with an SQL database.
5) Created a Student table with Name, Roll No, Age, Department, and Email.
6) Created HTML templates for displaying and entering student data. [CRUD Operations]
7) Implemented the Create operation to add new students.
8) Implemented the Read operation to display all students.
9) Implemented the Update operation to edit student details.
10) Implemented the Delete operation to remove student records.
11) Tested all CRUD operations to make sure the application was working correctly.
12) Installed Flask-Login and made a User table for storing login details.
13) Made Register, Login and Logout pages. Passwords are saved as hashes, not plain text.
14) Added login_required to the student pages so a user has to log in first.
15) Made two roles, admin and staff. Only the admin can delete students. The first user who registers becomes the admin.
16) Added validation to the add and edit forms (age range, email format, duplicate roll number). If there is an error, the form keeps what was typed.
17) Made error pages for 403 and 404.
18) Added a search box and a department filter on the home page.
19) Added sorting by clicking the column headings.
20) Added pagination, 10 students per page.
21) Added some test students to check search, sorting and paging.
# **_Result:_**
The project started as a simple CRUD app. It now also has login with admin and staff roles, form validation, and a student list with search, filter, sorting and pagination.