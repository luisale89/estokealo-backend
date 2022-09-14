from api.extensions import db


class RoleFunction(db.Model):
    __tablename__="role_function"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32))
    code = db.Column(db.String(32), unique=True, nullable=False)
    description = db.Column(db.Text)
    access_level = db.Column(db.Integer, default=0)
    #relations
    roles = db.relationship("Role", back_populates="role_function", lazy="dynamic")

    def __repr__(self) -> str:
        return f"RoleFunction(id={self.id})"

    def _base_serializer(self) -> dict:
        return {
            "ID": self.id,
            "name": self.name,
            "code": self.code,
            "description": self.description,
            "access_level": self.access_level
        }

    def serialize(self):
        return self._base_serializer()
    
    @staticmethod
    def _get_rolefunc_by_code(code:str):
        return db.session.query(RoleFunction.id).filter(RoleFunction.code == code).first()

    @classmethod
    def add_defaults(cls, cls_to_return:str="owner"):
        commit = {}
        owner = cls._get_rolefunc_by_code("owner")
        if not owner:
            newOwnerFunction = cls(
                name= "propietario",
                code= "owner",
                description= "usuario puede administrar todos los aspectos de la aplicación",
                access_level= 0
            )

            db.session.add(newOwnerFunction)
            commit.update({"owner": newOwnerFunction})

        admin = cls._get_rolefunc_by_code("admin")
        if not admin:
            newAdminFunction = cls(
                name = "administrador",
                code = "admin",
                description= "puede administrar algunos aspectos de la aplicación, con algunas limitaciones",
                access_level=1
            )

            db.session.add(newAdminFunction)
            commit.update({"admin": newAdminFunction})

        operator = cls._get_rolefunc_by_code("operator")
        if not operator:
            newOperatorFunction = cls(
                name= "operador",
                code= "operator",
                description= "Este usuario solo puede realizar acciones asignadas y modificar algunos aspectos de la aplicación",
                access_level=2
            )

            db.session.add(newOperatorFunction)
            commit.update({"operator": newOperatorFunction})

        viewer = cls._get_rolefunc_by_code("viewer")
        if not viewer:
            newViewerFunction = cls(
                name= "observador",
                code= "viewer",
                description="Este usuario es de solo lectura, y puede visualizar los aspectos públicos de la aplicación",
                access_level= 99
            )

            db.session.add(newViewerFunction)
            commit.update({"viewer": newViewerFunction})

        if commit:
            db.session.commit()

        return commit.get(cls_to_return, None)