# Copyright (c) 2026 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
This module contains utilities for creating medm assets. Some of these functions
create assets only in sandbox, while others create and publish them straight to
medm.
"""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from enum import Enum
from typing import Callable

import sgtk
from sgtk.flowam import create, utils
from tank_vendor.flow_integration_sdk import (
    exceptions,
    globals,
    objects,
    publish,
    sandbox,
    schema,
)

from ..constants import TEMPLATE_FOLDER, TEMPLATE_TYPE
from .utils import cleanpath, fileext


# ---------------------------------
# Classes
# ---------------------------------
class CreateMode(Enum):
    """Enum of modes for creating a new asset."""

    NEW = "new"  #: Create a DCC asset from a new scene as the source.
    CURRENT = "current"  #: Create a DCC asset from the current scene as the source.
    TEMPLATE = "template"  #: Create a DCC asset from template scene as the source.
    GENERIC = "generic"  #: Create a generic asset from a specified source file.


@dataclass
class CreateInputs(utils.BaseInputs):
    """Convenience structure to hold create inputs and allow them to be
    passed easily between helper functions.
    """

    #: Entity type of SG asset.
    sg_entity_type: str
    #: Name of the SG asset.
    #: This will be used for the AM asset name (both the container and workfile).
    sg_entity_name: str
    #: The name/code of the SG pipeline step associated with the current task context.
    sg_pipeline_step: str
    #: The AM project under which the asset should be added.
    am_project_id: str
    #: The name of the current SG task.
    sg_task_name: str = ""
    #: Description of asset.
    description: str = ""
    #: Determines which initial source file to use to create the asset.
    #: See `CreateMode` enum for valid values.
    create_mode: CreateMode = CreateMode.CURRENT
    #: Relevant only in some modes.
    #:      * TEMPLATE -> path to the template file to be used to build the new asset
    #:      * GENERIC -> path to the source file to copy directly to asset
    source_path: str = ""
    #: Optional callback function that will be called after scene is prepared
    prep_scene_callback: Callable | None = None

    def asdict(self):
        """Custom asdict to handle Enums and callables."""

        data = {}
        for key, value in self.__dict__.items():
            if isinstance(value, Enum):
                data[key] = value.value
            elif callable(value):
                data[key] = getattr(value, "__name__", str(value))
            else:
                data[key] = value
        return data

    def validate(self):
        """Check that input combinations are valid.

        Raises:
            CreateAssetError
        """

        # If sg entity name is provided, we also expect an entity type and pipeline step
        if self.sg_entity_name and not self.sg_entity_type:
            msg = "Incomplete sg context provided. Must provide sg_entity_type."
            raise exceptions.CreateAssetError(data=self.asdict(), details=msg)
        if self.sg_entity_name and not self.sg_pipeline_step:
            msg = "Incomplete sg context provided. Must provide sg_pipeline_step."
            raise exceptions.CreateAssetError(data=self.asdict(), details=msg)
        # If create mode is TEMPLATE or GENERIC, we need a source path
        if self.create_mode == CreateMode.TEMPLATE and not self.source_path:
            msg = "No template source path provided."
            raise exceptions.CreateAssetError(data=self.asdict(), details=msg)
        if self.create_mode == CreateMode.GENERIC and not self.source_path:
            msg = "No source path provided for generic asset."
            raise exceptions.CreateAssetError(data=self.asdict(), details=msg)
        # If pipeline step is provided, we expect task_name to be provided as well
        if self.sg_pipeline_step and not self.sg_task_name:
            msg = "Incomplete sg context provided. Must provide sg_task_name."
            raise exceptions.CreateAssetError(data=self.asdict(), details=msg)
        # prep_scene_callback is only applicable when create_mode is NEW or TEMPLATE
        if (
            self.create_mode == CreateMode.GENERIC
            and self.prep_scene_callback is not None
        ):
            msg = "prep_scene_callback is not applicable when create_mode is GENERIC."
            raise exceptions.CreateAssetError(data=self.asdict(), details=msg)

        # There should always be a project id provided
        if not self.am_project_id:
            raise exceptions.CreateAssetError(
                data=self.asdict(), details="No project id provided."
            )


@dataclass
class CreateTemplateInputs(utils.BaseInputs):
    """Convenience structure to hold create inputs and allow them to be
    passed easily between helper functions.
    """

    #: The name/code of the SG pipeline step that new template is for.
    sg_pipeline_step: str
    #: The AM project under which the template should be added.
    am_project_id: str
    #: The name new template asset.
    template_name: str = ""
    #: Description of template.
    description: str = ""
    #: Determines which initial source file to use to create the asset.
    #: See `CreateMode` enum for valid values.
    #: In the case of template creation, only NEW and CURRENT are applicable.
    create_mode: CreateMode = CreateMode.CURRENT

    def validate(self):
        """Check that input combinations are valid.

        Raises:
            CreateAssetError
        """

        # Pipeline step value must be provided
        if not self.sg_pipeline_step:
            msg = "No pipeline step provided."
            raise exceptions.CreateAssetError(data=self.asdict(), details=msg)
        # There should always be a project id provided
        if not self.am_project_id:
            raise exceptions.CreateAssetError(
                data=self.asdict(), details="No project id provided."
            )
        # Template must have a name
        if not self.template_name:
            raise exceptions.CreateAssetError(
                data=self.asdict(), details="No template name provided."
            )
        # Create mode TEMPLATE and GENERIC are not applicable for templates.
        if (
            self.create_mode == CreateMode.TEMPLATE
            or self.create_mode == CreateMode.GENERIC
        ):
            msg = f"Invalid CreateMode provided for template creation: {self.create_mode}."
            raise exceptions.CreateAssetError(data=self.asdict(), details=msg)


def get_template_source_path(template: objects.FlowAsset) -> str:
    """Return the published source path of the given template.
    Fetch binary if necessary.

    Args:
        template: Template asset.

    Returns:
        Full path to template file in blob storage.
    """
    revision = template.get_latest_revision()
    revision.fetch(component_purpose=globals.SOURCE_PURPOSE)
    return revision.get_storage_component_path(component_purpose=globals.SOURCE_PURPOSE)


# ---------------------------------
# Workflows
# ---------------------------------
def create_dcc_workfile(inputs: CreateInputs) -> sandbox.NewDraftInfo:
    """Create a DCC workfile asset in sandbox based on criteria provided in inputs.
    See documentation for CreateInputs for expected inputs.

    .. note:: Inputs can be passed in as a CreateInputs object assigned to the keyword
              argument _inputs_ or as a set of individual parameters. (e.g. sg_entity_name="my_name")

    Returns:
        A NewDraftInfo object containing all pertinent information about
        draft created for new asset, including draft id.

    Raises:
        CreateAssetError
    """
    app = sgtk.platform.current_bundle()
    inputs.log_intro("Creating new DCC workfile asset")
    inputs.validate()

    if not in_dcc_context():
        msg = "Cannot create DCC workfile without being in DCC."
        raise exceptions.CreateAssetError(data=inputs.asdict(), details=msg)

    # Create any necessary hierarchy above current asset
    parent = create.create_asset_hierarchy(inputs)

    # Create the workfile asset in sandbox
    draft_info = _create_dcc_workfile_asset(parent, inputs)

    app.log_info("Creating DCC asset complete!")

    # Open the draft file
    draft_path = draft_info.source_path
    app.log_info(f"Opening draft path: {draft_path}")
    flow_host().open_file(draft_path)

    app.context.set_flow_context(flow_host().current_file())

    return draft_info


def create_template_workfile(inputs: CreateTemplateInputs) -> sandbox.NewDraftInfo:
    """Create a DCC workfile asset in sandbox based on criteria provided in inputs.
    See documentation for CreateTemplateInputs for expected inputs.

    .. note:: Inputs can be passed in as a CreateTemplateInputs object assigned to the keyword
              argument _inputs_ or as a set of individual parameters. (e.g. sg_entity_name="my_name")

    Returns:
        A NewDraftInfo object containing all pertinent information about
        draft created for new asset, including draft id.

    Raises:
        CreateAssetError
    """
    app = sgtk.platform.current_bundle()

    inputs.log_intro("Creating new template asset")
    inputs.validate()

    if not in_dcc_context():
        msg = "Cannot create template workfile without being in DCC."
        raise exceptions.CreateAssetError(data=inputs.asdict(), details=msg)

    # Create any necessary hierarchy above current asset
    parent = _create_template_hierarchy(inputs)

    # Create the workfile asset in sandbox
    draft_info = _create_template_workfile_asset(parent, inputs)

    app.log_info("Creating template asset complete!")

    # Open the draft file
    draft_path = draft_info.source_path
    app.log_info(f"Opening draft path: {draft_path}")
    flow_host().open_file(draft_path)

    app.context.set_flow_context(flow_host().current_file())

    return draft_info


# ---------------------------------
# Auxiliary functions for workflows
# ---------------------------------
def flow_host() -> sgtk.flowam.host.FlowHost:
    """Convenience function to return the current host."""
    return sgtk.platform.current_engine().flow_host


def in_dcc_context() -> bool:
    """Return True if currently in a DCC context (i.e. engine is not tk-desktop)."""
    engine = sgtk.platform.current_engine()
    return engine.name != "tk-desktop"


def _has_workfile_type(parent: objects.FlowAsset, type_id: str) -> bool:
    """Return True if parent asset contains a child of given type."""

    if parent.find_children(type_id=type_id):
        return True
    return False


def _create_dcc_workfile_asset(
    parent: objects.FlowAsset, inputs: CreateInputs
) -> sandbox.NewDraftInfo:
    """Called when creating a new dcc workfile asset.
    This function will create the workfile asset in sandbox under the given parent.

    Args:
        parent: Asset to create workfile asset under.
        See CreateInputs documentation.

    Returns:
        The draft_info of the workfile asset created.

    Raises:
        CreateAssetError
    """
    app = sgtk.platform.current_bundle()

    # Determine workfile type to be created
    workfile_type = flow_host().WORKFILE_TYPE
    type_id = schema.get_schema_id(workfile_type)

    # Only allow one workfile of DCC type under parent
    if _has_workfile_type(parent, type_id):
        msg = f'A workfile of type "{workfile_type}" has already been created '
        msg += f'under pipeline step "{parent.name}". Please open the asset from '
        msg += "the Loader app to publish another revision of this asset."
        raise exceptions.CreateAssetError(data=inputs.asdict(), details=msg)

    # By convention asset name will be the sg entity name
    name = inputs.sg_entity_name

    # Prepare the source file and save to temporary location
    # By convention the source file will be named after the asset
    with tempfile.TemporaryDirectory() as temp_dir:
        ext = fileext(inputs.source_path) or flow_host().FILE_TYPES[0]
        temp_file = cleanpath(temp_dir, f"{name}.{ext}")
        if inputs.create_mode == CreateMode.NEW:
            # Clear scene
            flow_host().new_scene()
        elif inputs.create_mode == CreateMode.TEMPLATE:
            # Open the template file
            if not os.path.exists(inputs.source_path):
                msg = f"Template path does not exist: {inputs.source_path}"
                raise exceptions.CreateAssetError(data=inputs.asdict(), details=msg)
            try:
                flow_host().open_file(inputs.source_path)
            except Exception as exc:  # pylint: disable=broad-except
                msg = f"Could not open template path: {inputs.source_path}"
                raise exceptions.CreateAssetError(
                    data=inputs.asdict(), details=msg
                ) from exc

        # Call prep scene callback if provided
        if inputs.prep_scene_callback:
            try:
                inputs.prep_scene_callback()
            except Exception as exc:  # pylint: disable=broad-except
                msg = f"Error running prep_scene_callback during scene prep: {exc}"
                raise exceptions.CreateAssetError(data=inputs.asdict(), details=msg)

        app.log_info(f"Saving temp file to: {temp_file}")
        flow_host().save_file(temp_file)

        # Create a new asset in sandbox with a unique draft id
        app.log_info(
            f'Creating a workfile asset of type "{workfile_type}" for sg entity "{inputs.sg_entity_name}" in sandbox...'
        )
        desc = inputs.description
        return sandbox.create_asset_in_sandbox(
            name=name,
            description=desc,
            parent_id=parent.id,
            type_ids=[type_id],
            source_path=temp_file,
        )


def _create_template_hierarchy(inputs: CreateTemplateInputs) -> objects.FlowAsset:
    """Called when creating a template asset.
    This function will ensure that any hierarchical structuring above the workfile asset
    is created if necessary. (These will be committed directly to remote immediately.)

    High-level structure of template organization in AM project
    -----------------------------------------------------------

    - PROJECT
        - TEMPLATES FOLDER
            - pipeline step 1
                - template 1 (workfile)
                - template 2 (workfile)
            - pipeline step 2
                - template 1 (workfile)
                - template 2 (workfile)
                ...
            - pipeline step 3
            ...

    Args:
        See CreateTemplateInputs documentation.

    Returns:
        The parent asset of the workfile asset to be created.

    Raises:
        CreateAssetError
    """
    app = sgtk.platform.current_bundle()

    am_project_id = inputs.am_project_id
    sg_pipeline_step = inputs.sg_pipeline_step

    try:
        project = objects.FlowProject(am_project_id)
    except exceptions.FlowError as exc:
        msg = f"Invalid Flow project id provided: {am_project_id}"
        raise exceptions.CreateAssetError(data=inputs.asdict(), details=msg) from exc

    # Create top-level folder if it doesn't already exist in project
    folder = project.find_child(TEMPLATE_FOLDER)
    if not folder:
        app.log_info(f'Creating "{TEMPLATE_FOLDER}" folder...')
        desc = "Folder for template assets."
        folder = publish.publish_new_asset(
            name=TEMPLATE_FOLDER,
            parent_id=project.id,
            components=utils.create_components_for_publish(
                type_ids=[globals.FOLDER_TYPE_ID],
            ),
            description=desc,
        )

    # Create pipeline step if necessary
    # If a pipeline step asset associated with sg pipeline step doesn't exist, create it
    pipeline_step = folder.find_child(sg_pipeline_step)
    if not pipeline_step:
        app.log_info(f'Creating pipeline step asset for "{sg_pipeline_step}"...')
        pipeline_step_type_id = schema.get_schema_id(create.PIPELINE_STEP_TYPE)
        pipeline_step = publish.publish_new_asset(
            name=sg_pipeline_step,
            parent_id=folder.id,
            components=utils.create_components_for_publish(
                type_ids=[pipeline_step_type_id],
            ),
        )

    return pipeline_step


def _create_template_workfile_asset(
    parent: objects.FlowAsset, inputs: CreateTemplateInputs
) -> sandbox.NewDraftInfo:
    """Called when creating a new template workfile asset.
    This function will create the workfile asset in sandbox under the given parent.

    Args:
        parent: Asset to create workfile asset under.
        See CreateTemplateInputs documentation.

    Returns:
        The draft id of the workfile asset created.
    """
    app = sgtk.platform.current_bundle()

    # Determine workfile type to be created
    # NOTE: templates will have dual types, both a dcc type
    #       and template designation
    workfile_type = flow_host().WORKFILE_TYPE
    workfile_type_id = schema.get_schema_id(workfile_type)
    template_type_id = schema.get_schema_id(TEMPLATE_TYPE)

    name = inputs.template_name

    # Prepare the source file and save to temporary location
    # By convention the source file will be named after the asset
    with tempfile.TemporaryDirectory() as temp_dir:
        ext = flow_host().FILE_TYPES[0]
        temp_file = cleanpath(temp_dir, f"{name}.{ext}")
        if inputs.create_mode == CreateMode.NEW:
            # Clear scene
            flow_host().new_scene()
        app.log_info(f"Saving temp file to: {temp_file}")
        flow_host().save_file(temp_file)

        # Create a new asset in sandbox with a unique draft id
        app.log_info(
            f'Creating a template asset of type "{workfile_type}" for pipeline step "{inputs.sg_pipeline_step}" in sandbox...'
        )
        desc = inputs.description
        return sandbox.create_asset_in_sandbox(
            name=name,
            description=desc,
            parent_id=parent.id,
            type_ids=[workfile_type_id, template_type_id],  # flag as template type
            source_path=temp_file,
        )
