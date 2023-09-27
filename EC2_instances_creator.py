import boto3
import constant
import time


class EC2Creator:
    def __init__(self):
        self.client = boto3.client('ec2')
        self.open_http_port()
        self.cluster_t2_instances_ids = []
        self.cluster_m4_instances_ids = []

    # Runs a request to create an instance from parameters and saves their ids
    def create_instance(self, availability_zone, instance_type):
        response = self.client.run_instances(
            BlockDeviceMappings=[
                {
                    'DeviceName': '/dev/sda1',
                    'Ebs': {
                        # deleting the storage on instance termination
                        'DeleteOnTermination': True,

                        # 8gb volume
                        'VolumeSize': 8,

                        # Volume type
                        'VolumeType': 'gp2',
                    },
                },
            ],

            # UBUNTU instance
            ImageId=constant.UBUNTU_IMAGE,

            # UBUNTU instance
            InstanceType=instance_type,

            # Availability zone
            Placement={
                'AvailabilityZone': availability_zone,
            },

            DisableApiTermination=False,

            # One instance
            MaxCount=1,
            MinCount=1,

            # Script to launch on instance startup
            UserData=open('launch_script.sh').read()
        )
        print(response["Instances"][0]["InstanceId"])
        time.sleep(5)
        return response["Instances"][0]["InstanceId"]

    # Sequence of requests that creates the 4 t2 instances and saves their ids
    def create_cluster_t2_large(self):
        self.cluster_t2_instances_ids = [
            self.create_instance(constant.US_EAST_1A, constant.T2_LARGE),
            self.create_instance(constant.US_EAST_1B, constant.T2_LARGE),
            self.create_instance(constant.US_EAST_1C, constant.T2_LARGE),
            self.create_instance(constant.US_EAST_1D, constant.T2_LARGE)
        ]

    # Sequence of requests that creates the 5 m4 instances
    def create_cluster_m4_large(self):
        self.cluster_m4_instances_ids = [
            self.create_instance(constant.US_EAST_1A, constant.M4_LARGE),
            self.create_instance(constant.US_EAST_1B, constant.M4_LARGE),
            self.create_instance(constant.US_EAST_1C, constant.M4_LARGE),
            self.create_instance(constant.US_EAST_1D, constant.M4_LARGE),
            self.create_instance(constant.US_EAST_1E, constant.M4_LARGE)
        ]

    # Main function that creates all the instances and retrieves their ids
    def create_clusters(self):
        self.create_cluster_t2_large()
        time.sleep(20)
        self.create_cluster_m4_large()

        return (
            self.cluster_t2_instances_ids,
            self.cluster_m4_instances_ids
        )

    # Termination function that terminates the running instances
    def terminate_instances(self):
        self.client.terminate_instances(InstanceIds=self.cluster_t2_instances_ids)
        self.client.terminate_instances(InstanceIds=self.cluster_m4_instances_ids)

    # If not done already, opens the port 80 on the default security group so that
    #  the ports of all instances and load balancers are exposed by default on creation
    def open_http_port(self):
        # Gets all open ports on the default group
        opened_ports = [i_protocol.get('FromPort') for i_protocol in
                        self.client.describe_security_groups(GroupNames=[constant.DEFAULT_SECURITY_GROUP_NAME])
                        ['SecurityGroups'][0]['IpPermissions']]
        if constant.HTTP_PORT not in opened_ports:
            self.client.authorize_security_group_ingress(
                GroupName=constant.DEFAULT_SECURITY_GROUP_NAME,
                CidrIp=constant.CIDR_IP,
                FromPort=constant.HTTP_PORT,
                ToPort=constant.HTTP_PORT,
                IpProtocol=constant.IP_PROTOCOL
            )