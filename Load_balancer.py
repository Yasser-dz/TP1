import boto3
import constant

class LoadBalancer:
    def __init__(self):
        self.elb = boto3.client('elbv2')
        self.load_balancer = None
        self.target_group_t2 = None
        self.target_group_m4 = None

    # Gets the subnet ids of the current deployment
    def get_subnet_id(self, availability_zone):
        ec2 = boto3.resource('ec2')
        subnets = list(ec2.subnets.all())
        return [x for x in subnets if x.availability_zone == availability_zone][0].id

    # Creates a load balancer with different availability zones
    def create_load_balancer(self):
        self.load_balancer = self.elb.create_load_balancer(
            Type=constant.APPLICATION_LOAD_BALANCER,
            Name='DefaultLoadBalancer',
            IpAddressType=constant.DEFAULT_IP_TYPE,
            Subnets=[
                self.get_subnet_id(constant.US_EAST_1A),
                self.get_subnet_id(constant.US_EAST_1B),
                self.get_subnet_id(constant.US_EAST_1C),
                self.get_subnet_id(constant.US_EAST_1D),
            ],
        )
        lb_address = self.load_balancer.get('LoadBalancers')[0].get('DNSName')
        print(lb_address)
        with open(constant.LB_ADDRESS_PATH, 'w') as f:
            f.write(lb_address)

    # Gets the vpc of the current deployment
    def get_vpc(self):
        ec2 = boto3.resource('ec2')
        vpcs = list(ec2.vpcs.all())
        return vpcs[0].id

    # Creates a target group that will be linked to a load balancer
    def create_target_group(self, target_type, name, protocol, port, vpc, protocol_version):
        return self.elb.create_target_group(
            TargetType=target_type,
            Name=name,
            Protocol=protocol,
            Port=port,
            VpcId=vpc,
            ProtocolVersion=protocol_version
        )

    # Creates both target groups that will be used by the load balancers
    def create_target_groups(self):
        self.target_group_t2 = self.create_target_group(
            target_type=constant.TG_TARGET_TYPE,
            name=constant.TG_NAME_T2,
            protocol=constant.TG_PROTOCOL,
            port=constant.DEFAULT_PORT,
            vpc=self.get_vpc(),
            protocol_version=constant.TG_PROTOCOL_VERSION,
        )

        self.target_group_m4 = self.create_target_group(
            target_type=constant.TG_TARGET_TYPE,
            name=constant.TG_NAME_M4,
            protocol=constant.TG_PROTOCOL,
            port=constant.DEFAULT_PORT,
            vpc=self.get_vpc(),
            protocol_version=constant.TG_PROTOCOL_VERSION
        )

    # Links a target group to a listener
    def register_target_group(self, listener, target_group, route, priority):
        self.elb.create_rule(
            ListenerArn=listener.get('Listeners')[0].get('ListenerArn'),
            Actions=[
                    {
                        'TargetGroupArn': target_group.get('TargetGroups')[0].get('TargetGroupArn'),
                        'Type': 'forward'
                    },
            ],
            Conditions=[
                {
                    'Field': constant.PATH_PATTERN_CONDITION,
                    'Values': [route]
                },
            ],
            Priority=priority
        )

    # Links the both target groups to a listener to forward the routes to the right load balancers
    def register_target_groups(self):
        listener = self.elb.create_listener(
            LoadBalancerArn=self.load_balancer.get('LoadBalancers')[0].get('LoadBalancerArn'),
            Port=constant.DEFAULT_PORT,
            Protocol=constant.DEFAULT_PROTOCOL,
            DefaultActions=[
                {
                    # default route is mandatory. '/' will be redirected to T2.large cluster.
                    'TargetGroupArn': self.target_group_t2.get('TargetGroups')[0].get('TargetGroupArn'),
                    'Type': constant.FORWARD_RULE,
                    'Order': 1
                }
            ]
        )

        # registering our custom routes
        self.register_target_group(listener, target_group=self.target_group_t2, route='/cluster1', priority=1)
        self.register_target_group(listener, target_group=self.target_group_m4, route='/cluster2', priority=2)

    # Registers a cluster to a target group
    def register_cluster(self, target_group, cluster_ids):
        self.elb.register_targets(
            TargetGroupArn=target_group.get('TargetGroups')[0].get('TargetGroupArn'),
            # All the instances
            Targets=
            [
                {
                    'Id': cluster_id,
                    'Port': constant.DEFAULT_PORT
                }
                for cluster_id in cluster_ids
            ]
        )
        
    # Cleanup

    def delete_load_balancer(self):
        self.elb.delete_load_balancer(LoadBalancerArn=self.load_balancer.get('LoadBalancers')[0].get('LoadBalancerArn'))

    def delete_target_groups(self):
        self.elb.delete_target_group(TargetGroupArn=self.target_group_t2.get('TargetGroups')[0].get('TargetGroupArn'))
        self.elb.delete_target_group(TargetGroupArn=self.target_group_m4.get('TargetGroups')[0].get('TargetGroupArn'))