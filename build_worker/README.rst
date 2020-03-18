Build worker tool
=================

Contains the binary that is the brain of build worker server.
Builds and uploads the image to ECR.


How to build a release
======================

`docker pull ekidd/rust-musl-builder`

` ✗ docker run --rm -it -v "$(pwd)":/home/rust/src ekidd/rust-musl-builder cargo build --release`
