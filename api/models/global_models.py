from api.extensions import db
from api.utils.enums import RoleTypes


class RoleFunction(db.Model):
    __tablename__ = "role_function"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32))
    code = db.Column(db.String(32), unique=True, nullable=False)
    description = db.Column(db.Text)
    access_level = db.Column(db.Integer, default=0)
    # relations

    def __repr__(self) -> str:
        return f"RoleFunction(id={self.id})"

    def _base_serializer(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "description": self.description,
            "accessLevel": self.access_level,
        }

    def serialize(self):
        return self._base_serializer()

    @staticmethod
    def _get_rolefunc_by_code(code: str):
        return (
            db.session.query(RoleFunction.id).filter(RoleFunction.code == code).first()
        )

    @classmethod
    def add_defaults(cls, cls_to_return: str = RoleTypes.OWNER.value):
        """stores all roles in the database, and returns cls_to_return class, to be used"""
        commit = {}
        owner = cls._get_rolefunc_by_code(RoleTypes.OWNER.value)
        if not owner:
            newOwnerFunction = cls(
                name="Propietario",
                code=RoleTypes.OWNER.value,
                description="usuario puede administrar todos los aspectos de la aplicación",
                access_level=0,
            )

            db.session.add(newOwnerFunction)
            commit.update({"owner": newOwnerFunction})

        admin = cls._get_rolefunc_by_code(RoleTypes.ADMIN.value)
        if not admin:
            newAdminFunction = cls(
                name="Administrador",
                code=RoleTypes.ADMIN.value,
                description="puede administrar algunos aspectos de la aplicación, con algunas limitaciones",
                access_level=1,
            )

            db.session.add(newAdminFunction)
            commit.update({"admin": newAdminFunction})

        operator = cls._get_rolefunc_by_code(RoleTypes.OPERATOR.value)
        if not operator:
            newOperatorFunction = cls(
                name="Operador",
                code=RoleTypes.OPERATOR.value,
                description="Este usuario solo puede realizar acciones asignadas y modificar algunos aspectos de la aplicación",
                access_level=2,
            )

            db.session.add(newOperatorFunction)
            commit.update({"operator": newOperatorFunction})

        viewer = cls._get_rolefunc_by_code(RoleTypes.VIEWER.value)
        if not viewer:
            newViewerFunction = cls(
                name="Observador",
                code=RoleTypes.VIEWER.value,
                description="Este usuario es de solo lectura, y puede visualizar los aspectos públicos de la aplicación",
                access_level=99,
            )

            db.session.add(newViewerFunction)
            commit.update({"viewer": newViewerFunction})

        if commit:
            db.session.commit()

        return commit.get(cls_to_return, None)
