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
<h2>Prerequisites</h2>
<h4>1. Set Up Database (for this project I used a PostgreSQL database, but any SQL database compatible with AWS would do)</h4>
<ul>
  <li>Ensure your PostgreSQL database is running and accessible.</li>
  <li>Update the <code>DATABASE_URL</code> in <code>notifications.py</code> with your database credentials.</li>
</ul>
<h4>2. Set Up Gmail Account</h4>
<ul>
  <li>Update the <code>email_sender</code> and <code>email_password</code> in <code>notifications.py</code> with your Gmail credentials.</li>
  <li>Use an App Password if 2 Factor Authentification is enabled.</li>
</ul>
<h4>3. AWS Lambda Configuration</h4>
<ul>
  <li>Ensure your Lambda function has the necessary permissions to access the database and send emails.</li>
</ul>
<h4>4. Install Docker Desktop</h4>
<ul>
  <li>You need a running Docker Engine in order to build a Docker Image.</li>
</ul>

<br>
<h2>Deploying to AWS Lambda</h2>
<ul>
  <li>1. Build the Docker Image: <code>docker build -t task-notification-lambda .</code> (make sure <code>notifications.py</code>, <code>requirements.txt</code> and the <code>Dockerfile</code> are in the same directory).</li>
  <li>2. Push the Docker image to Amazon ECR.</li>
  <li>3. Create a new Lambda function using the Docker image.</li>
  <li>4. Set up an EventBridge rule to trigger the Lambda function at the desired interval (e.g., daily).</li>
</ul>

<h2>License</h2>
<p>This project is licensed under the MIT License - see the LICENSE file for details.</p>













