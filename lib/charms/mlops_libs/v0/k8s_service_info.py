#!/usr/bin/env python3
# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Library for sharing Kubernetes Services information.

This library offers a Python API for providing and requesting information about
any Kubernetes Service resource.
The default relation name is `k8s-svc-info` and it's recommended to use that name,
though if changed, you must ensure to pass the correct name when instantiating the
provider and requirer classes, as well as in `metadata.yaml`.

## Getting Started

### Fetching the library with charmcraft

Using charmcraft you can:
```shell
charmcraft fetch-lib charms.<pending>.v0.k8s_service_info
```

## Using the library as requirer

### Add relation to metadata.yaml
```yaml
requires:
  k8s-svc-info:
    interface: k8s-service
    limit: 1
```

### Instantiate the KubernetesServiceInfoRequirer class in charm.py

```python
from ops.charm import CharmBase
from charms.<pending>.v0.kubernetes_service_info import KubernetesServiceInfoRequirer, KubernetesServiceInfoRelationError

class RequirerCharm(CharmBase):
    def __init__(self, *args):
        self._k8s_svc_info_requirer = KubernetesServiceInfoRequirer(self)
        self.framework.observe(self.on.some_event_emitted, self.some_event_function)

    def some_event_function():
        # use the getter function wherever the info is needed
        try:
            k8s_svc_info_data = self._k8s_svc_info_requirer.get_k8s_svc_info()
        except KubernetesServiceInfoRelationError as error:
            "your error handler goes here"
```

## Using the library as provider

### Add relation to metadata.yaml
```yaml
provides:
  k8s-svc-info:
    interface: k8s-service
```

### Instantiate the KubernetesServiceInfoProvider class in charm.py

```python
from ops.charm import CharmBase
from charms.<pending>.v0.kubernetes_service_info import KubernetesServiceInfoProvider, KubernetesServiceInfoRelationError

class ProviderCharm(CharmBase):
    def __init__(self, *args, **kwargs):
        ...
        self._k8s_svc_info_provider = KubernetesServiceInfoProvider,(self)
        self.observe(self.on.some_event, self._some_event_handler)
    def _some_event_handler(self, ...):
        # This will update the relation data bag with the GRPC Service name and port
        try:
            self._k8s_svc_info_provider.send_k8s_svc_info(svc_name, svc_port)
        except KubernetesServiceInfoRelationError as error:
            "your error handler goes here"
```

## Relation data

The data shared by this library is:
* svc_name: the name of the Kubernetes Service
  as it appears in the resource metadata, e.g. "metadata-grpc-service".
* svc_port: the port of the Kubernetes Service
"""

import logging

from ops.framework import Object
from ops.model import Relation

# The unique Charmhub library identifier, never change it
LIBID = "f5c3f6cc023e40468d6f9a871e8afcd0"

# Increment this major API version when introducing breaking changes
LIBAPI = 0

# Increment this PATCH version before using `charmcraft publish-lib` or reset
# to 0 if you are raising the major API version
LIBPATCH = 1

# Default relation and interface names. If changed, consistency must be kept
# across the provider and requirer.
DEFAULT_RELATION_NAME = "k8s-svc-info"
DEFAULT_INTERFACE_NAME = "k8s-service"
REQUIRED_ATTRIBUTES = ["svc_name", "svc_port"]

logger = logging.getLogger(__name__)


class KubernetesServiceInfoRelationError(Exception):
    """Base exception class for any relation error handled by this library."""

    pass


class KubernetesServiceInfoRelationMissingError(KubernetesServiceInfoRelationError):
    """Exception to raise when the relation is missing on either end."""

    def __init__(self):
        self.message = "Missing k8s-svc-info relation."
        super().__init__(self.message)


class KubernetesServiceInfoRelationDataMissingError(KubernetesServiceInfoRelationError):
    """Exception to raise when there is missing data in the relation data bag."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class KubernetesServiceInfoRequirer(Object):
    """Base class that represents a requirer relation end.

    Args:
        requirer_charm (CharmBase): the requirer application
        relation_name (str, optional): the name of the relation

    Attributes:
        relation_name (str): variable for storing the name of the relation
    """

    def __init__(self, requirer_charm, relation_name: str = DEFAULT_RELATION_NAME):
        super().__init__(requirer_charm, relation_name)
        self.relation_name = relation_name

    @staticmethod
    def _relation_preflight_checks(relation: Relation) -> None:
        """Series of checks for the relation and relation data.

        Args:
            relation (Relation): the relation object to run the checks on

        Raises:
            KubernetesServiceInfoRelationDataMissingError if data is missing or incomplete
            KubernetesServiceInfoRelationMissingError: if there is no related application
            ops.model.TooManyRelatedAppsError: if there is more than one related application
        """
        # Raise if there is no related application
        if not relation:
            raise KubernetesServiceInfoRelationMissingError()

        # Extract remote app information from relation
        remote_app = relation.app
        # Get relation data from remote app
        relation_data = relation.data[remote_app]

        # Raise if there is no data found in the relation data bag
        if not relation_data:
            raise KubernetesServiceInfoRelationDataMissingError(
                "No data found in relation data bag."
            )

        # Check if the relation data contains the expected attributes
        missing_attributes = [
            attribute for attribute in REQUIRED_ATTRIBUTES if attribute not in relation_data
        ]
        if missing_attributes:
            raise KubernetesServiceInfoRelationDataMissingError(
                f"Missing attributes: {missing_attributes}"
            )

    def get_k8s_svc_info(self) -> dict:
        """Return a dictionary with the Kubernetes Service information.

        Raises:
            KubernetesServiceInfoRelationDataMissingError: if data is missing entirely or some attributes
            KubernetesServiceInfoRelationMissingError: if there is no related application
        """
        # Run pre-flight checks
        # Raises TooManyRelatedAppsError if related to more than one app
        relation = self.model.get_relation(self.relation_name)
        self._relation_preflight_checks(relation=relation)

        # Get relation data from remote app
        relation_data = relation.data[relation.app]

        return {
            "svc_name": relation_data["svc_name"],
            "svc_port": relation_data["svc_port"],
        }


class KubernetesServiceInfoProvider(Object):
    """Base class that represents a provider relation end.

    Args:
        provider_charm (CharmBase): the provider application
        relation_name (str, optional): the name of the relation

    Attributes:
        provider_charm (CharmBase): variable for storing the provider application
        relation_name (str): variable for storing the name of the relation
    """

    def __init__(self, provider_charm, relation_name: str = DEFAULT_RELATION_NAME):
        super().__init__(provider_charm, relation_name)
        self.provider_charm = provider_charm
        self.relation_name = relation_name

    def send_k8s_svc_info_relation_data(
        self,
        svc_name: str,
        svc_port: str,
    ) -> None:
        """Update the relation data bag with data from a Kubernetes Service.

        This method will complete successfully even if there are no related applications.

        Args:
            svc_name (str): the name of the Kubernetes Service the provider knows about
            svc_port (str): the port number of the Kubernetes Service the provider knows about
        """
        # Update the relation data bag with a Kubernetes Service information
        relations = self.model.relations[self.relation_name]

        # Update relation data
        for relation in relations:
            relation.data[self.provider_charm.app].update(
                {
                    "svc_name": svc_name,
                    "svc_port": svc_port,
                }
            )
