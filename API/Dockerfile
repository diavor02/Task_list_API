FROM public.ecr.aws/lambda/python:3.9

COPY requirements.txt .

RUN pip install -r requirements.txt --target /var/task/

COPY . .

CMD [ "api2.handler" ]