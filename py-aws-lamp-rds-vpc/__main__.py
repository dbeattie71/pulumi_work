"""
Deploys:
- Network: VPC, Subnets, Security Groups
- DB Backend: MySQL RDS
- FrontEnd: WP in Fargate
"""

import pulumi
import pulumi_random as random
import network
import database
import frontend

# Get config data
config = pulumi.Config()
service_name = config.get("service_name") or "lamp-demo"
db_name = config.get("db_name") or "lampdb"
db_user = config.get("db_user") or "admin"
db_password = config.get_secret("db_password") or "__makeapassword__"
if db_password == "__makeapassword__":
    password = random.RandomPassword("password",
        length=16,
        special=True,
        override_special="_%@",
        )
    db_password = password.result

# Create an AWS VPC and subnets, etc
network = network.Vpc(service_name, network.VpcArgs())
subnet_ids = []
for subnet in network.subnets:
    subnet_ids.append(subnet.id)

# Create RDS instance
db = database.Rds(service_name, database.RdsArgs(
    db_name=db_name,
    db_user=db_user,
    db_password=db_password,
    publicly_accessible=True,
    subnet_ids=subnet_ids,
    security_group_ids=[network.rds_security_group.id]
))

fe = frontend.WebService(service_name, frontend.WebServiceArgs(
    db_host=db.rds.address,
    db_port="3306",
    db_name=db.rds.name,
    db_user=db.rds.username,
    db_password=db.rds.password,
    vpc_id=network.vpc.id,
    subnet_ids=subnet_ids,
    security_group_ids=[network.fe_security_group.id]
))

web_url = pulumi.Output.concat("http://", fe.alb.dns_name)
pulumi.export("Web Service URL", web_url)

pulumi.export('DB Endpoint', db.rds.address)
pulumi.export('DB User Name', db.rds.username)
pulumi.export('DB Password', db.rds.password)