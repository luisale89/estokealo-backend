from api.extensions import db


class RoleFunction(db.Model):
    __tablename__="role_function"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32))
    code = db.Column(db.String(32), unique=True, nullable=False)
    description = db.Column(db.Text)
    access_level = db.Column(db.Integer, default=0)
    #relations

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
        return {
            self.__tablename__: self._base_serializer()
        }
    
    @staticmethod
    def _get_rolefunc_by_code(code:str):
        return db.session.query(RoleFunction.id).filter(RoleFunction.code == code).first()

    @classmethod
    def add_defaults(cls):
        commit = False
        owner = cls._get_rolefunc_by_code("owner")
        if not owner:
            newOwnerFunction = cls(
                name= "propietario",
                code= "owner",
                description= "usuario puede administrar todos los aspectos de la aplicación",
                level= 0
            )

            db.session.add(newOwnerFunction)
            commit = True

        admin = cls._get_rolefunc_by_code("admin")
        if not admin:
            newAdminFunction = cls(
                name = "administrador",
                code = "admin",
                description= "puede administrar algunos aspectos de la aplicación, con algunas limitaciones",
                level=1
            )

            db.session.add(newAdminFunction)
            commit = True

        operator = cls._get_rolefunc_by_code("operator")
        if not operator:
            newOperatorFunction = cls(
                name= "operador",
                code= "operator",
                description= "Este usuario solo puede realizar acciones asignadas y modificar algunos aspectos de la aplicación",
                level=2
            )

            db.session.add(newOperatorFunction)
            commit=True

        viewer = cls._get_rolefunc_by_code("viewer")
        if not viewer:
            newViewerFunction = cls(
                name= "observador",
                code= "viewer",
                description="Este usuario es de solo lectura, y puede visualizar los aspectos públicos de la aplicación",
                level= 99
            )

            db.session.add(newViewerFunction)
            commit = True

        if commit:
            db.session.commit()

        pass