import datetime
import io
import json

import github
import numpy as np
import pandas as pd
from rest_framework import exceptions, serializers

from aquacycl_app import models
from aquacycl_project import constants, settings
from users import models as users_models


class ManifestController:
    def fetch_from_github_repo_link(self, owner: str, repo: str) -> tuple:
        """
        To fetch a repository based on the owner and repo name
        Params:
            owner: owner or organization of the repository
            repo: name of the repository
        Returns:
            config_data: configuration metadata for the site from the repository
            csv_file_names: list of names of csv files
            csv_files: dictionary of csv files with name as key and content dataframe as value
        """
        auth = github.Auth.Token(settings.GITHUB_TOKEN)
        github_object = github.Github(auth=auth)
        try:
            repo_object = github_object.get_repo(f"{owner}/{repo}")
            config = repo_object.get_contents("config.json")
            contents = repo_object.get_contents("")
        except github.UnknownObjectException:
            raise exceptions.NotFound(
                {
                    "result": False,
                    "msg": "Please provide a valid link.",
                    "validation_error_msg": "Repository or content not found.",
                },
                code="not_found",
            )
        except github.BadCredentialsException:
            raise exceptions.AuthenticationFailed(
                {
                    "result": False,
                    "msg": "Invalid or expired credentials.",
                },
                code="authentication_failed",
            )
        except github.BadUserAgentException:
            raise exceptions.PermissionDenied(
                {
                    "result": False,
                    "msg": "Bad user agent header.",
                },
                code="permission_denied",
            )
        except github.RateLimitExceededException:
            raise serializers.ValidationError(
                {
                    "result": False,
                    "msg": "Rate limit exceeded. Please try again later.",
                },
                code="validation_error",
            )
        config_data = json.loads(config.decoded_content)
        config_name = config.name
        config_latest_commit_hash = config.repository.get_commits(
            path=config.path
        )[0].sha
        csv_files = {}
        csv_file_hashes = {}
        csv_file_names = []
        for content in contents:
            if content.path.endswith(".csv"):
                csv_file_names.append(content.name)
                try:
                    csv_df = pd.read_csv(
                        io.StringIO(content.decoded_content.decode("utf-8"))
                    )
                except pd.errors.EmptyDataError:
                    raise serializers.ValidationError(
                        {
                            "result": False,
                            "msg": "Please check the file and try again.",
                        },
                        code="validation_error",
                    )
                if len(csv_df) == 0:
                    raise serializers.ValidationError(
                        {
                            "result": False,
                            "msg": "Plase check the file and try again.",
                            "validation_error_field": "",
                        },
                        code="validation_error",
                    )
                csv_files[content.name] = csv_df
                latest_commit = content.repository.get_commits(
                    path=content.path
                )[0]
                csv_file_hashes[content.name] = latest_commit.sha

        return (
            config_data,
            config_name,
            config_latest_commit_hash,
            csv_file_hashes,
            csv_file_names,
            csv_files,
        )

    def check_if_site_repo_entry_exists(
        self,
        site: models.User,
    ) -> bool:
        """
        To check if an entry in SiteManifest table exists for the given site
        Params:
            site: site object for the given site
        Returns:
            bool: True if the entry exists, False otherwise
        """
        return models.SiteManifest.objects.filter(site=site).exists()

    def create_site_manifest(
        self,
        user: users_models.User,
        site: users_models.Site,
        site_repo_url: str,
        owner: str,
        repo: str,
    ) -> models.SiteManifest:
        """
        To create a site manifest entry for the given site and manifest repository
        Params:
            user: Admin user who posted the repository URL
            site: Site for the given repository URL
            site_repo_url: Repository URL
            owner: Github user or organization that owns the repository
            repo: Repository name
        Returns:
            site_manifest: created site manifest entry
        """
        return models.SiteManifest.objects.create(
            admin_user=user,
            site=site,
            site_repo_url=site_repo_url,
            owner=owner,
            repo=repo,
        )

    def create_site_manifest_version_history_objects(
        self,
        csv_file_names: list,
        user: users_models.User,
        site_manifest: models.SiteManifest,
        primary_manifest_file_name: str,
        csv_file_hashes: dict,
    ):
        """
        To create manifest version history entries for the files in the repository
        Params:
            csv_file_names: List of file names of csv files in the repository
            user: admin user who initiated the request
            site_manifest: Site manifest entry associated with the repository
            primary_manifest_file_name: Name of the primary manifest file under use
            csv_file_hashes: dictionary of latest commit hashes of each csv file with csv file name as key

        Returns:
            None
        """
        manifest_version_history_objects = list(
            map(
                lambda name: models.SiteManifestVersionHistory(
                    added_by=user,
                    site_manifest=site_manifest,
                    validated_date=datetime.datetime.utcnow(),
                    file_version=name.split("_")[2][:-4],
                    manifest_file_name=name,
                    is_primary=True
                    if name == primary_manifest_file_name
                    else False,
                    latest_commit_hash=csv_file_hashes[name],
                ),
                csv_file_names,
            )
        )
        models.SiteManifestVersionHistory.objects.bulk_create(
            manifest_version_history_objects
        )

    def create_manifest_log_objects(
        self,
        csv_files: dict,
        site: users_models.Site,
    ):
        """
        To create manifest log entries from the fetched csv files
        Params:
            csv_file_names: dictionary with csv file names as keys and csv files byte content as values
            site: Site for the given repository URL
        Returns:
            None
        """
        manifest_log_objects = []
        for name, content_df in csv_files.items():
            content_df = content_df.replace(np.nan, None)
            df_dict_list = content_df.to_dict(orient="records")
            for df_dict in df_dict_list:
                manifest_log_objects.append(
                    models.ManifestLog(
                        subtopic_bit_no=df_dict[
                            constants.Manifest.SUBTOPIC_BIT_NUMBER
                        ],
                        subtopic_reported_on=df_dict[
                            constants.Manifest.SUBTOPIC_REPORTED_ON
                        ],
                        site=site,
                        file_version=name.split("_")[2][:-4],
                        manifest_file_name=name,
                        data=df_dict,
                    )
                )

        models.ManifestLog.objects.bulk_create(
            manifest_log_objects, batch_size=1000
        )

    def get_site_manifest(
        self, site: users_models.Site
    ) -> models.SiteManifest:
        """
        To retrieve the site manifest entry for a given site
        Params:
            site: site for the given repository URL
        Returns:
            site_manifest: site_manifest object for the given site
        """
        return models.SiteManifest.objects.filter(site=site).first()

    def update_site_manifest_version_history(
        self,
        user: users_models.User,
        csv_file_names: list,
        site_manifest: models.SiteManifest,
        primary_manifest_file_name: str,
        csv_file_hashes: dict,
    ):
        """
        To update the site manifest version history entries for a given site manifest and csv files fetched from repo
        Params:
            user: admin user who initiated the validation process
            csv_file_names: list of names of csv files fetched from repository
            site_manifest: models.SiteManifest object for the given site
            primary_manifest_file_name: Name of the primary manifest file under use
            csv_file_hashes: dictionary of latest commit hashes of each csv file with csv file name as key

        Returns:
            None
        """

        site_manifest_version_history_objects = (
            models.SiteManifestVersionHistory.objects.filter(
                site_manifest=site_manifest,
            )
        )
        existing_site_manifest_version_history_names = []
        existing_site_manifest_version_history_objects = []
        delete_site_manifest_version_history_objects = (
            site_manifest_version_history_objects
        )

        for (
            site_manifest_version_history
        ) in site_manifest_version_history_objects:
            if (
                site_manifest_version_history.manifest_file_name
                in csv_file_names
            ):
                delete_site_manifest_version_history_objects = (
                    delete_site_manifest_version_history_objects.exclude(
                        id=site_manifest_version_history.id
                    )
                )
                existing_site_manifest_version_history_names.append(
                    site_manifest_version_history.manifest_file_name
                )
                site_manifest_version_history.is_primary = (
                    True
                    if site_manifest_version_history.manifest_file_name
                    == primary_manifest_file_name
                    else False
                )
                site_manifest_version_history.latest_commit_hash = (
                    csv_file_hashes[
                        site_manifest_version_history.manifest_file_name
                    ]
                )
                existing_site_manifest_version_history_objects.append(
                    site_manifest_version_history
                )
        difference_list = list(
            set(csv_file_names)
            - set(existing_site_manifest_version_history_names)
        )

        delete_site_manifest_version_history_objects.delete()
        models.SiteManifestVersionHistory.objects.bulk_update(
            existing_site_manifest_version_history_objects,
            ["is_primary", "latest_commit_hash"],
        )
        self.create_site_manifest_version_history_objects(
            csv_file_names=difference_list,
            user=user,
            site_manifest=site_manifest,
            primary_manifest_file_name=primary_manifest_file_name,
            csv_file_hashes=csv_file_hashes,
        )

    def update_site_manifest_log(
        self,
        csv_files: dict,
        site: users_models.Site,
    ):
        """
        To update site manifest log with the data from csv files
        Params:
            csv_files: dictionary with csv file names as key and content as value
            site: site for the given repository URL
        Returns:
            None
        """
        manifest_log_objects = models.ManifestLog.objects.filter(site=site)
        manifest_log_objects.delete()
        self.create_manifest_log_objects(
            csv_files=csv_files,
            site=site,
        )

    def update_site_manifest(
        self,
        user: users_models.User,
        site_manifest: models.SiteManifest,
        site_repo_url: str,
        owner: str,
        repo: str,
    ) -> models.SiteManifest:
        """
        Params:
            user: The admin user who initiated the request
            site_manifest: The site manifest object for the given site
            site_repo_url: The new site repository URL
            owner: The repository owner extracted from the repository URL
            repo: The repository name extracted from the repository URL
        Returns:
            site_manifest: The updated site manifest object
        """
        site_manifest.admin_user = user
        site_manifest.site_repo_url = site_repo_url
        site_manifest.owner = owner
        site_manifest.repo = repo
        site_manifest.save()
        return site_manifest

    def delete_site_manifest_version_history(
        self, site_manifest: models.SiteManifest
    ):
        """
        To delete all the site manifest version history entries for the given site manifest
        Params:
            site_manifest: Site manifest object for the given site
        Returns:
            None
        """
        site_manifest_version_history_objects = (
            models.SiteManifestVersionHistory.objects.filter(
                site_manifest=site_manifest
            )
        )
        site_manifest_version_history_objects.delete()

    def get_site_manifest_version_history(
        self,
        site_manifest: models.SiteManifest,
    ) -> models.SiteManifestVersionHistory:
        """
        To get the queryset of manifest files for a given site
        Params:
            site_manifest: site manifest object for the given site
        Returns:
            site_manifest_version_history: queryset of manifest files for a given site
        """
        return (
            models.SiteManifestVersionHistory.objects.select_related(
                "added_by",
                "site_manifest",
                "site_manifest__site",
                "site_manifest__site__company",
            )
            .filter(site_manifest=site_manifest)
            .order_by("-file_version")
        )

    def create_config(
        self,
        site_manifest: models.SiteManifest,
        config_name: str,
        config_latest_commit_hash: str,
    ):
        """
        To create an entry for the config file for a given site repository
        Params:
            site_manifest: The site manifest for the given site repository
            config_name: The name of the config file
            config_latest_commit_hash: The latest commit hash for the config file
        Returns:
            None
        """
        site_config = models.SiteConfig(
            site_manifest=site_manifest,
            config_name=config_name,
            latest_commit_hash=config_latest_commit_hash,
        )
        site_config.save()

    def delete_config(
        self,
        site_manifest: models.SiteManifest,
    ):
        """
        To delete a config file entry for the given site manifest of a site
        Params:
            site_manifest: The site manifest for the given site repository
        Returns:
            None
        """
        models.SiteConfig.objects.filter(site_manifest=site_manifest).delete()

    def update_config(
        self,
        site_manifest: models.SiteManifest,
        config_latest_commit_hash: str,
    ):
        """
        To update the config file entry for the given site manifest of a site
        Params:
            site_manifest: The site manifest for the given site repository
            config_latest_commit_hash: The latest commit hash for the config file
        Returns:
            None
        """
        site_config = models.SiteConfig.objects.get(
            site_manifest=site_manifest
        )
        site_config.latest_commit_hash = config_latest_commit_hash
        site_config.save()
