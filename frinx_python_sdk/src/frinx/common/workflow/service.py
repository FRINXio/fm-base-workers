import logging

from frinx.common.workflow.workflow import WorkflowImpl

logger = logging.getLogger(__name__)


class ServiceWorkflowsImpl:
    service_workflows: list[type[WorkflowImpl]] = []

    def __init__(self, workflows: list[type[WorkflowImpl]] = None, exclude: bool = False) -> None:
        """

        Args:
            workflows: list of Workflows [workflow subclasses]
            exclude: If true, exclude workflows from all workflows. Else install only selected.
        """
        if workflows is None:
            workflows = []
        self.service_workflows = self._inner_class_list(workflows, exclude)

    def register(self, overwrite: bool = False) -> None:
        """
        Register workflows to conductor.

        Args:
            overwrite: Overwrite all workflow if exists.
        """
        for task in self.service_workflows:
            # TODO check if need to run constructor
            # task().register(overwrite)
            task.register(overwrite)

    @classmethod
    def _inner_class_list(
        cls, workflows: list[type[WorkflowImpl]], exclude: bool
    ) -> list[type[WorkflowImpl]]:
        """
        Create list od inner workflows in class.
        Possibility to install only selected workflow or exclude selected from all.

        Args:
            workflows: List of workflows to install/exclude.
            exclude: If true, exclude mode is used. Else install only selected workflows.

        Returns:
            object:
        """

        if workflows is None:
            workflows = []

        try:
            class_workflows = []

            for attr_name in cls.__dict__.values():
                if isinstance(attr_name, type) and issubclass(attr_name, WorkflowImpl):
                    class_workflows.append(attr_name)

            match exclude:
                case True:
                    for workflow in workflows:
                        class_workflows.remove(workflow)
                    return class_workflows
                case False:
                    required_workflows = []
                    if len(workflows) > 0:
                        for workflow in workflows:
                            if workflow in class_workflows:
                                required_workflows.append(workflow)
                            else:
                                # TODO what should happened if wrong workflow was imported?
                                logger.info("Workflow %s missing in %s", workflow, cls.__name__)
                    else:
                        return class_workflows
                    return required_workflows
        except Exception as error:
            logger.error(error)
            return []
            # TODO what should happened?
