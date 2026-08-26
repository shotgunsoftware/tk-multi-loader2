# Copyright (c) 2026 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""Unit tests for the Flow AM pipeline step validation helpers."""

import importlib.util
import pathlib
import types

import pytest

MODULE_PATH = (
    pathlib.Path(__file__).resolve().parent.parent
    / "python"
    / "tk_multi_loader"
    / "flowam"
    / "step_validation.py"
)

try:
    # step_validation only depends on sgtk and the Flow Integration SDK, so load
    # it straight from disk rather than through the flowam package, whose other
    # modules pull in Qt and a live engine.
    import sgtk  # noqa: F401
    from tank_vendor.flow_integration_sdk import exceptions  # noqa: F401

    _spec = importlib.util.spec_from_file_location("step_validation", MODULE_PATH)
    step_validation = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(step_validation)
except ImportError:
    # Flow AM features need a tk-core that ships the Flow Integration SDK.
    pytestmark = pytest.mark.skip()


ENTITY_NAME = "Hero"
MAYA_TYPE = "type.workfile.maya"
MAYA_TYPE_ID = "schema-id-maya-workfile"


class StubWorkfile:
    """Stand-in for a workfile asset carrying a single schema type."""

    def __init__(self, name, type_id, revision_id="rev-1"):
        self.name = name
        self.type_id = type_id
        self.revision_id = revision_id


class StubNode:
    """Minimal stand-in for a ``FlowProject`` or ``FlowAsset``."""

    def __init__(self, name, children=(), workfiles=()):
        self.name = name
        self._children = {child.name: child for child in children}
        self._workfiles = list(workfiles)

    def find_child(self, name, force_query=False):
        return self._children.get(name)

    def find_children(self, name="", type_id="", force_query=False):
        return [w for w in self._workfiles if w.type_id == type_id]


def build_project(steps, root_folder="Assets", entity_name=ENTITY_NAME):
    """Build a stub ``<root_folder>/<entity>/<step>/<entity>`` hierarchy.

    :param steps: Mapping of pipeline step name to whether that step has a
        published workfile for the entity.
    :param root_folder: Name of the project's top-level folder.
    :param entity_name: Name of the entity the steps belong to.
    :returns: The stub project node.
    """
    step_nodes = []
    for step_name, is_published in steps.items():
        workfiles = (
            [
                StubWorkfile(
                    f"{entity_name} - MAYA",
                    MAYA_TYPE_ID,
                    revision_id=f"rev-{step_name}",
                )
            ]
            if is_published
            else []
        )
        asset_root = StubNode(entity_name, workfiles=workfiles)
        step_nodes.append(StubNode(step_name, children=[asset_root]))

    container = StubNode(entity_name, children=step_nodes)
    return StubNode("project", children=[StubNode(root_folder, children=[container])])


@pytest.fixture
def flow_am(monkeypatch):
    """Return a callable pointing ``step_validation`` at a stub project."""

    def _install(project, resolve_type_id=True):
        monkeypatch.setattr(
            step_validation,
            "objects",
            types.SimpleNamespace(FlowProject=lambda _project_id: project),
        )
        monkeypatch.setattr(
            step_validation,
            "schema",
            types.SimpleNamespace(
                get_schema_id=lambda name: (
                    MAYA_TYPE_ID if resolve_type_id and name == MAYA_TYPE else None
                )
            ),
        )

    return _install


def find_unpublished(step="Surfacing", entity_type="Asset", dependencies=None):
    """Call the module under test with the common set of arguments."""
    return step_validation.find_unpublished_upstream_step(
        am_project_id="am-project-1",
        sg_entity_type=entity_type,
        sg_entity_name=ENTITY_NAME,
        sg_pipeline_step=step,
        workfile_type=MAYA_TYPE,
        step_dependencies=(
            {"Surfacing": "Model"} if dependencies is None else dependencies
        ),
    )


@pytest.mark.parametrize(
    "pipeline_step,step_dependencies,expected",
    [
        ("Surfacing", {"Surfacing": "Model"}, "Model"),
        ("Rigging", {"Rigging": "Model", "Surfacing": "Model"}, "Model"),
        ("Model", {"Surfacing": "Model"}, None),
        ("", {"Surfacing": "Model"}, None),
        ("Surfacing", {}, None),
        ("Surfacing", {"Surfacing": ""}, None),
    ],
)
def test_get_upstream_step(pipeline_step, step_dependencies, expected):
    """Only steps mapped to a non-empty upstream step resolve to one."""
    assert (
        step_validation.get_upstream_step(pipeline_step, step_dependencies) == expected
    )


