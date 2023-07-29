from enum import Enum


class BaseEnum(Enum):
    @classmethod
    def values_as_list(cls) -> list:
        return [c.value for c in cls]

    @classmethod
    def names_as_list(cls) -> list:
        return [c.name for c in cls]

    @classmethod
    def as_dict(cls) -> list:
        return [{c.name: c.value} for c in cls]


class AccessLevel(BaseEnum):
    OWNER = 0
    ADMIN = 1
    OPERATOR = 2
    CLIENT = 3
    VIEWER = 99


class RoleTypes(BaseEnum):
    OWNER = "propietario"
    ADMIN = "administrador"
    OPERATOR = "operador"
    CLIENT = "cliente"
    VIEWER = "observador"


class OperationStatus(BaseEnum):
    ACCEPTED = "accepted"
    PENDING = "pending"
    REJECTED = "rejected"


if __name__ == "__main__":
    print("AccessLevel values: ")
    print(AccessLevel.values_as_list())
    print(AccessLevel.names_as_list())
    print(AccessLevel.as_dict())
    print(AccessLevel.OPERATOR.value)

    print("---")
    print("OperationStatus values: ")
    print(OperationStatus.values_as_list())
