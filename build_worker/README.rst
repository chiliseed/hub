Build worker tool
=================

Contains the binary that is the brain of build worker server.
Builds and uploads the image to ECR.


How to build a release
======================

`docker pull ekidd/rust-musl-builder`

` ✗ docker run --rm -it -v "$(pwd)":/home/rust/src ekidd/rust-musl-builder cargo build --release`

Then to upload the release to S3:

`cd target/x86_64-unknown-linux-musl/release`

`tar -zcvf chiliseed-build-worker-0.1.0.tar.gz chiliseed-build-worker`

Go to S3 and upload ^ tarball. Set public read permission.
