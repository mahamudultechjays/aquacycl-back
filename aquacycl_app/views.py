from django.contrib import auth
from rest_framework import response, status, views

from aquacycl_app import controllers, serializers
from aquacycl_project import constants
from tj_packages import custom_pagination
from users import controllers as user_controllers

User = auth.get_user_model()


class Manifest(views.APIView):
    """
    API endpoint to handle validate manifest file link requests.
    """

    def post(self, request):
        user = request.user
        data = request.data
        site_id = data.get("site_id", "")
        site_repo_url = data.get("site_repo_url", "")

        user_controller = user_controllers.UserController()
        user_profile = user_controller.get_user_profile_by_user(user=user)
        if not user_profile.user_type.id == constants.UserTypeNames.ADMIN:
            return response.Response(
                {
                    "result": False,
                    "msg": "Only Admin have access to this API.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if not site_repo_url:
            return response.Response(
                {
                    "result": False,
                    "msg": "Please enter a valid repository link before clicking on the validate button.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not (constants.Manifest.GITHUB_DOMAIN in site_repo_url):
            return response.Response(
                {
                    "result": False,
                    "msg": "Please enter a valid repository link before clicking on the validate button.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not site_id:
            return response.Response(
                {
                    "result": False,
                    "msg": "site id is missing or empty",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        manifest_controller = controllers.ManifestController()

        owner, repo = site_repo_url.split("/")[-2:]
        site = user_controller.get_site_by_id(site_id=site_id)

        if not owner == constants.Manifest.OWNER:
            return response.Response(
                {
                    "result": False,
                    "msg": "Please provide a valid link.",
                    "validation_error_field": "site_repo_url",
                    "validation_error_msg": "Invalid repo owner",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        repo_name_header = repo.split("_")[0]

        if not repo_name_header == constants.Manifest.REPO_NAME_HEADER:
            return response.Response(
                {
                    "result": False,
                    "msg": "Please provide a valid link.",
                    "validation_error_field": "site_repo_url",
                    "validation_error_msg": "Invalid repo header",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        (
            config_data,
            config_name,
            config_latest_commit_hash,
            csv_file_hashes,
            csv_file_names,
            csv_files,
        ) = manifest_controller.fetch_from_github_repo_link(
            owner=owner, repo=repo
        )

        production = config_data.get("production", {})
        customer = production.get("customer", None)
        site_name = production.get("siteName", None)
        primary_manifest_file_name = production.get(
            "manifestCSVFilename", None
        )

        if not (
            customer == site.company.manifest_config_name
            and site_name == site.manifest_config_name
            and primary_manifest_file_name in csv_file_names
        ):
            return response.Response(
                {
                    "result": False,
                    "msg": "Please provide a valid link.",
                    "validation_error_field": "site_repo_url",
                    "validation_error_msg": "Invalid company or site name.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        is_site_repo_entry_exists = (
            manifest_controller.check_if_site_repo_entry_exists(site=site)
        )

        if not is_site_repo_entry_exists:
            site_manifest = manifest_controller.create_site_manifest(
                user=user,
                site=site,
                site_repo_url=site_repo_url,
                owner=owner,
                repo=repo,
            )
            manifest_controller.create_site_manifest_version_history_objects(
                csv_file_names=csv_file_names,
                user=user,
                site_manifest=site_manifest,
                primary_manifest_file_name=primary_manifest_file_name,
                csv_file_hashes=csv_file_hashes,
            )
            manifest_controller.create_manifest_log_objects(
                csv_files=csv_files,
                site=site,
            )
            manifest_controller.create_config(
                site_manifest=site_manifest,
                config_name=config_name,
                config_latest_commit_hash=config_latest_commit_hash,
            )

        else:
            site_manifest = manifest_controller.get_site_manifest(site=site)

            if site_manifest.site_repo_url != site_repo_url:
                site_manifest = manifest_controller.update_site_manifest(
                    user=user,
                    site_manifest=site_manifest,
                    site_repo_url=site_repo_url,
                    owner=owner,
                    repo=repo,
                )
                manifest_controller.delete_site_manifest_version_history(
                    site_manifest=site_manifest
                )
                manifest_controller.create_site_manifest_version_history_objects(
                    csv_file_names=csv_file_names,
                    user=user,
                    site_manifest=site_manifest,
                    primary_manifest_file_name=primary_manifest_file_name,
                    csv_file_hashes=csv_file_hashes,
                )
                manifest_controller.update_site_manifest_log(
                    csv_files=csv_files, site=site
                )
                manifest_controller.delete_config(site_manifest=site_manifest)
                manifest_controller.create_config(
                    site_manifest=site_manifest,
                    config_name=config_name,
                    config_latest_commit_hash=config_latest_commit_hash,
                )

            else:
                manifest_controller.update_site_manifest_version_history(
                    user=user,
                    csv_file_names=csv_file_names,
                    site_manifest=site_manifest,
                    primary_manifest_file_name=primary_manifest_file_name,
                    csv_file_hashes=csv_file_hashes,
                )
                manifest_controller.update_site_manifest_log(
                    csv_files=csv_files,
                    site=site,
                )
                manifest_controller.update_config(
                    site_manifest=site_manifest,
                    config_latest_commit_hash=config_latest_commit_hash,
                )

        return response.Response(
            {
                "result": True,
                "msg": "Manifest file validated successfully.",
                "data": data,
            },
            status=status.HTTP_201_CREATED,
        )

    def get(self, request):
        user = request.user
        query_params = request.query_params

        user_controller = user_controllers.UserController()
        user_profile = user_controller.get_user_profile_by_user(user=user)
        if not user_profile.user_type.id == constants.UserTypeNames.ADMIN:
            return response.Response(
                {
                    "result": False,
                    "msg": "Only Admin have access to this API.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        site_id = query_params.get("site_id", "")

        if not site_id:
            return response.Response(
                {
                    "result": False,
                    "msg": "site id missing or empty.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        site = user_controller.get_site_by_id(site_id=site_id)

        manifest_controller = controllers.ManifestController()

        site_manifest = manifest_controller.get_site_manifest(site=site)

        data = {
            "site_repo_url": site_manifest.site_repo_url
            if site_manifest is not None
            else None,
        }

        return response.Response(
            {
                "result": True,
                "msg": "Success",
                "data": data,
            },
            status=status.HTTP_200_OK,
        )


class ManifestHistory(views.APIView):
    """
    API endpoint to handle manifest history table requests.
    """

    def get(self, request):
        user = request.user
        query_params = request.query_params

        user_controller = user_controllers.UserController()
        user_profile = user_controller.get_user_profile_by_user(user=user)
        if not user_profile.user_type.id == constants.UserTypeNames.ADMIN:
            return response.Response(
                {
                    "result": False,
                    "msg": "Only Admin have access to this API.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        site_id = query_params.get("site_id", "")
        limit = query_params.get("limit", "")
        offset = query_params.get("offset", 0)

        if not site_id:
            site = user_profile.site_preference
            preference_company_id = site.company.id if site else None
            preference_site_id = site.id if site else None
        else:
            site = user_controller.get_site_by_id(site_id=site_id)
            preference_company_id = None
            preference_site_id = None

        if not limit:
            return response.Response(
                {
                    "result": False,
                    "msg": "limit is required.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        manifest_controller = controllers.ManifestController()

        site_manifest = manifest_controller.get_site_manifest(site=site)

        site_manifest_version_history_objects = (
            manifest_controller.get_site_manifest_version_history(
                site_manifest=site_manifest,
            )
        )

        pagination = custom_pagination.Pagination()
        serialized_data, next_link = pagination.get_paginated_response(
            site_manifest_version_history_objects,
            offset,
            limit,
            serializers.ManifestHistorySerializer,
        )

        return response.Response(
            {
                "result": True,
                "msg": "Success",
                "preference_company_id": preference_company_id,
                "preference_site_id": preference_site_id,
                "version_history_count": site_manifest_version_history_objects.count(),
                "next_link": next_link,
                "data": serialized_data,
            },
            status=status.HTTP_200_OK,
        )
