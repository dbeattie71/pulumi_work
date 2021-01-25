"""An AWS Python Pulumi program"""

import pulumi
import network
import database

name_base = "mitch"
# Create an AWS VPC and subnets, etc
network = network.Vpc(name_base, network.VpcArgs())
#pulumi.export('network', network)

# Create RDS instance
db = database.Rds(name_base, database.RdsArgs(
  db_name="mitchdb",
  username="mitchadmin",
  password="mitchpasswordrds",
  subnets=network.subnets,
  security_group_ids=[network.rds_security_group.id]
))
pulumi.export('rds address', db.rds.address)