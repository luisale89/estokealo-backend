from enum import Enum, unique


@unique
class RoleTypes(Enum):
    ADMIN:str = "admin"
    OWNER:str = "owner"
    OPERATOR:str = "operator"
    VIEWER:str = "viewer"


@unique
class OperationStatus(Enum):
    ACCEPTED:str = "accepted"
    PENDING:str = "pending"
    REJECTED:str = "rejected"


if __name__ == "__main__":
    print("RoleTypes values: ")
    for member in RoleTypes:
        print(member.value)

    print("---")
    print("OperationStatus values: ")
    for member in OperationStatus:
        print(member.value)

    