def test_upstream_published_allows_build(flow_am):
    """No warning when the upstream step has a published workfile."""
    flow_am(build_project({"Model": True}))
    assert find_unpublished() is None


def test_upstream_present_but_unpublished_warns(flow_am):
    """The step folder existing is not proof of a publish."""
    flow_am(build_project({"Model": False}))
    assert find_unpublished() == "Model"


def test_upstream_step_missing_warns(flow_am):
    """A step nobody has touched yet has nothing published."""
    flow_am(build_project({"Layout": True}))
    assert find_unpublished() == "Model"


def test_step_without_configured_upstream_is_not_checked(flow_am):
    """Steps absent from the mapping are never validated."""
    flow_am(build_project({"Model": False}))
    assert find_unpublished(step="Model") is None


def test_unsupported_entity_type_is_skipped(flow_am):
    """An entity type with no Flow AM folder cannot be checked, so it passes."""
    flow_am(build_project({"Model": False}))
    assert find_unpublished(entity_type="CustomEntity01") is None


def test_shot_entity_uses_shot_folder(flow_am):
    """Shots live under "Shot" rather than "Assets"."""
    flow_am(build_project({"Model": True}, root_folder="Shot"))
    assert find_unpublished(entity_type="Shot") is None

    flow_am(build_project({"Model": True}, root_folder="Assets"))
    assert find_unpublished(entity_type="Shot") == "Model"


def test_unresolved_workfile_type_is_skipped(flow_am):
    """An unresolved schema id would match every child, so the check is skipped."""
    flow_am(build_project({"Model": False}), resolve_type_id=False)
    assert find_unpublished() is None


def test_flow_am_error_allows_build(monkeypatch, flow_am):
    """A Flow AM outage must not block a build behind a misleading message."""

    def raise_error(_project_id):
        raise step_validation.exceptions.FlowError("simulated Flow AM outage")

    flow_am(build_project({"Model": False}))
    monkeypatch.setattr(
        step_validation, "objects", types.SimpleNamespace(FlowProject=raise_error)
    )
    assert find_unpublished() is None


def find_upstream(step="Surfacing", entity_type="Asset", dependencies=None):
    """Call the referencing resolver with the common set of arguments."""
    return step_validation.find_upstream_workfile(
        am_project_id="am-project-1",
        sg_entity_type=entity_type,
        sg_entity_name=ENTITY_NAME,
        sg_pipeline_step=step,
        workfile_type=MAYA_TYPE,
        step_dependencies=(
            {"Surfacing": "Model"} if dependencies is None else dependencies
        ),
    )


def test_find_upstream_workfile_returns_published_asset(flow_am):
    """The upstream step's published workfile asset is returned for referencing."""
    flow_am(build_project({"Model": True}))
    workfile = find_upstream()
    assert workfile is not None
    assert workfile.revision_id == "rev-Model"


def test_find_upstream_workfile_none_when_unpublished(flow_am):
    """Nothing to reference when the upstream step has no publish."""
    flow_am(build_project({"Model": False}))
    assert find_upstream() is None


def test_find_upstream_workfile_none_without_configured_upstream(flow_am):
    """Steps absent from the mapping resolve no reference."""
    flow_am(build_project({"Model": True}))
    assert find_upstream(dependencies={}) is None


def test_find_upstream_workfile_none_for_unsupported_entity(flow_am):
    """An entity type with no Flow AM folder resolves no reference."""
    flow_am(build_project({"Model": True}))
    assert find_upstream(entity_type="CustomEntity01") is None


def test_find_upstream_workfile_none_when_type_unresolved(flow_am):
    """An unresolved schema id would match every child, so skip referencing."""
    flow_am(build_project({"Model": True}), resolve_type_id=False)
    assert find_upstream() is None


def test_find_upstream_workfile_none_on_flow_am_error(monkeypatch, flow_am):
    """A Flow AM outage skips referencing rather than surfacing an error."""

    def raise_error(_project_id):
        raise step_validation.exceptions.FlowError("simulated Flow AM outage")

    flow_am(build_project({"Model": True}))
    monkeypatch.setattr(
        step_validation, "objects", types.SimpleNamespace(FlowProject=raise_error)
    )
    assert find_upstream() is None
