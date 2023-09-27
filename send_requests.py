import constant
import requests
import time
import threading
import socket
import logging



def send_GET_request(url):
    """ Send GET request to specified url. """

    try:
        response = requests.get(url)
    except socket.gaierror:
        logging.info("Failed to establish a new connection: [Errno -2] Name or service not known")
    


def run_test_scenario_1(url_cluster_1, url_cluster_2):
    """ Send 1000 requests to cluster 1 and cluster 2. """

    logging.info("Thread 1 start")

    for _ in range(1000):
        send_GET_request(url_cluster_1)
        send_GET_request(url_cluster_2)

    logging.info("Thread 1 end")   


def run_test_scenario_2(url_cluster_1, url_cluster_2):
    """ Send 500 requests to cluster 1 and cluster 2 followed by another 1000 requests. """

    logging.info("Thread 2 start")
    for _ in range(500):
        send_GET_request(url_cluster_1)
        send_GET_request(url_cluster_2)

    logging.info("Thread 2: 60 sec timeout")
    time.sleep(60)

    for _ in range(1000):
        send_GET_request(url_cluster_1)
        send_GET_request(url_cluster_2)

    logging.info("Thread 2 end")


if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)

    # Fetch ELB dns address
    elb_dns = open(constant.LB_ADDRESS_PATH).readline()
    url_cluster_1 = f'http://{elb_dns}/cluster1'
    url_cluster_2 = f'http://{elb_dns}/cluster2'

    thread_1 = threading.Thread(target=run_test_scenario_1, args=(url_cluster_1, url_cluster_2))
    thread_2 = threading.Thread(target=run_test_scenario_2, args=(url_cluster_1, url_cluster_2))

    # Start threads
    thread_1.start()
    thread_2.start()

    # Wait for threads to terminate
    thread_1.join()
    thread_2.join()