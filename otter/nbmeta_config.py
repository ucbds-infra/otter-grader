"""A config definition for Otter's configurations stored in the notebook metadata"""

import fica
import nbformat as nbf

from typing import Any, Optional

from .utils import NOTEBOOK_METADATA_KEY


OK_FORMAT_VARNAME = "OK_FORMAT"


class NBMetadataConfig(fica.Config):
    """
    The configurations stored in a notebook's metadata.

    This object defines the structure of the configurations that Otter can store in a notebook
    file's metadata. These configurations are parsed from ``nb["metadata"]["otter"]``.
    """

    assignment_name: Optional[str] = fica.Key(
        type_=str,
        allow_none=True,
    )
    """the name of the assignment"""

    tests: dict[str, dict[str, Any]] = fica.Key(
        type_=dict,
        # This value should never be None unless the value specified in the notebook metadata is
        # null. It is here as a patch for fica, which doesn't handle type-checking a factory
        # correctly.
        # TODO: remove allow_none=True once fica fixes this bug (chrispyles/fica#33)
        allow_none=True,
        factory=lambda: {},
    )
    """test cases keyed by question name"""

    ok_format: bool = fica.Key(
        name=OK_FORMAT_VARNAME,
        type_=bool,
        allow_none=True,
    )
    """whether the tests in ``tests`` are in the OK format"""

    require_no_pdf_confirmation: Optional[bool] = fica.Key(
        type_=bool,
        allow_none=True,
    )
    """whether to require students to acknowledge that a PDF couldn't be generated during export"""

    export_pdf_failure_message: Optional[str] = fica.Key(
        type_=str,
        allow_none=True,
    )
    """a custom message to display to students when ACKing the lack of a PDF"""

    def __init__(
        self,
        user_config: Optional[dict[str, Any]] = None,
        documentation_mode: bool = False,
        require_valid_keys: bool = False,
    ) -> None:
        if user_config is None:
            user_config = {}
        if ("tests" in user_config) != (OK_FORMAT_VARNAME in user_config):
            raise ValueError(f"{OK_FORMAT_VARNAME} must be specified with tests")

        super().__init__(user_config, documentation_mode, require_valid_keys)

    @classmethod
    def from_notebook(cls, nb: nbf.NotebookNode) -> "NBMetadataConfig":
        """
        Create a :py:class:`NBMetadataConfig` from a notebook object.
        """
        return cls(nb.get("metadata", {}).get(NOTEBOOK_METADATA_KEY, {}))
