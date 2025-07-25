"""Utilities to resolve important paths on the host and in the container."""

import os
from pathlib import Path
from typing import Callable, Optional, Union


class HostPaths:
    workspace_dir: Path
    """We assume all repositories live in a workspace directory, e.g., ``~/workspace/ls/localstack``,
    ``~/workspace/ls/localstack-pro``, ..."""

    localstack_project_dir: Path
    localstack_pro_project_dir: Path
    moto_project_dir: Path
    postgresql_proxy: Path
    rolo_dir: Path
    volume_dir: Path
    venv_dir: Path

    def __init__(
        self,
        workspace_dir: Union[os.PathLike, str] = None,
        volume_dir: Union[os.PathLike, str] = None,
        venv_dir: Union[os.PathLike, str] = None,
    ):
        self.workspace_dir = Path(workspace_dir or os.path.abspath(os.path.join(os.getcwd(), "..")))
        self.localstack_project_dir = self.workspace_dir / "localstack"
        self.localstack_pro_project_dir = self.workspace_dir / "localstack-pro"
        self.moto_project_dir = self.workspace_dir / "moto"
        self.postgresql_proxy = self.workspace_dir / "postgresql-proxy"
        self.rolo_dir = self.workspace_dir / "rolo"
        self.volume_dir = Path(volume_dir or "/tmp/localstack")
        self.venv_dir = Path(
            venv_dir
            or os.getenv("VIRTUAL_ENV")
            or os.getenv("VENV_DIR")
            or os.path.join(os.getcwd(), ".venv")
        )

    @property
    def aws_community_package_dir(self) -> Path:
        return self.localstack_project_dir / "localstack-core" / "localstack"

    @property
    def aws_pro_package_dir(self) -> Path:
        return (
            self.localstack_pro_project_dir / "localstack-pro-core" / "localstack" / "pro" / "core"
        )


# Type representing how to extract a specific path from a common root path, typically a lambda function
PathMappingExtractor = Callable[[HostPaths], Path]

# Declaration of which local packages can be mounted into the container, and their locations on the host
HOST_PATH_MAPPINGS: dict[
    str,
    PathMappingExtractor,
] = {
    "moto": lambda paths: paths.moto_project_dir / "moto",
    "postgresql_proxy": lambda paths: paths.postgresql_proxy / "postgresql_proxy",
    "rolo": lambda paths: paths.rolo_dir / "rolo",
    "plux": lambda paths: paths.workspace_dir / "plux" / "plugin",
}


class ContainerPaths:
    """Important paths in the container"""

    project_dir: str = "/opt/code/localstack"
    site_packages_target_dir: str = "/opt/code/localstack/.venv/lib/python3.11/site-packages"
    docker_entrypoint: str = "/usr/local/bin/docker-entrypoint.sh"
    localstack_supervisor: str = "/usr/local/bin/localstack-supervisor"
    localstack_source_dir: str
    localstack_pro_source_dir: Optional[str]

    def dependency_source(self, name: str) -> str:
        """Returns path of the given source dependency in the site-packages directory."""
        return self.site_packages_target_dir + f"/{name}"


class CommunityContainerPaths(ContainerPaths):
    """In the community image, code is copied into /opt/code/localstack/localstack-core/localstack"""

    def __init__(self):
        self.localstack_source_dir = f"{self.project_dir}/localstack-core/localstack"


class ProContainerPaths(ContainerPaths):
    """In the pro image, localstack and ext are installed into the venv as dependency"""

    def __init__(self):
        self.localstack_source_dir = self.dependency_source("localstack")
        self.localstack_pro_source_dir = self.dependency_source("localstack") + "/pro/core"
