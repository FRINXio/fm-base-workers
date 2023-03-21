from frinx.client.FrinxConductorWrapper import FrinxConductorWrapper
from frinx.common.worker.worker import WorkerImpl
from pydantic import dataclasses


class Config:
    arbitrary_types_allowed = True


@dataclasses.dataclass(config=Config)
class ServiceWorkersImpl:
    def __init__(self) -> None:
        self.service_workers = self._inner_class_list()

    def Tasks(self) -> list[WorkerImpl]:
        return self.service_workers

    def register(self, cc: FrinxConductorWrapper) -> None:
        for task in self.service_workers:
            task.register(cc)

    @classmethod
    def _inner_class_list(cls) -> list[WorkerImpl]:
        results = []
        for attr_name in dir(cls):
            obj = getattr(cls, attr_name)
            if isinstance(obj, type) and issubclass(obj, WorkerImpl):
                task = obj()  # TODO is that good solution?
                results.append(task)
        return results
