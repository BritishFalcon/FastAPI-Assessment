from pydantic import BaseModel, confloat, constr, model_validator


class RequestBase(BaseModel):

    question: constr(min_length=1, max_length=500, strict=True)
    sw_lat: confloat(ge=-90.0, le=90.0, strict=True)
    sw_lon: confloat(ge=-180.0, le=180.0, strict=True)
    ne_lat: confloat(ge=-90.0, le=90.0, strict=True)
    ne_lon: confloat(ge=-180.0, le=180.0, strict=True)

    @model_validator(mode="after")
    def validate_coordinates(cls, model):
        if model.sw_lat >= model.ne_lat or model.sw_lon >= model.ne_lon:
            raise ValueError("Current co-ordinates are inverse, an hence invalid!")
        return model
