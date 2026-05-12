import logging
logger = logging.getLogger(__name__)

from sqlalchemy import Engine
from sqlalchemy.orm import Session
from zworkflow.dal.dtos import SchemaDTO
from zworkflow.dal.daos import SchemaDAO

def test_task_def_dao(engine:Engine, schema_dao:SchemaDAO):
    # 保存一个SchemaDTO
    with Session(engine) as session:
        with session.begin() as transaction:
            schema_definition = {
                "type": "object",
                "required": ["x", "y"],
                "properties": {
                    "x": {
                        "type": "integer",
                        "description": "The x coordinate"
                    },
                    "y": {
                        "type": "integer",
                        "description": "The y coordinate"
                    }
                },
                "additionalProperties": False
            }
            schema_dto = schema_dao.save(
                SchemaDTO(
                    name = "Pixel",
                    version = "1.0",
                    description="Pixel",
                    title = "Pixel",
                    definition = schema_definition
                ),
                session=session
            )
            # it should be saved, id should not be None
            # field value shoudl match
            schema_id = schema_dto.id
            assert schema_dto.id is not None
            assert schema_dto.name == "Pixel"
            assert schema_dto.version == "1.0"
            assert schema_dto.description == "Pixel"
            assert schema_dto.title == "Pixel"
            assert schema_dto.definition == schema_definition
    
    # Loading the schema, make sure nothing is saved wrong
    with Session(engine) as session:
        schema_dto = schema_dao.get(schema_id, session=session)
        assert schema_dto.id == schema_id
        assert schema_dto.name == "Pixel"
        assert schema_dto.version == "1.0"
        assert schema_dto.description == "Pixel"
        assert schema_dto.title == "Pixel"
        assert schema_dto.definition == schema_definition
    
    # try to list Schema should return one
    with Session(engine) as session:
        schema_dtos = schema_dao.list(session=session)
        assert len(schema_dtos) == 1
        schema_dto = schema_dtos[0]
        assert schema_dto.id == schema_id
        assert schema_dto.name == "Pixel"
        assert schema_dto.version == "1.0"
        assert schema_dto.description == "Pixel"
        assert schema_dto.title == "Pixel"
        assert schema_dto.definition == schema_definition
