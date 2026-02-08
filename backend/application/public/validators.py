from ..extension import ma
from ..model import Programme, Branch


class ProgrammePublicSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Programme
        load_instance = False
        include_relationships = True

    id = ma.auto_field(dump_only=True)
    name = ma.auto_field(dump_only=True)
    code = ma.auto_field(dump_only=True)
    duration_years = ma.auto_field(dump_only=True)
    is_active = ma.auto_field(dump_only=True)

    branches = ma.Nested(
        "BranchPublicSchema",
        many=True,
        dump_only=True
    )


class BranchPublicSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Branch
        load_instance = False

    id = ma.auto_field(dump_only=True)
    code = ma.auto_field(dump_only=True)
    name = ma.auto_field(dump_only=True)
    is_active = ma.auto_field(dump_only=True)


