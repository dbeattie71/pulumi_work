from pulumi import ComponentResource, ResourceOptions
from pulumi_aws import rds

class RdsArgs:

    def __init__(self,
                db_name=None,
                username=None,
                password=None,
                subnets=None,
                security_group_ids=None,
                allocated_storage=20,
                engine="mysql",
                engine_version="5.7",
                instance_class="db.t2.micro",
                storage_type="gp2"):
        self.db_name = db_name
        self.username = username
        self.password = password
        self.subnets = subnets
        self.security_group_ids = security_group_ids
        self.allocated_storage = allocated_storage
        self.engine = engine
        self.engine_version = engine_version
        self.instance_class = instance_class
        self.storage_type = storage_type

class Rds(ComponentResource):

    def __init__(self,
                 name: str,
                 args: RdsArgs,
                 opts: ResourceOptions = None):

        super().__init__("custom:resource:RDS", name, {}, opts)

        # Create RDS subnet group to put RDS instance on.
        subnet_group_name = f'{name}-sng'
        subnet_ids = []
        for subnet in args.subnets:
            subnet_ids.append(subnet.id)

        rds_subnet_group = rds.SubnetGroup(subnet_group_name,
            subnet_ids = subnet_ids,
            tags={
                "Name": subnet_group_name
            },
            opts=ResourceOptions(parent=self)
        )

        rds_name = f'{name}-rds'
        self.rds = rds.Instance(rds_name,
            name = args.db_name,
            allocated_storage = args.allocated_storage,
            engine = args.engine,
            engine_version = args.engine_version,
            instance_class = args.instance_class,
            storage_type = args.storage_type,
            db_subnet_group_name = rds_subnet_group.id,
            username = args.username,
            password = args.password,
            vpc_security_group_ids = args.security_group_ids,
            skip_final_snapshot = True,
            opts=ResourceOptions(parent=self)
        )

        self.register_outputs({})