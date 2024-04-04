#!/bin/bash

set -e

export PB_REPO=${1}
if [ ! -d ${PB_REPO} ] || [ -z ${PB_REPO} ]; then export PB_REPO=/mnt/p0/Personal/protobuf/src; fi
if [ -z ${PROTOC} ]; then export PROTOC=protoc; fi
export FLAGS="${FLAGS} -I${PB_REPO}"

export SOURCES_PB="google/protobuf/any.proto google/protobuf/api.proto google/protobuf/descriptor.proto google/protobuf/duration.proto google/protobuf/empty.proto google/protobuf/field_mask.proto google/protobuf/source_context.proto google/protobuf/struct.proto google/protobuf/timestamp.proto google/protobuf/type.proto google/protobuf/wrappers.proto google/protobuf/compiler/plugin.proto"

export OUT_LIB=src/betterproto/lib
export OUT_LIB_PYDANTIC=${OUT_LIB}/pydantic
export OUT_LIB_STD=${OUT_LIB}/std

mkdir -p ${OUT_LIB_PYDANTIC} ${OUT_LIB_STD}
touch ${OUT_LIB_PYDANTIC}/__init__.py ${OUT_LIB_STD}/__init__.py

export PBS=$(for pb_pkg_path in ${SOURCES_PB}; do echo "${PB_REPO}/${pb_pkg_path}"; done)

${PROTOC} ${FLAGS} \
    --python_betterproto_opt=pydantic_dataclasses,INCLUDE_GOOGLE \
    --python_betterproto_out=${OUT_LIB_PYDANTIC} \
    ${PBS}

${PROTOC} ${FLAGS} \
    --python_betterproto_opt=INCLUDE_GOOGLE \
    --python_betterproto_out=${OUT_LIB_STD} \
    ${PBS}