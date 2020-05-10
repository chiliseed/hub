#[macro_use]
extern crate log;

use std::path::Path;
use std::process::{Command, Stdio, exit};
use std::env;

use rusoto_ecr::{EcrClient, Ecr, DescribeImagesRequest, ImageIdentifier};
use rusoto_core::Region;
use tokio;
use structopt::StructOpt;

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

async fn is_ecr_contains_image_tag(tag: &str, ecr_url: &str) -> bool {
    let client = EcrClient::new(Region::default());
    let repo_parts: Vec<&str> = ecr_url.split(".com/").collect();

    info!("Checking if image tag {} exists in repo {}", tag, repo_parts[1]);

    return match client.describe_images(DescribeImagesRequest {
        filter: None,
        image_ids: Some(vec![ImageIdentifier { image_digest: None, image_tag: Some(tag.to_string()) }]),
        max_results: None,
        next_token: None,
        registry_id: None,
        repository_name: repo_parts[1].to_string(),
    }).await {
        Ok(r) => {
            r.image_details.is_some()
        }
        Err(err) => {
            debug!("Error checking if image exists: {}", err.to_string());
            false
        }
    };
}

const DEPLOYMENT_ROOT: &str = "/home/ubuntu/deployment/build";

#[derive(Debug, StructOpt)]
#[structopt(name = "chiliseed-build-worker", about = "Image builder.")]
struct Opts {
    /// Optional build argument that will be passed to `docker build` command
    #[structopt(long)]
    build_arg: Option<Vec<String>>,
    /// Short git sha of the version to be deployed
    #[structopt(short = "-v", env = "CHILISEED_VERSION")]
    version: String,
}

fn main() {
    pretty_env_logger::try_init_custom_env("CHILISEED_LOG")
        .expect("Cannot initialize the logger that was already initialized.");

    let opts = Opts::from_args();
    info!("Building with arguments: {:?}", opts);

    let here = env::current_dir().unwrap();
    let env = env::var("CHILISEED_ENV").unwrap();
    let dockerfile = env::var("CHILISEED_DOCKERFILE").unwrap();
    let dockerfile_target = match env::var("CHILISEED_DOCKERFILE_TARGET") {
        Ok(val) => Some(val),
        Err(err) => {
            debug!("Error getting dockerfile target: {}", err);
            None
        },
    };
    let service_name = env::var("CHILISEED_SERVICE_NAME").unwrap();
    let build_version = format!("{}:{}", service_name, opts.version);
    let ecr_url = env::var("CHILISEED_ECR_URL").unwrap();
    let repo = format!("{}:{}", ecr_url, opts.version);

    info!("Starting build in pwd: {}", here.display());
    info!("Deploying version {} for service {} in environment {}", opts.version, service_name, env);

    if !Path::new(DEPLOYMENT_ROOT).exists() {
        error!("Deployment path does not exist. Creating: {}", DEPLOYMENT_ROOT);
        exit(1);
    }

    if !Path::new(&Path::new(DEPLOYMENT_ROOT).join(dockerfile.clone())).exists() {
        error!("Deployment dir has no dockerfile");
        exit(1);
    }

    let dockerfile_path = Path::new(DEPLOYMENT_ROOT).join(dockerfile);
    let dockerfile_path_buf = dockerfile_path.canonicalize().unwrap();
    let absolute_dockerfile_path = dockerfile_path_buf.to_str().unwrap();

    let mut async_runtime = tokio::runtime::Runtime::new().unwrap();
    let async_is_ecr_contains_image_tag = is_ecr_contains_image_tag(&opts.version, &ecr_url);
    let tag_exist = async_runtime.block_on(async_is_ecr_contains_image_tag);
    if tag_exist {
        info!("Image tag {} already exists in repo.", opts.version);
        return;
    } else {
        info!("Creating image");
    }

    let aws_login = format!("aws ecr get-login-password | docker login --username AWS --password-stdin {}", ecr_url);
    let deployment_start = vec!["docker --version", &aws_login];

    let docker_tag = format!("docker tag {} {}", build_version, repo);
    let docker_push = format!("docker push {}", repo);
    let push_image = vec![docker_tag, docker_push];

    let mut build = Vec::new();
    let mut docker_build = String::from("docker build");
    if let Some(dockerfile_target_state) = dockerfile_target {
        docker_build.push_str(&format!(
            " --target {} -t {} -f {} {}",
            dockerfile_target_state,
            build_version,
            absolute_dockerfile_path,
            DEPLOYMENT_ROOT
        ));
    } else {
        docker_build.push_str(&format!(" -t {} -f {} {}", build_version, absolute_dockerfile_path , DEPLOYMENT_ROOT));
    }

    if let Some(build_args) = opts.build_arg {
        for build_arg in build_args {
            let param = format!(" --build-arg {}", build_arg);
            docker_build.push_str(&param);
        }
    }

    build.push(docker_build);
    build.extend(push_image.iter().cloned());

    for cmd in deployment_start {
        if !exec_command("/bin/sh", vec!["-c", cmd]) {
            error!("Failed to execute: {}", cmd);
            exit(1)
        }
    }

    for cmd in &build {
        if !exec_command("/bin/sh", vec!["-c", cmd]) {
            error!("Failed to execute: {}", cmd);
            exit(1)
        }
    }

    info!("Image tag {} successfully pushed", opts.version);
}
