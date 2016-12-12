# -*- coding: utf-8 -*-
"""
TwinDB Amazon infrastructure
"""
import logging
import boto3
from botocore.exceptions import ClientError
import click
from twindb_infrastructure.clogging import setup_logging
from twindb_infrastructure.config.config import TWINDB_INFRA_CONFIG, Config, \
    ConfigException
from twindb_infrastructure.tagset import TagSet
from twindb_infrastructure.util import printf


class TwinDBInfraException(Exception):
    pass


log = logging.getLogger(__name__)
CONFIG = None
AWS_REGIONS = [
    'us-east-1',
    'us-east-2',
    'us-west-1',
    'us-west-2',
    'ap-northeast-2',
    'ap-southeast-1',
    'ap-southeast-2',
    'ap-northeast-1',
    'eu-central-1',
    'eu-west-1'
]


def parse_config(path):
    """Parse TwinDB Infrastructure config

    :param path: path to config file
    :raise ConfigException if config can't be parsed
    """
    return Config(path)


@click.group()
@click.option('--config', default=TWINDB_INFRA_CONFIG,
              help='Config file',
              show_default=True,
              type=click.Path(exists=True))
@click.option('--debug', is_flag=True, default=False,
              help='Print debug messages')
def main(config, debug):
    """
    Console script to work with TwinDB Amazon Infrastructure
    """
    global CONFIG

    setup_logging(log, debug=debug)
    log.debug('Using config %s' % config)
    try:
        CONFIG = parse_config(config)
    except ConfigException as err:  # pragma: no cover
        log.error(err)
        exit(-1)


@main.command()
@click.option('--tags', is_flag=True, help='Show instance tags')
@click.option('--verbose', is_flag=True,
              help='Show more details about the instance')
@click.option('--region', type=click.Choice(AWS_REGIONS), help='AWS region name')
@click.argument('tags-filter', nargs=-1)
def show(tags, verbose, region, tags_filter):
    """List TwinDB servers"""

    if region:
        region_name = region
    else:
        region_name = CONFIG.aws.aws_default_region

    client = boto3.client('ec2', region_name=region_name)
    response = client.describe_instances()
    log.debug('response = %r' % response)
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            if tags_filter \
                    and \
                    not TagSet(tags_filter).issubset(TagSet(instance['Tags'])):
                continue

            printf('%s' % instance['InstanceId'])
            if verbose:
                printf(' State: %s,' % instance['State']['Name'])
                try:
                    printf(' PublicIP: %s,' % instance['PublicIpAddress'])
                except KeyError:
                    pass
                try:
                    printf(' PrivateIP: %s,' % instance['PrivateIpAddress'])
                except KeyError:
                    pass
                printf(' AvailabilityZone: %s'
                       % instance['Placement']['AvailabilityZone'])

            if tags:
                printf(': Tags: ')
                try:
                    printf('%s\n', TagSet(instance['Tags']))
                except KeyError:
                    printf("None\n")
                    pass
            else:
                printf("\n")


@main.command()
@click.argument('instance-id')
def terminate(instance_id):
    """Terminate Amazon instance"""

    try:
        ec2 = boto3.resource('ec2')
        ec2.instances.filter(InstanceIds=[instance_id]).terminate()

    except ClientError as err:
        log.error(err)


@main.command()
@click.argument('instance-id')
def stop(instance_id):
    """Stop Amazon instance"""

    try:
        ec2 = boto3.resource('ec2')
        ec2.instances.filter(InstanceIds=[instance_id]).stop()

    except ClientError as err:
        log.error(err)


@main.command()
@click.argument('instance-id')
def start(instance_id):
    """Start Amazon instance"""

    try:
        ec2 = boto3.resource('ec2')
        ec2.instances.filter(InstanceIds=[instance_id]).start()

    except ClientError as err:
        log.error(err)


@main.command()
@click.argument('instance-id')
def launch(instance_id):
    """Launch new Amazon instance"""

    try:
        ec2 = boto3.resource('ec2')
        ec2.instances.filter(InstanceIds=[instance_id]).start()

    except ClientError as err:
        log.error(err)
