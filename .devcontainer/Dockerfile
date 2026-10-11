FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

RUN find /etc/apt/sources.list.d -type f \
    -exec grep -l "dl.yarnpkg.com" {} + \
    -delete
