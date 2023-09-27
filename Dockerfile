FROM python:3.10.0


# Install required python dependency
RUN pip install requests==2.27.1

# Copy send request script into Docker container
COPY send_requests.py send_requests.py

# Copy constants into Docker container
COPY constant.py constant.py

# Copy load balancer address file into Docker container
COPY lb_address.txt lb_address.txt


# Run script to send requests to instances
CMD [ "python",  "./send_requests.py" ]