import os
from operator import itemgetter

import pytest

from localstack.services.cloudformation.v2.utils import is_v2_engine
from localstack.testing.aws.util import is_aws_cloud
from localstack.testing.pytest import markers

pytestmark = pytest.mark.skipif(
    condition=not is_v2_engine() and not is_aws_cloud(),
    reason="Only targeting the new engine",
)


@pytest.mark.skip(reason="flaky")
@markers.aws.validated
@markers.snapshot.skip_snapshot_verify(
    paths=[
        "$..ClusterConfig.DedicatedMasterCount",  # added in LS
        "$..ClusterConfig.DedicatedMasterEnabled",  # added in LS
        "$..ClusterConfig.DedicatedMasterType",  # added in LS
        "$..SoftwareUpdateOptions",  # missing
        "$..OffPeakWindowOptions",  # missing
        "$..ChangeProgressDetails",  # missing
        "$..AutoTuneOptions.UseOffPeakWindow",  # missing
        "$..ClusterConfig.MultiAZWithStandbyEnabled",  # missing
        "$..AdvancedSecurityOptions.AnonymousAuthEnabled",  # missing
        # TODO different values:
        "$..Processing",
        "$..ServiceSoftwareOptions.CurrentVersion",
        "$..ClusterConfig.DedicatedMasterEnabled",
        "$..ClusterConfig.InstanceType",  # TODO the type was set in cfn
        "$..AutoTuneOptions.State",
        '$..AdvancedOptions."rest.action.multi.allow_explicit_index"',  # TODO this was set to false in cfn
    ]
)
def test_domain(deploy_cfn_template, aws_client, snapshot):
    snapshot.add_transformer(snapshot.transform.key_value("DomainId"))
    snapshot.add_transformer(snapshot.transform.key_value("DomainName"))
    snapshot.add_transformer(snapshot.transform.key_value("ChangeId"))
    snapshot.add_transformer(snapshot.transform.key_value("Endpoint"), priority=-1)
    template_path = os.path.join(
        os.path.dirname(__file__), "../../../../../templates/opensearch_domain.yml"
    )
    result = deploy_cfn_template(template_path=template_path)
    domain_endpoint = result.outputs["SearchDomainEndpoint"]
    assert domain_endpoint
    domain_arn = result.outputs["SearchDomainArn"]
    assert domain_arn
    domain_name = result.outputs["SearchDomain"]

    domain = aws_client.opensearch.describe_domain(DomainName=domain_name)
    assert domain["DomainStatus"]
    snapshot.match("describe_domain", domain)

    assert domain_arn == domain["DomainStatus"]["ARN"]
    tags_result = aws_client.opensearch.list_tags(ARN=domain_arn)
    tags_result["TagList"].sort(key=itemgetter("Key"))
    snapshot.match("list_tags", tags_result)


@markers.aws.validated
@markers.snapshot.skip_snapshot_verify(
    paths=[
        "$..DomainStatus.AIMLOptions",
        "$..DomainStatus.AdvancedSecurityOptions.AnonymousAuthEnabled",
        "$..DomainStatus.AutoTuneOptions.State",
        "$..DomainStatus.AutoTuneOptions.UseOffPeakWindow",
        "$..DomainStatus.ChangeProgressDetails",
        "$..DomainStatus.ClusterConfig.MultiAZWithStandbyEnabled",
        "$..DomainStatus.ClusterConfig.ZoneAwarenessConfig",
        "$..DomainStatus.DomainEndpointOptions.TLSSecurityPolicy",
        "$..DomainStatus.IPAddressType",
        "$..DomainStatus.IdentityCenterOptions",
        "$..DomainStatus.ModifyingProperties",
        "$..DomainStatus.OffPeakWindowOptions",
        "$..DomainStatus.ServiceSoftwareOptions.CurrentVersion",
        "$..DomainStatus.SoftwareUpdateOptions",
    ]
)
def test_domain_with_alternative_types(deploy_cfn_template, aws_client, snapshot):
    """
    Test that the alternative types for the OpenSearch domain are accepted using the resource documentation example
    """
    snapshot.add_transformer(snapshot.transform.key_value("Endpoint"))
    stack = deploy_cfn_template(
        template_path=os.path.join(
            os.path.dirname(__file__),
            "../../../../../templates/opensearch_domain_alternative_types.yml",
        )
    )
    domain_name = stack.outputs["SearchDomain"]
    domain = aws_client.opensearch.describe_domain(DomainName=domain_name)
    snapshot.match("describe_domain", domain)
