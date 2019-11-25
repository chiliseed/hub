import os

from control_center.settings import BASE_DIR

INFRA_DIR = os.path.join(BASE_DIR, "infra_executors")
TERRAFORM_DIR = os.path.join(INFRA_DIR, "terraform")
EXEC_LOGS_DIR = os.path.join(INFRA_DIR, "exec_logs")
TERRAFORM_PLUGIN_DIR = os.path.join("~", ".terraform.d", "plugins")
