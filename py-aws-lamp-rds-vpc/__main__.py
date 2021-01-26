"""
Deploys:
- Network: VPC, Subnets, Security Groups
- DB Backend: MySQL RDS
- FrontEnd: WP in Fargate
"""

import pulumi
import network
import database
import frontend

# Get config data
config = pulumi.Config()
project = config.get("project") or "wp-demo"
db_name = config.require("db_name")
db_user = config.require("db_user")
db_password = config.require_secret("db_password")

name_base = "mitch"
# Create an AWS VPC and subnets, etc
network = network.Vpc(name_base, network.VpcArgs())
subnet_ids = []
for subnet in network.subnets:
    subnet_ids.append(subnet.id)
# pulumi.export('network', network)

# Create RDS instance
db = database.Rds(name_base, database.RdsArgs(
    db_name=db_name,
    db_user=db_user,
    db_password=db_password,
    publicly_accessible=True,
    subnet_ids=subnet_ids,
    security_group_ids=[network.rds_security_group.id]
))
pulumi.export('rds ', db.rds.address)

#fe = Output.all(db.rds.address, db.rds.name, db.rds.username, db.rds.passwordsql_server.name, database.name) \
# .apply(lambda args: f"Server=tcp:{args[0]}.database.windows.net;initial catalog={args[1]}...")
fe = frontend.WebService(name_base, frontend.WebServiceArgs(
    db_host=db.rds.address,
    db_port="3306",
    db_name=db.rds.name,
    db_user=db.rds.username,
    db_password=db.rds.password,
    vpc_id=network.vpc.id,
    subnet_ids=subnet_ids,
    security_group_ids=[network.fe_security_group.id]
))
pulumi.export('fe', fe.alb.dns_name)
