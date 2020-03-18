#[macro_use]
extern crate log;

use std::path::Path;
use std::process::{Command, Stdio, exit};
use std::env;

use rusoto_ecr::{EcrClient, Ecr, DescribeImagesRequest, ImageIdentifier};
use rusoto_core::Region;
use tokio;

// Wrapper for executing commands in user shell. All output is sent to user shell
fn exec_command(cmd: &str, args: Vec<&str>) -> bool {
    println!("{} {:?}", cmd, args);
    let mut cli_command = match Command::new(cmd)
        .args(&args)
        .stdin(Stdio::inherit())
        .stdout(Stdio::inherit())
        .stderr(Stdio::inherit())
        .spawn()
    {
        Err(err) => panic!("Error spawning: {}", err.to_string()),
        Ok(process) => process,
    };

    cli_command.wait().unwrap().success()
}

#[tokio::main]
async fn is_ecr_contains_image_tag(tag: &str, ecr_url: &str) -> bool {
    let client = EcrClient::new(Region::default());
    let repo_parts: Vec<&str> = ecr_url.split(".com/").collect();

    info!("Checking if image tag {} exists in repo {}", tag, repo_parts[1]);

    match client.describe_images(DescribeImagesRequest {
        filter: None,
        image_ids: Some(vec![ImageIdentifier { image_digest: None, image_tag: Some(tag.to_string()) }]),
        max_results: None,
        next_token: None,
        registry_id: None,
        repository_name: repo_parts[1].to_string(),
    }).await {
        Ok(r) => {
            return r.image_details.is_some()
        }
        Err(err) => {
            debug!("Error checking if image exists: {}", err.to_string());
            return false
        }
    };
}

const DEPLOYMENT_ROOT: &str = "/home/ubuntu/deployment/build";

fn main() {
    pretty_env_logger::try_init_custom_env("CHILISEED_LOG")
        .expect("Cannot initialize the logger that was already initialized.");

    let here = env::current_dir().unwrap();
    let env = env::var("CHILISEED_ENV").unwrap();
    let version = env::var("CHILISEED_VERSION").unwrap();
    let dockerfile_target = match env::var("DOCKERFILE_TARGET") {
        Ok(val) => Some(val),
        Err(err) => {
            debug!("Error getting dockerfile target: {}", err);
            None
        },
    };
    let service_name = env::var("CHILISEED_SERVICE_NAME").unwrap();
    let build_version = format!("{}:{}", service_name, version);
    let ecr_url = env::var("CHILISEED_ECR_URL").unwrap();
    let repo = format!("{}:{}", ecr_url, version);

    info!("Starting build in pwd: {}", here.display());
    info!("Deploying version {} for service {} in environment {}", version, service_name, env);

    if !Path::new(DEPLOYMENT_ROOT).exists() {
        error!("Deployment path does not exist. Creating: {}", DEPLOYMENT_ROOT);
        exit(1);
    }

    if !Path::new(&Path::new(DEPLOYMENT_ROOT).join("Dockerfile")).exists() {
        error!("Deployment dir has no dockerfile");
        exit(1);
    }

    if is_ecr_contains_image_tag(&version, &ecr_url) {
        info!("Image tag {} already exists in repo.", version);
        return;
    }

    let aws_login = format!("aws ecr get-login-password | docker login --username AWS --password-stdin {}", ecr_url);
    let deployment_start = vec!["docker --version", &aws_login];

    let docker_tag = format!("docker tag {} {}", build_version, repo);
    let docker_push = format!("docker push {}", repo);
    let push_image = vec![docker_tag, docker_push];


    let mut build = Vec::new();
    if let Some(dockerfile_target_state) = dockerfile_target {
        let docker_build = format!("docker build --target {} -t {} {}", dockerfile_target_state, build_version, DEPLOYMENT_ROOT);
        build.push(docker_build.clone());
        build.extend(push_image.iter().cloned());
    } else {
        build.push(format!("docker build -t {} {}", build_version, DEPLOYMENT_ROOT));
        build.extend(push_image.iter().cloned());
    }

    for cmd in deployment_start {
        if !exec_command("/usr/bin/sh", vec!["-c", cmd]) {
            error!("Failed to execute: {}", cmd);
            exit(1)
        }
    }

    for cmd in &build {
        if !exec_command("/usr/bin/sh", vec!["-c", cmd]) {
            error!("Failed to execute: {}", cmd);
            exit(1)
        }
    }

    info!("Image tag {} successfully pushed", version);
}
