# EC2
UBUNTU_IMAGE = "ami-08c40ec9ead489470"
US_EAST_1A = "us-east-1a"
US_EAST_1B = "us-east-1b"
US_EAST_1C = "us-east-1c"
US_EAST_1D = "us-east-1d"
US_EAST_1E = "us-east-1e"

T2_LARGE = "t2.large"
M4_LARGE = "m4.large"

APPLICATION_LOAD_BALANCER="application"

DEFAULT_IP_TYPE = "ipv4"

DEFAULT_PORT = 80
DEFAULT_PROTOCOL = 'HTTP'

# Target Group
TG_TARGET_TYPE = "instance"
TG_NAME_T2 = "TargetGroupT2"
TG_NAME_M4 = "TargetGroupM4"
TG_PROTOCOL = "HTTP"
TG_PROTOCOL_VERSION = "HTTP1"

# Target groups Rules
FORWARD_RULE = "forward"
PATH_PATTERN_CONDITION = 'path-pattern'

# Load balancer 
LB_NAME = "DefaultLoadBalancer"
LB_ADDRESS_PATH = "lb_address.txt"  # dns address save location

# Port configuration
DEFAULT_SECURITY_GROUP_NAME = "default"
CIDR_IP = "0.0.0.0/0"
HTTP_PORT = 80
IP_PROTOCOL = "tcp"