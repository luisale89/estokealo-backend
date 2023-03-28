from jsonschema import validate
from jsonschema.exceptions import ValidationError

schema={
    "type": "object",
    "properties": {
        "verification_code": {"type": "integer", "minimum": 100000, "maximum": 999999},
        "name": {"type": "string", "minLength": 1},
        "email": {"type": "string", "minLength": 1},
        "address": {"type": "object", "properties": {
            "street": {"type": "string"},
            "city": {"type": "string"},
            "country": {"type": "string"},
            "zip_code": {"type": "integer"}
        }, 
        "required": ["street", "city", "country"],
        "additionalProperties": False
        }
    },
    "required": ["name", "email"],
    "additionalProperties": False
}

if __name__ == "__main__":
    instance = {
        "verification_code": 1234556778,
        "name": "1223",
        "email": "12345"
    }
    try:
        validate(instance=instance, schema=schema)
        print("valid")
    except ValidationError as e:
        response = {e.path[0]: e.message}
        print(response)