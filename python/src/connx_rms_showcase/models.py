from pydantic import BaseModel, ConfigDict, Field


class Customer(BaseModel):
    # Accept both the API field names (customer_id, city, ...) and the CONNX column
    # names (customerid, customercity, ...) when building a model.
    model_config = ConfigDict(str_strip_whitespace=True, validate_by_name=True, validate_by_alias=True)

    customer_id: str = Field(alias="customerid", max_length=5)
    name: str = Field(alias="customername", max_length=31)
    address: str | None = Field(default=None, alias="customeraddress", max_length=22)
    city: str | None = Field(default=None, alias="customercity", max_length=14)
    state: str | None = Field(default=None, alias="customerstate", max_length=10)
    zip_code: str | None = Field(default=None, alias="customerzip", max_length=8)
    country: str | None = Field(default=None, alias="customercountry", max_length=7)
    phone: str | None = Field(default=None, alias="customerphone", max_length=14)
