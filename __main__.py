import pulumi
import pulumi_aws as aws

# Config: region is picked from AWS environment (already in GitHub Actions)
# We'll create a basic infra stack without requiring SSH keys or extra config

# 1️⃣ Create VPC
vpc = aws.ec2.Vpc(
    "pulumi-vpc",
    cidr_block="10.0.0.0/16",
    enable_dns_support=True,
    enable_dns_hostnames=True,
    tags={"Name": "pulumi-vpc"}
)

# 2️⃣ Create a public subnet
subnet = aws.ec2.Subnet(
    "pulumi-public-subnet",
    vpc_id=vpc.id,
    cidr_block="10.0.1.0/24",
    map_public_ip_on_launch=True,
    tags={"Name": "pulumi-public-subnet"}
)

# 3️⃣ Create Internet Gateway
igw = aws.ec2.InternetGateway("pulumi-igw", vpc_id=vpc.id)

# 4️⃣ Create a Route Table with default route
route_table = aws.ec2.RouteTable(
    "pulumi-rt",
    vpc_id=vpc.id,
    routes=[{"cidr_block": "0.0.0.0/0", "gateway_id": igw.id}],
)

# 5️⃣ Associate Route Table to Subnet
aws.ec2.RouteTableAssociation(
    "pulumi-rt-assoc",
    subnet_id=subnet.id,
    route_table_id=route_table.id,
)

# 6️⃣ Security Group allowing SSH & HTTP
sg = aws.ec2.SecurityGroup(
    "pulumi-sg",
    vpc_id=vpc.id,
    description="Allow SSH and HTTP access",
    ingress=[
        {"protocol": "tcp", "from_port": 22, "to_port": 22, "cidr_blocks": ["0.0.0.0/0"]},
        {"protocol": "tcp", "from_port": 80, "to_port": 80, "cidr_blocks": ["0.0.0.0/0"]}
    ],
    egress=[
        {"protocol": "-1", "from_port": 0, "to_port": 0, "cidr_blocks": ["0.0.0.0/0"]}
    ],
    tags={"Name": "pulumi-sg"}
)

# 7️⃣ Get latest Amazon Linux 2 AMI
ami = aws.ec2.get_ami(
    most_recent=True,
    owners=["amazon"],
    filters=[
        {"name": "name", "values": ["amzn2-ami-hvm-*-x86_64-gp2"]},
    ],
)

# 8️⃣ User data for simple web server
user_data = """#!/bin/bash
yum update -y
yum install -y httpd
systemctl enable httpd
systemctl start httpd
echo "Hello from Pulumi EC2 Instance!" > /var/www/html/index.html
"""

# 9️⃣ Launch EC2 Instance
instance = aws.ec2.Instance(
    "pulumi-ec2",
    instance_type="t2.micro",
    ami=ami.id,
    subnet_id=subnet.id,
    vpc_security_group_ids=[sg.id],
    associate_public_ip_address=True,
    user_data=user_data,
    tags={"Name": "pulumi-ec2"},
)

# 🔟 Outputs
pulumi.export("instance_public_ip", instance.public_ip)
pulumi.export("instance_public_dns", instance.public_dns)
