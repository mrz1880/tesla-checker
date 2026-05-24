"""Pydantic schemas for Leboncoin __NEXT_DATA__ payloads."""

from __future__ import annotations

from pydantic import BaseModel, Field


class LbcAttribute(BaseModel):
    key: str = ""
    value: str = ""
    value_label: str = ""


class LbcLocation(BaseModel):
    city: str = ""
    zipcode: str = ""


class LbcAd(BaseModel):
    list_id: int = 0
    subject: str = ""
    body: str = ""
    url: str = ""
    price: list[int] = Field(default_factory=list)
    attributes: list[LbcAttribute] = Field(default_factory=list)
    location: LbcLocation = Field(default_factory=LbcLocation)


class LbcSearchData(BaseModel):
    ads: list[LbcAd] = Field(default_factory=list)
