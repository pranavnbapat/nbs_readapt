from __future__ import annotations

from django.conf import settings
from django.core.management.base import BaseCommand
from opensearchpy import helpers

from apps.repository.models import RepositoryRecord
from apps.search.indexing import build_index_body, build_record_document
from apps.search.opensearch import get_opensearch_client


class Command(BaseCommand):
    help = "Index normalized repository records from PostgreSQL into OpenSearch."

    def add_arguments(self, parser):
        parser.add_argument(
            "--recreate",
            action="store_true",
            help="Delete and recreate the BM25 index before indexing.",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=200,
            help="Database iterator chunk size.",
        )
        parser.add_argument(
            "--dataset",
            action="append",
            default=[],
            help="Limit indexing to one or more dataset keys.",
        )

    def handle(self, *args, **options):
        index_name = settings.OPENSEARCH["index_bm25"]
        client = get_opensearch_client()

        if options["recreate"] and client.indices.exists(index=index_name):
            client.indices.delete(index=index_name)
            self.stdout.write(f"Deleted index: {index_name}")

        if not client.indices.exists(index=index_name):
            client.indices.create(index=index_name, body=build_index_body())
            self.stdout.write(f"Created index: {index_name}")

        queryset = (
            RepositoryRecord.objects.all()
            .prefetch_related(
                "countries",
                "primary_hazards",
                "secondary_hazards",
                "primary_nbs_types",
                "secondary_nbs_types",
            )
            .order_by("id")
        )
        if options["dataset"]:
            queryset = queryset.filter(source_dataset__in=options["dataset"])

        def actions():
            for record in queryset.iterator(chunk_size=options["batch_size"]):
                yield {
                    "_op_type": "index",
                    "_index": index_name,
                    "_id": f"record-{record.id}",
                    "_source": build_record_document(record),
                }

        success_count, _ = helpers.bulk(client, actions(), request_timeout=300)
        client.indices.refresh(index=index_name)
        self.stdout.write(self.style.SUCCESS(f"Indexed {success_count} records into {index_name}."))
