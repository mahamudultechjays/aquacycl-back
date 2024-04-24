import datetime
import io
import json

import github
import numpy as np
import pandas as pd

from aquacycl_app import models
from aquacycl_project import constants, settings
from users import models as user_models


def update_site_manifest_log(
    site: user_models.Site, content_file_name: str, content_file: str
):
    content_df = pd.read_csv(io.StringIO(content_file.decode("utf-8")))
    content_df = content_df.replace(np.nan, None)
    content_dict_list = content_df.to_dict(orient="records")
    manifestlog = models.ManifestLog.objects.filter(
        site=site, manifest_file_name=content_file_name
    )
    manifestlog.delete()
    manifest_log_objects = []
    for df_dict in content_dict_list:
        manifest_log_objects.append(
            models.ManifestLog(
                subtopic_bit_no=df_dict[
                    constants.Manifest.SUBTOPIC_BIT_NUMBER
                ],
                subtopic_reported_on=df_dict[
                    constants.Manifest.SUBTOPIC_REPORTED_ON
                ],
                site=site,
                file_version=content_file_name.split("_")[2][:-4],
                manifest_file_name=content_file_name,
                data=df_dict,
            )
        )
    models.ManifestLog.objects.bulk_create(
        manifest_log_objects, batch_size=1000
    )


def update_site_manifest_details():
    auth = github.Auth.Token(settings.GITHUB_TOKEN)
    github_object = github.Github(auth=auth)

    site_manifest_objects = models.SiteManifest.objects.all()
    for site_manifest in site_manifest_objects:

        repo_object = github_object.get_repo(
            f"{site_manifest.owner}/{site_manifest.repo}"
        )

        contents = repo_object.get_contents("")
        csv_files = {}
        csv_file_names = []
        csv_file_hashes = {}
        for content in contents:
            if content.path.endswith(".csv"):
                csv_file_names.append(content.name)
                csv_files[content.name] = content.decoded_content
                latest_commit = content.repository.get_commits(
                    path=content.path
                )[0]
                csv_file_hashes[content.name] = latest_commit.sha

        config = repo_object.get_contents("config.json")
        config_data = json.loads(config.decoded_content)
        production = config_data.get("production", {})
        primary_manifest_file_name = production.get(
            "manifestCSVFilename", None
        )

        site_manifest_version_history_objects = (
            models.SiteManifestVersionHistory.objects.filter(
                site_manifest=site_manifest
            )
        )
        delete_site_manifest_version_history_objects = (
            site_manifest_version_history_objects
        )
        update_site_manifest_version_history_objects = []

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

                if (
                    site_manifest_version_history.latest_commit_hash
                    != csv_file_hashes[
                        site_manifest_version_history.manifest_file_name
                    ]
                ):
                    update_site_manifest_log(
                        site=site_manifest.site,
                        content_file_name=site_manifest_version_history.manifest_file_name,
                        content_file=csv_files[
                            site_manifest_version_history.manifest_file_name
                        ],
                    )
                    site_manifest_version_history.latest_commit_hash = (
                        csv_file_hashes[
                            site_manifest_version_history.manifest_file_name
                        ]
                    )
                site_manifest_version_history.is_primary = (
                    True
                    if site_manifest_version_history.manifest_file_name
                    == primary_manifest_file_name
                    else False
                )
                update_site_manifest_version_history_objects.append(
                    site_manifest_version_history
                )
            else:
                models.ManifestLog.objects.filter(
                    site=site_manifest_version_history.site,
                    manifest_file_name=site_manifest_version_history.manifest_file_name,
                ).delete()

        models.SiteManifestVersionHistory.objects.bulk_update(
            update_site_manifest_version_history_objects,
            ["latest_commit_hash", "is_primary"],
        )
        delete_site_manifest_version_history_objects.delete()
        config_entry = models.SiteConfig.objects.get(
            site_manifest=site_manifest
        )
        config_latest_commit_hash = config.repository.get_commits(
            path=config.path
        )[0].sha
        config_entry.latest_commit_hash = config_latest_commit_hash
        config_entry.save()

        cron_config = models.CronConfig.objects.filter(
            name="cron last run datetime"
        ).first()

        if not cron_config:
            cron_config = models.CronConfig(name="cron last run datetime")
        else:
            cron_config.updated_on = datetime.datetime.utcnow()
        cron_config.save()
