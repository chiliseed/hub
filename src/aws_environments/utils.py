import logging

from django.db.models import Q

from aws_environments.models import Service

logger = logging.getLogger(__name__)


def check_if_service_can_be_created(attrs, project):
    """Checks if new service can be created with provided attributes.

    Parameters
    ----------
    attrs : dict
        details of this new service
    project : Project instance

    Returns
    -------
    bool, Option[str]
        (True, None) if service can be created
        (False, "<error reason>") if service cannot be created
    """
    logger.info("Checking if service with this name/subdomain already exists")
    service_exists = Service.objects.filter(
        Q(project=project),
        Q(is_deleted=False),
        Q(name=attrs["name"]) | Q(subdomain=attrs["subdomain"]),
    ).exists()
    is_port_taken = Service.objects.filter(
        Q(project=project),
        Q(is_deleted=False),
        Q(container_port=attrs["container_port"])
        | Q(alb_port_http=attrs["alb_port_http"])
        | Q(alb_port_https=attrs["alb_port_https"]),
    ).exists()

    if service_exists:
        logger.info(
            "Service with this name/subdomain already exists. name=%s subdomain=%s project_id=%s",
            attrs["name"],
            attrs["subdomain"],
            project.id,
        )
        return False, "Service with this name/subdomain already exists."
    elif is_port_taken:
        logger.info(
            "Ports are taken. container_port=%s alb_http_port=%s alb_http_ports=%s project_id=%s",
            attrs["container_port"],
            attrs["alb_port_http"],
            attrs["alb_port_https"],
            project.id,
        )
        return False, "Your other services for this project already took those ports."

    return True, None
