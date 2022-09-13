from api.extensions import db
from api.utils import helpers as h
from datetime import datetime
from flask import abort
from sqlalchemy.sql.functions import ReturnTypeFromArgs


def update_row_content(model, new_row_data: dict) -> tuple[dict, dict]:
    """
    Funcion para actualizar el contenido de una fila de cualquier tabla en la bd.
    Recorre cada item del parametro <new_row_data> y determina si el nombre coincide con el nombre de una de las
     columnas.
    en caso de coincidir, se hacen validaciones sobre el contenido, si coincide con la instancia esperada en la
    columna de la bd y se devuelve un diccionario con los valores a actualizar en el modelo.

    * Parametros:

    1. model: instancia de los modelos de la bd
    2. new_row_data: diccionario con el contenido a actualizar en el modelo. Generalmente es el body del request
    recibido en el endpoint
        request.get_json()..

    *
    Respuesta:
    -> tuple con el formato: (to_update:{dict}, invalids:[list], warnings:{dict})

    Raises:
    -> APIExceptions ante cualquier error de instancias, cadena de caracteres erroneas, etc.

    """
    table_columns = model.__table__.columns
    to_update = {}
    warnings = {}

    for row, content in new_row_data.items():
        if row in table_columns:  # si coinicide el nombre del parmetro con alguna de las columnas de la db
            data = table_columns[row]
            if data.name.startswith("_") or data.primary_key or data.name.endswith("_id"):
                continue  # columnas que cumplan con los criterios anteriores no se pueden actualizar en esta funcion.

            column_type = data.type.python_type

            if not isinstance(content, column_type):
                warnings.update({row: f"invalid instance, [{column_type.__name__}] is expected"})
                continue

            if column_type == datetime:
                content = h.normalize_datetime(content)
                if not content:
                    warnings.update({row: f"invalid datetime format, {content} was received"})
                    continue  # continue with the next loop

            if isinstance(content, str):
                sh = h.StringHelpers(string=content)
                valid, msg = sh.is_valid_string(max_length=data.type.length)
                if not valid:
                    warnings.update({row: msg})
                    continue

                content = sh.normalize(spaces=True)

            if isinstance(content, list) or isinstance(content, dict):  # formatting json content
                content = {f"{table_columns[row].name}": content}

            to_update[row] = content

    if not to_update:
        warnings.update({"empty_params": 'no match were found between app-parameters and parameters in body'})

    return to_update, warnings


def handle_db_error(error) -> None:
    """handle SQLAlchemy Exceptions and errors"""
    db.session.rollback()
    abort(500, f"{error}")


class Unaccent(ReturnTypeFromArgs):
    inherit_cache = True
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)