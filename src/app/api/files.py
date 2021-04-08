from typing import Optional

from fastapi import APIRouter, status, UploadFile, File, Header
from ..db import files as files_repository

from ..utils.Exceptions import raise_422_exception, raise_401_exception, raise_404_exception
from ..utils import token
from ..core.validator import Validator, SupportedFormat
from ..core.convertors.helper_functions import convert_to_geojson as to_geojson
from fastapi.responses import FileResponse
from pathlib import Path
from geojson_pydantic.features import FeatureCollection
from pydantic import parse_obj_as
from .schemas import FileRecord
import os
from dataclasses import asdict

router = APIRouter()


async def file_request_handler(file_uuid: str, access_token: Optional[str] = None):
    if not access_token:
        raise_401_exception()
    user = await token.check_user_credentials(access_token)
    if not user:
        raise_401_exception()
    file_record = await files_repository.get_one(file_uuid)
    if not file_record:
        raise_404_exception()
    if file_record.get("user_id") != user["user_id"]:
        raise_401_exception()
    if not Path(file_record.get("path")).exists():
        raise_404_exception()
    return FileRecord.parse_obj(dict(file_record))

@router.post("/upload/", status_code=status.HTTP_201_CREATED)
async def create_upload_file(file: UploadFile = File(...), access_token: Optional[str] = Header(None)):
    print(access_token)
    if not access_token:
        raise_401_exception()
    filename, file_extension = os.path.splitext(file.filename)
    if file_extension not in Validator.SUPPORTED_FORMAT:
        raise_422_exception()
    user = await token.check_user_credentials(access_token)
    if not user:
        raise_401_exception()
    file_uuid = await files_repository.create_from_request(file, file_extension, user)
    return file_uuid


@router.get("/{file_uuid}", status_code=status.HTTP_200_OK)
async def download_file(file_uuid: str, access_token: Optional[str] = Header(None)):
    file_record = await file_request_handler(file_uuid, access_token)
    return FileResponse(
        file_record.path, media_type='application/octet-stream', filename=file_record.file_name)


@router.get("/{file_uuid}/format", status_code=status.HTTP_200_OK)
async def get_allowed_formats(file_uuid: str, access_token: Optional[str] = Header(None)):
    file_record = await file_request_handler(file_uuid, access_token)
    available_format = SupportedFormat.get_available_format(file_record.type)
    urls = [f"/files/{file_uuid}/to{export_format}" for export_format in available_format]
    return urls


@router.get("/{file_uuid}/toGEOJSON", response_model=FeatureCollection, status_code=status.HTTP_200_OK)
async def convert_to_geojson(file_uuid: str, access_token: Optional[str] = Header(None)):
    file_record = await file_request_handler(file_uuid, access_token)
    geojson_response = await to_geojson(file_record)
    if not geojson_response:
        raise_422_exception()
    return FeatureCollection.parse_raw(geojson_response)
