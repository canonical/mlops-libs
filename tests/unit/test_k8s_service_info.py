#!/usr/bin/env python3
# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

import pytest
from charms.mlops_libs.v0.k8s_service_info import (
    KubernetesServiceInfoObject,
    KubernetesServiceInfoProvider,
    KubernetesServiceInfoProviderWrapper,
    KubernetesServiceInfoRelationDataMissingError,
    KubernetesServiceInfoRelationMissingError,
    KubernetesServiceInfoRequirer,
)
from ops.charm import CharmBase
from ops.model import TooManyRelatedAppsError
from ops.testing import Harness

TEST_RELATION_NAME = "test-relation"
REQUIRER_CHARM_META = f"""
name: requirer-test-charm
requires:
  {TEST_RELATION_NAME}:
    interface: test-interface
"""
PROVIDER_CHARM_META = f"""
name: provider-test-charm
provides:
  {TEST_RELATION_NAME}:
    interface: test-interface
"""


class GenericCharm(CharmBase):
    pass


@pytest.fixture()
def requirer_charm_harness():
    return Harness(GenericCharm, meta=REQUIRER_CHARM_META)


@pytest.fixture()
def provider_charm_harness():
    return Harness(GenericCharm, meta=PROVIDER_CHARM_META)


def test_get_data_passes(requirer_charm_harness):
    """Assert the relation data is as expected."""
    # Initial configuration
    requirer_charm_harness.set_model_name("test-model")
    requirer_charm_harness.set_leader(True)
    requirer_charm_harness.begin()

    # Add and update relation
    data_dict = {"svc_name": "some-service", "svc_port": "7878"}
    requirer_charm_harness.add_relation(TEST_RELATION_NAME, "app", app_data=data_dict)

    # Instantiate KubernetesServiceInfoRequirer class
    requirer_charm_harness.charm._k8s_svc_info_requirer = KubernetesServiceInfoRequirer(
        requirer_charm_harness.charm, relation_name=TEST_RELATION_NAME
    )

    # Get the relation data
    expected_data = KubernetesServiceInfoObject(
        name=data_dict["svc_name"], port=data_dict["svc_port"]
    )
    actual_relation_data = requirer_charm_harness.charm._k8s_svc_info_requirer.get_data()

    # Assert returns dictionary with expected values
    assert actual_relation_data.name == expected_data.name
    assert actual_relation_data.port == expected_data.port


def test_check_raise_too_many_relations(requirer_charm_harness):
    """Assert that TooManyRelatedAppsError is raised if more than one application is related."""
    requirer_charm_harness.set_model_name("test-model")
    requirer_charm_harness.begin()
    requirer_charm_harness.set_leader(True)

    # Instantiate KubernetesServiceInfoRequirer class
    requirer_charm_harness.charm._k8s_svc_info_requirer = KubernetesServiceInfoRequirer(
        requirer_charm_harness.charm, relation_name=TEST_RELATION_NAME
    )

    requirer_charm_harness.add_relation(TEST_RELATION_NAME, "app")
    requirer_charm_harness.add_relation(TEST_RELATION_NAME, "app2")

    with pytest.raises(TooManyRelatedAppsError):
        requirer_charm_harness.charm._k8s_svc_info_requirer.get_data()


def test_validate_relation_raise_no_relation(requirer_charm_harness):
    """Assert that  KubernetesServiceInfoRelationMissingError is raised in the absence of the relation."""
    requirer_charm_harness.set_model_name("test-model")
    requirer_charm_harness.begin()
    requirer_charm_harness.set_leader(True)

    # Instantiate KubernetesServiceInfoRequirer class
    requirer_charm_harness.charm._k8s_svc_info_requirer = KubernetesServiceInfoRequirer(
        requirer_charm_harness.charm, relation_name=TEST_RELATION_NAME
    )

    with pytest.raises(KubernetesServiceInfoRelationMissingError):
        requirer_charm_harness.charm._k8s_svc_info_requirer.get_data()


