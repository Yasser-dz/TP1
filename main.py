from EC2_instances_creator import EC2Creator
from Load_balancer import LoadBalancer
from metric_generator import MetricGenerator
import time
import os

ec2 = EC2Creator()
LB = LoadBalancer()

print('Creating clusters...')
t2_cluster, m4_cluster = ec2.create_clusters()
print('Clusters created!')

print("Waiting 60 seconds before creating load balancer...")
time.sleep(60)

# create load balancer
print('Creating load balancer...')
LB.create_load_balancer()
print("load balancer created!")

# create target groups
print('Creating target groups...')
LB.create_target_groups()
print('Target groups created!')

# register targets
print('Registering Instances to target groups...')
LB.register_cluster(LB.target_group_t2, t2_cluster)
LB.register_cluster(LB.target_group_m4, m4_cluster)
print('Instances registration complete!')

print('Registering target groups to load balancer...')
LB.register_target_groups()
print('Target groups registration complete!')

print('Waiting 240 seconds before sending GET requests..')
time.sleep(240)

# Send GET requests to EC2 instances
print("Sending get requests to instances...")
os.system("docker build -t tp1/send_requests .")
print("Running Docker container...")
os.system("docker run tp1/send_requests:latest")
print("Requests sent")

print("Waiting 60 seconds for collection of CloudWatch metrics...")
time.sleep(60)


# Generate metric plots
metricGenerator = MetricGenerator(
        elb_id = LB.load_balancer.get('LoadBalancers')[0].get('LoadBalancerArn').split("/", 1)[1],
        cluster_t2_id=LB.target_group_t2.get('TargetGroups')[0].get('TargetGroupArn').split(":")[-1],
        cluster_m4_id=LB.target_group_m4.get('TargetGroups')[0].get('TargetGroupArn').split(":")[-1],
        cluster_t2_instances_ids=ec2.cluster_t2_instances_ids,
        cluster_m4_instances_ids=ec2.cluster_m4_instances_ids
    )

metricGenerator.prepare_results()


# Terminate services
ec2.terminate_instances()
LB.delete_load_balancer()
time.sleep(30)
LB.delete_target_groups()