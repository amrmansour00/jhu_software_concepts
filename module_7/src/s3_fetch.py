"""Download the GradCafe seed dataset from Amazon S3."""

import argparse
import os
from pathlib import Path

import boto3


def get_s3_client():
    """Create an S3 client using the active AWS credential chain."""
    return boto3.client("s3")


def download_from_s3(bucket, key, destination, client=None):
    """Download one S3 object to a local destination."""
    destination_path = Path(destination)
    destination_path.parent.mkdir(parents=True, exist_ok=True)

    s3_client = client or get_s3_client()

    s3_client.download_file(
        bucket,
        key,
        str(destination_path),
    )

    return destination_path


def main():
    """Download the configured GradCafe dataset from S3."""
    parser = argparse.ArgumentParser(
        description="Download GradCafe applicant data from Amazon S3."
    )
    parser.add_argument(
        "--bucket",
        default=os.getenv("S3_BUCKET"),
        help="S3 bucket name. Defaults to S3_BUCKET.",
    )
    parser.add_argument(
        "--key",
        default=os.getenv("S3_KEY", "applicant_data.json"),
        help="S3 object key.",
    )
    parser.add_argument(
        "--destination",
        default=os.getenv(
            "S3_DESTINATION",
            "ec2/src/data/applicant_data.json",
        ),
        help="Local destination path.",
    )

    args = parser.parse_args()

    if not args.bucket:
        parser.error(
            "S3 bucket is required. "
            "Provide --bucket or set S3_BUCKET."
        )

    output = download_from_s3(
        args.bucket,
        args.key,
        args.destination,
    )

    print(f"Downloaded s3://{args.bucket}/{args.key} to {output}")


if __name__ == "__main__":
    main()