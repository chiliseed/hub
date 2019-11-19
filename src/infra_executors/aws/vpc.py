import boto3

client = boto3.client("ec2")


def create_vpc(cidr_block="10.0.0.0/16"):
    """Create vpc with the provided ipv4 cidr block.

    https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Subnets.html

    Parameters
    ----------
    cidr_block : str
        range of ipv4 addresses for the VPC

    Returns
    -------
    str
        id of the vpc
    """
    params = dict(
        CidrBlock=cidr_block,
        AmazonProvidedIpv6CidrBlock=False,
        DryRun=True,
        InstanceTenancy="default",
    )
    resp = client.create_vpc(**params)
    print(resp)
    params['DryRun'] = False
    resp = client.create_vpc(**params)
    return resp['Vpc']['VpcId']
