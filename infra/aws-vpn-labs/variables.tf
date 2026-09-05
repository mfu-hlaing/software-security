variable "aws_region" {
  description = "AWS Region for the isolated pilot account."
  type        = string
  default     = "ap-southeast-1"
}

variable "availability_zone" {
  description = "Optional single AZ. Empty selects the first available AZ; the pilot deliberately accepts single-AZ availability to control cost."
  type        = string
  default     = ""
}

variable "project_name" {
  description = "Short resource/tag prefix."
  type        = string
  default     = "software-security-labs"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,30}$", var.project_name))
    error_message = "project_name must be 3-31 lowercase letters, numbers, or hyphens."
  }
}

variable "vpc_cidr" {
  description = "Dedicated training VPC; must not overlap student home/campus networks or the WireGuard client network."
  type        = string
  default     = "10.60.0.0/16"

  validation {
    condition     = can(cidrnetmask(var.vpc_cidr))
    error_message = "vpc_cidr must be an IPv4 CIDR."
  }
}

variable "edge_subnet_cidr" {
  type        = string
  description = "Public subnet containing only the WireGuard/NAT edge."
  default     = "10.60.0.0/24"

  validation {
    condition     = can(cidrhost(var.edge_subnet_cidr, 10))
    error_message = "edge_subnet_cidr must be an IPv4 CIDR with host index 10 available."
  }
}

variable "team_1_subnet_cidr" {
  type        = string
  description = "Private subnet dedicated to team one."
  default     = "10.60.10.0/24"

  validation {
    condition     = can(cidrhost(var.team_1_subnet_cidr, 10))
    error_message = "team_1_subnet_cidr must be an IPv4 CIDR with host index 10 available."
  }
}

variable "team_2_subnet_cidr" {
  type        = string
  description = "Private subnet dedicated to team two."
  default     = "10.60.20.0/24"

  validation {
    condition     = can(cidrhost(var.team_2_subnet_cidr, 10))
    error_message = "team_2_subnet_cidr must be an IPv4 CIDR with host index 10 available."
  }
}

variable "wireguard_cidr" {
  type        = string
  description = "WireGuard client network."
  default     = "10.66.0.0/24"

  validation {
    condition     = can(cidrnetmask(var.wireguard_cidr))
    error_message = "wireguard_cidr must be an IPv4 CIDR."
  }
}

variable "wireguard_server_address" {
  type        = string
  description = "WireGuard interface address in CIDR form."
  default     = "10.66.0.1/24"

  validation {
    condition     = can(cidrnetmask(var.wireguard_server_address))
    error_message = "wireguard_server_address must be an IPv4 address with CIDR prefix."
  }
}

variable "wireguard_port" {
  type        = number
  description = "Public UDP listen port."
  default     = 51820

  validation {
    condition     = var.wireguard_port >= 1024 && var.wireguard_port <= 65535
    error_message = "wireguard_port must be between 1024 and 65535."
  }
}

variable "wireguard_source_cidrs" {
  type        = set(string)
  description = "Public source ranges allowed to initiate WireGuard. 0.0.0.0/0 supports roaming students; narrow it when addresses are stable."
  default     = ["0.0.0.0/0"]

  validation {
    condition     = alltrue([for value in var.wireguard_source_cidrs : can(cidrnetmask(value))])
    error_message = "Every wireguard_source_cidrs value must be an IPv4 CIDR."
  }
}

variable "instructor_wireguard_public_key" {
  type        = string
  description = "Instructor device WireGuard PUBLIC key. Generate the private key on that device; never pass it to Terraform."
  sensitive   = false

  validation {
    condition     = can(regex("^[A-Za-z0-9+/]{43}=$", var.instructor_wireguard_public_key))
    error_message = "instructor_wireguard_public_key must be a WireGuard base64 public key, not a private key or config."
  }
}

variable "instructor_wireguard_cidr" {
  type        = string
  description = "Fixed instructor tunnel identity."
  default     = "10.66.0.2/32"

  validation {
    condition     = can(regex("/32$", var.instructor_wireguard_cidr)) && can(cidrnetmask(var.instructor_wireguard_cidr))
    error_message = "instructor_wireguard_cidr must be one IPv4 /32."
  }
}

variable "team_1_peer_cidrs" {
  type        = set(string)
  description = "Fixed WireGuard /32 slots authorized to team one's HTTPS host. Add public keys later with scripts/onboard-peer.sh."
  default     = ["10.66.0.10/32", "10.66.0.11/32", "10.66.0.12/32", "10.66.0.13/32"]

  validation {
    condition     = length(var.team_1_peer_cidrs) > 0 && alltrue([for value in var.team_1_peer_cidrs : can(regex("/32$", value)) && can(cidrnetmask(value))])
    error_message = "Every team_1_peer_cidrs value must be an IPv4 /32."
  }
}

