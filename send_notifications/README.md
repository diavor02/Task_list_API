<h2>Table of Contents</h2>
<ul>
  <li><a href="#overview">Overview</a></li>
  <li><a href="#features">Features</a></li>
  <li><a href="#deploying-to-aws-lambda">Deploying to AWS Lambda</a></li>
  <li><a href="#license">License</a></li>
</ul>

<br>
<h1>PART 2: SENDING NOTIFICATIONS TO USERS</h1>

<h2>Overview</h2>

<p>This project is part of a larger API system that allows users to store their tasks in a database and receive email notifications one day before the task deadline. This specific part of the project is responsible for sending the notifications. The system is designed to run as an AWS Lambda function, triggered by AWS EventBridge.</p>

<p>The notification system is built using Python and leverages the following technologies:</p>
<ul>
  <li><strong>FastAPI</strong>: For handling HTTP requests (though not directly used in this part).</li>
  <li><strong>SQLAlchemy</strong>: For ORM (Object-Relational Mapping) to interact with the PostgreSQL database.</li>
  <li><strong>psycopg2</strong>: For connecting to the PostgreSQL database.</li>
  <li><strong>smtplib</strong>: For sending email notifications via Gmail's SMTP server.</li>
  <li><strong>AWS Lambda</strong>: For serverless execution of the notification sending logic.</li>
  <li><strong>AWS EventBridge</strong>: For triggering the Lambda function at scheduled intervals.</li>
</ul>

<br>
<h2>Features</h2>
<ul>
  <li><strong>Task Management</strong>: Users can store tasks with descriptions and deadlines.</li>
  <li><strong>Email Notifications</strong>: Users receive email notifications one day before the task deadline.</li>
  <li><strong>Customizable Notifications</strong>: Users can opt-in or opt-out of notifications.</li>
  <li><strong>Scalable</strong>: The system is designed to run in a serverless environment, making it highly scalable.</li>
</ul>

<br>
<h2>Deploying to AWS Lambda</h2>
<ul>
  <li>AWS Lambda for serverless execution (the function was created using the Docker image</li>
  <li>EventBridge rule to trigger the Lambda function at the desired interval (e.g., daily).</li>
  <li>Docker container packaging</li>
</ul>

<br>
<h2>License</h2>
<p>This project is licensed under the MIT License - see the LICENSE file for details.</p>