def test_validate_relation_raise_no_relation_data(requirer_charm_harness):
    """Assert that KubernetesServiceInfoRelationDataMissingError is raised in the absence of relation data."""
    requirer_charm_harness.set_model_name("test-model")
    requirer_charm_harness.begin()
    requirer_charm_harness.set_leader(True)

    # Instantiate KubernetesServiceInfoRequirer class
    requirer_charm_harness.charm._k8s_svc_info_requirer = KubernetesServiceInfoRequirer(
        requirer_charm_harness.charm, relation_name=TEST_RELATION_NAME
    )

    requirer_charm_harness.add_relation(TEST_RELATION_NAME, "app")

    with pytest.raises(KubernetesServiceInfoRelationDataMissingError) as error:
        requirer_charm_harness.charm._k8s_svc_info_requirer.get_data()
    assert str(error.value) == f"No data found in relation {TEST_RELATION_NAME} data bag."


def test_validate_relation_raises_data_missing_attribute(requirer_charm_harness):
    """Assert KubernetesServiceInfoRelationDataMissingError is raised in the absence of a relation data attribute."""
    # Initial configuration
    requirer_charm_harness.set_model_name("test-model")
    requirer_charm_harness.begin()
    requirer_charm_harness.set_leader(True)

    # Instantiate KubernetesServiceInfoRequirer class
    requirer_charm_harness.charm._k8s_svc_info_requirer = KubernetesServiceInfoRequirer(
        requirer_charm_harness.charm, relation_name=TEST_RELATION_NAME
    )

    # Add and update relation
    faulty_relation_data = {"svc_name": "name"}
    requirer_charm_harness.add_relation(TEST_RELATION_NAME, "app", app_data=faulty_relation_data)

    with pytest.raises(KubernetesServiceInfoRelationDataMissingError) as error:
        requirer_charm_harness.charm._k8s_svc_info_requirer.get_data()
    assert str(error.value) == f"Missing attributes: ['svc_port'] in relation {TEST_RELATION_NAME}"


def test_provider_sends_data_automatically_passes(provider_charm_harness):
    """Assert the relation data is passed automatically by the provider."""
    provider_charm_harness.set_model_name("test-model")
    provider_charm_harness.set_leader(True)
    provider_charm_harness.begin()

    # Instantiate the KubernetesServiceInfoProvider
    svc_name = "some-svc"
    svc_port = "7878"
    provider_charm_harness.charm._k8s_svc_info_provider = KubernetesServiceInfoProvider(
        charm=provider_charm_harness.charm,
        svc_name=svc_name,
        svc_port=svc_port,
        relation_name=TEST_RELATION_NAME,
    )

    # Add corresponding relation
    provider_charm_harness.add_relation(TEST_RELATION_NAME, "app")

    # Check the relation data
    relations = provider_charm_harness.model.relations[TEST_RELATION_NAME]
    for relation in relations:
        actual_relation_data = relation.data[provider_charm_harness.charm.app]
        # Assert returns dictionary with expected values
        assert actual_relation_data.get("svc_name") == svc_name
        assert actual_relation_data.get("svc_port") == svc_port


def test_provider_wrapper_send_data_passes(provider_charm_harness):
    """Assert the relation data is as expected by the provider wrapper."""
    # Initial configuration
    provider_charm_harness.set_model_name("test-model")
    provider_charm_harness.begin()
    provider_charm_harness.set_leader(True)
    provider_charm_harness.add_relation(TEST_RELATION_NAME, "app")

    # Instantiate KubernetesServiceInfoProviderWrapper class
    provider_charm_harness.charm._k8s_svc_info_provider = KubernetesServiceInfoProviderWrapper(
        provider_charm_harness.charm,
        relation_name=TEST_RELATION_NAME,
    )

    # Send relation data
    relation_data = KubernetesServiceInfoObject(name="some-service", port="7878")
    provider_charm_harness.charm._k8s_svc_info_provider.send_data(
        svc_name=relation_data.name, svc_port=relation_data.port
    )
    relations = provider_charm_harness.model.relations[TEST_RELATION_NAME]
    for relation in relations:
        actual_relation_data = relation.data[provider_charm_harness.charm.app]
        # Assert returns dictionary with expected values
        assert actual_relation_data.get("svc_name") == relation_data.name
        assert actual_relation_data.get("svc_port") == relation_data.port