variable "team_2_peer_cidrs" {
  type        = set(string)
  description = "Fixed WireGuard /32 slots authorized to team two's HTTPS host."
  default     = ["10.66.0.20/32", "10.66.0.21/32", "10.66.0.22/32", "10.66.0.23/32"]

  validation {
    condition     = length(var.team_2_peer_cidrs) > 0 && alltrue([for value in var.team_2_peer_cidrs : can(regex("/32$", value)) && can(cidrnetmask(value))])
    error_message = "Every team_2_peer_cidrs value must be an IPv4 /32."
  }
}

variable "instructor_ssh_public_key" {
  type        = string
  description = "Instructor SSH PUBLIC key. SSH is reachable only inside the instructor WireGuard tunnel."

  validation {
    condition     = can(regex("^(ssh-ed25519|ecdsa-sha2-nistp256|ssh-rsa) [A-Za-z0-9+/=]+(?: .*)?$", trimspace(var.instructor_ssh_public_key)))
    error_message = "instructor_ssh_public_key must be a valid OpenSSH public key line."
  }
}

variable "ubuntu_ami_id" {
  type        = string
  description = "Explicit Ubuntu 24.04 amd64 AMI for this Region. Resolve and review it before apply; avoiding a moving 'latest' lookup makes rebuilds auditable."

  validation {
    condition     = can(regex("^ami-[0-9a-f]+$", var.ubuntu_ami_id))
    error_message = "ubuntu_ami_id must look like ami-0123456789abcdef0."
  }
}

variable "edge_instance_type" {
  type        = string
  description = "Small always-on WireGuard/NAT edge."
  default     = "t3.micro"

  validation {
    condition     = can(regex("^t3a?\\.", var.edge_instance_type))
    error_message = "edge_instance_type must be an amd64 t3/t3a type so standard CPU credits are supported."
  }
}

variable "lab_instance_type" {
  type        = string
  description = "Per-team disposable lab host. Increase temporarily if image builds exhaust memory."
  default     = "t3.small"

  validation {
    condition     = can(regex("^t3a?\\.", var.lab_instance_type))
    error_message = "lab_instance_type must be an amd64 t3/t3a type so standard CPU credits are supported."
  }
}

variable "root_volume_size_gib" {
  type        = number
  description = "Encrypted gp3 root volume size for each instance."
  default     = 24

  validation {
    condition     = var.root_volume_size_gib >= 16 && var.root_volume_size_gib <= 100
    error_message = "root_volume_size_gib must be between 16 and 100 GiB."
  }
}

variable "ebs_kms_key_id" {
  type        = string
  description = "Optional customer-managed KMS key ARN/ID. Empty uses the AWS-managed EBS key."
  default     = ""
}

variable "repository_url" {
  type        = string
  description = "Public HTTPS Git repository containing this deployment directory."
  default     = "https://github.com/nutthakorn7/software-security.git"

  validation {
    condition     = can(regex("^https://github\\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\\.git$", var.repository_url))
    error_message = "repository_url must be a public GitHub HTTPS .git URL; credentials in URLs are forbidden."
  }
}

variable "repository_ref" {
  type        = string
  description = "Full 40-character commit SHA containing deploy/internal-labs. Branches and tags are rejected because they can move."

  validation {
    condition     = can(regex("^[0-9a-f]{40}$", var.repository_ref))
    error_message = "repository_ref must be a full lowercase 40-character Git commit SHA."
  }
}

variable "internal_domain" {
  type        = string
  description = "Private DNS suffix served by dnsmasq over WireGuard."
  default     = "labs.test"

  validation {
    condition     = can(regex("^[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?\\.test$", var.internal_domain))
    error_message = "internal_domain must be a lowercase name beneath the reserved .test suffix."
  }
}

variable "team_1_id" {
  type        = string
  description = "Opaque project marker for team one; do not use a name or student ID."
  default     = "team-one-demo"

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]{2,31}$", var.team_1_id))
    error_message = "team_1_id must be a 3-32 character opaque lowercase alias."
  }
}

variable "team_2_id" {
  type        = string
  description = "Opaque project marker for team two; do not use a name or student ID."
  default     = "team-two-demo"

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]{2,31}$", var.team_2_id))
    error_message = "team_2_id must be a 3-32 character opaque lowercase alias."
  }
}

variable "extra_tags" {
  type        = map(string)
  description = "Additional non-sensitive AWS tags. Never put roster data or keys in tags."
  default     = {}

  validation {
    condition = length(setintersection(
      toset(keys(var.extra_tags)),
      toset(["Name", "Role", "Team", "Project", "ManagedBy", "Purpose"]),
    )) == 0
    error_message = "extra_tags cannot override reserved identity/security tags: Name, Role, Team, Project, ManagedBy, or Purpose."
  }
}
