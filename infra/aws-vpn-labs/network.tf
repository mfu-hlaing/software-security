resource "aws_vpc" "labs" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = { Name = "${var.project_name}-vpc" }

  # These are hard failures (unlike advisory check blocks) because overlapping
  # routing or identity ranges can collapse the team security boundary.
  lifecycle {
    precondition {
      condition = alltrue([
        local.cidr_ranges.vpc.start <= local.cidr_ranges.edge.start && local.cidr_ranges.vpc.end >= local.cidr_ranges.edge.end,
        local.cidr_ranges.vpc.start <= local.cidr_ranges.team1.start && local.cidr_ranges.vpc.end >= local.cidr_ranges.team1.end,
        local.cidr_ranges.vpc.start <= local.cidr_ranges.team2.start && local.cidr_ranges.vpc.end >= local.cidr_ranges.team2.end,
      ])
      error_message = "Every edge/team subnet must be fully contained by vpc_cidr."
    }

    precondition {
      condition = (
        (local.cidr_ranges.edge.end < local.cidr_ranges.team1.start || local.cidr_ranges.team1.end < local.cidr_ranges.edge.start) &&
        (local.cidr_ranges.edge.end < local.cidr_ranges.team2.start || local.cidr_ranges.team2.end < local.cidr_ranges.edge.start) &&
        (local.cidr_ranges.team1.end < local.cidr_ranges.team2.start || local.cidr_ranges.team2.end < local.cidr_ranges.team1.start)
      )
      error_message = "Edge and team subnets must be pairwise non-overlapping."
    }

    precondition {
      condition = (
        (local.cidr_ranges.vpc.end < local.cidr_ranges.wireguard.start || local.cidr_ranges.wireguard.end < local.cidr_ranges.vpc.start) &&
        (local.cidr_ranges.vpc.end < local.cidr_ranges.docker.start || local.cidr_ranges.docker.end < local.cidr_ranges.vpc.start) &&
        (local.cidr_ranges.wireguard.end < local.cidr_ranges.docker.start || local.cidr_ranges.docker.end < local.cidr_ranges.wireguard.start)
      )
      error_message = "VPC, WireGuard, and fixed Docker address spaces must not overlap."
    }

    precondition {
      condition = (
        length(setintersection(var.team_1_peer_cidrs, var.team_2_peer_cidrs)) == 0 &&
        !contains(var.team_1_peer_cidrs, var.instructor_wireguard_cidr) &&
        !contains(var.team_2_peer_cidrs, var.instructor_wireguard_cidr) &&
        !contains(local.team_1_peer_ips, local.wireguard_server_ip) &&
        !contains(local.team_2_peer_ips, local.wireguard_server_ip) &&
        local.wireguard_server_ip != local.instructor_wireguard_ip
      )
      error_message = "All instructor, server, team-one, and team-two WireGuard identities must be distinct."
    }

    precondition {
      condition = alltrue(concat(
        [for value in var.team_1_peer_cidrs : (
          local.cidr_ranges.wireguard.start <= local.cidr_ranges["team1-peer:${value}"].start &&
          local.cidr_ranges.wireguard.end >= local.cidr_ranges["team1-peer:${value}"].end
        )],
        [for value in var.team_2_peer_cidrs : (
          local.cidr_ranges.wireguard.start <= local.cidr_ranges["team2-peer:${value}"].start &&
          local.cidr_ranges.wireguard.end >= local.cidr_ranges["team2-peer:${value}"].end
        )],
        [
          local.cidr_ranges.wireguard.start <= local.cidr_ranges.instructor.start &&
          local.cidr_ranges.wireguard.end >= local.cidr_ranges.instructor.end,
          local.cidr_ranges.wireguard.start <= local.cidr_ranges.server.start &&
          local.cidr_ranges.wireguard.end >= local.cidr_ranges.server.end,
        ],
      ))
      error_message = "Every WireGuard server/instructor/team identity must be inside wireguard_cidr."
    }

    precondition {
      condition     = split("/", var.wireguard_server_address)[1] == split("/", var.wireguard_cidr)[1]
      error_message = "wireguard_server_address must use the same prefix length as wireguard_cidr."
    }
  }
}

resource "aws_internet_gateway" "labs" {
  vpc_id = aws_vpc.labs.id
  tags   = { Name = "${var.project_name}-igw" }
}

resource "aws_subnet" "edge" {
  vpc_id            = aws_vpc.labs.id
  availability_zone = local.availability_zone
  cidr_block        = var.edge_subnet_cidr
  # Public addressing is an explicit property of the single edge ENI below;
  # do not make every future instance in this subnet public by default.
  map_public_ip_on_launch = false
  tags                    = { Name = "${var.project_name}-edge" }
}

resource "aws_subnet" "team_1" {
  vpc_id                  = aws_vpc.labs.id
  availability_zone       = local.availability_zone
  cidr_block              = var.team_1_subnet_cidr
  map_public_ip_on_launch = false
  tags                    = { Name = "${var.project_name}-team1-private", Team = "team1" }
}

resource "aws_subnet" "team_2" {
  vpc_id                  = aws_vpc.labs.id
  availability_zone       = local.availability_zone
  cidr_block              = var.team_2_subnet_cidr
  map_public_ip_on_launch = false
  tags                    = { Name = "${var.project_name}-team2-private", Team = "team2" }
}

resource "aws_route_table" "edge" {
  vpc_id = aws_vpc.labs.id
  tags   = { Name = "${var.project_name}-edge" }
}

resource "aws_route" "edge_internet" {
  route_table_id         = aws_route_table.edge.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.labs.id
}

resource "aws_route_table_association" "edge" {
  subnet_id      = aws_subnet.edge.id
  route_table_id = aws_route_table.edge.id
}

resource "aws_route_table" "team_1" {
  vpc_id = aws_vpc.labs.id
  tags   = { Name = "${var.project_name}-team1" }
}

resource "aws_route_table" "team_2" {
  vpc_id = aws_vpc.labs.id
  tags   = { Name = "${var.project_name}-team2" }
}

# The edge is a deliberately tiny NAT instance for host bootstrap/update traffic,
# avoiding a permanently billed NAT Gateway. Docker's internal networks prevent
# the vulnerable workloads from using this host route.
resource "aws_route" "team_1_internet" {
  route_table_id         = aws_route_table.team_1.id
  destination_cidr_block = "0.0.0.0/0"
  network_interface_id   = aws_instance.wireguard_edge.primary_network_interface_id
}

resource "aws_route" "team_2_internet" {
  route_table_id         = aws_route_table.team_2.id
  destination_cidr_block = "0.0.0.0/0"
  network_interface_id   = aws_instance.wireguard_edge.primary_network_interface_id
}

# Explicit return routes preserve each peer's 10.66.0.x source identity. Do not
# masquerade VPN-to-VPC traffic: the /32 is what team security groups authorize.
resource "aws_route" "team_1_vpn_return" {
  route_table_id         = aws_route_table.team_1.id
  destination_cidr_block = var.wireguard_cidr
  network_interface_id   = aws_instance.wireguard_edge.primary_network_interface_id
}

resource "aws_route" "team_2_vpn_return" {
  route_table_id         = aws_route_table.team_2.id
  destination_cidr_block = var.wireguard_cidr
  network_interface_id   = aws_instance.wireguard_edge.primary_network_interface_id
}

resource "aws_route_table_association" "team_1" {
  subnet_id      = aws_subnet.team_1.id
  route_table_id = aws_route_table.team_1.id
}

resource "aws_route_table_association" "team_2" {
  subnet_id      = aws_subnet.team_2.id
  route_table_id = aws_route_table.team_2.id
}

resource "aws_security_group" "wireguard_edge" {
  name        = "${var.project_name}-wireguard-edge"
  description = "Only public ingress in the pilot: WireGuard UDP"
  vpc_id      = aws_vpc.labs.id

  tags = { Name = "${var.project_name}-wireguard-edge" }
}

resource "aws_vpc_security_group_ingress_rule" "wireguard_public" {
  for_each = var.wireguard_source_cidrs

  security_group_id = aws_security_group.wireguard_edge.id
  description       = "WireGuard tunnel initiation"
  ip_protocol       = "udp"
  from_port         = var.wireguard_port
  to_port           = var.wireguard_port
  cidr_ipv4         = each.value
}

# A NAT instance must accept the private hosts' forwarded bootstrap traffic.
# No public source gets this rule, and the edge host firewall independently
# defaults INPUT/FORWARD to drop.
resource "aws_vpc_security_group_ingress_rule" "edge_from_team_1" {
  security_group_id = aws_security_group.wireguard_edge.id
  description       = "Forward team-one host bootstrap traffic"
  ip_protocol       = "-1"
  cidr_ipv4         = var.team_1_subnet_cidr
}

resource "aws_vpc_security_group_ingress_rule" "edge_from_team_2" {
  security_group_id = aws_security_group.wireguard_edge.id
  description       = "Forward team-two host bootstrap traffic"
  ip_protocol       = "-1"
  cidr_ipv4         = var.team_2_subnet_cidr
}

resource "aws_vpc_security_group_egress_rule" "edge_all" {
  security_group_id = aws_security_group.wireguard_edge.id
  description       = "Tunnel forwarding, package updates, and NAT return traffic"
  ip_protocol       = "-1"
  cidr_ipv4         = "0.0.0.0/0"
}

resource "aws_security_group" "team_1_lab" {
  name        = "${var.project_name}-team1-lab"
  description = "Team-one HTTPS plus instructor-only private SSH"
  vpc_id      = aws_vpc.labs.id
  tags        = { Name = "${var.project_name}-team1-lab", Team = "team1" }
}

resource "aws_security_group" "team_2_lab" {
  name        = "${var.project_name}-team2-lab"
  description = "Team-two HTTPS plus instructor-only private SSH"
  vpc_id      = aws_vpc.labs.id
  tags        = { Name = "${var.project_name}-team2-lab", Team = "team2" }
}

resource "aws_vpc_security_group_ingress_rule" "team_1_https" {
  for_each = setunion(var.team_1_peer_cidrs, toset([var.instructor_wireguard_cidr]))

  security_group_id = aws_security_group.team_1_lab.id
  description       = "HTTPS from authorized team-one tunnel identity"
  ip_protocol       = "tcp"
  from_port         = 8443
  to_port           = 8443
  cidr_ipv4         = each.value
}

resource "aws_vpc_security_group_ingress_rule" "team_2_https" {
  for_each = setunion(var.team_2_peer_cidrs, toset([var.instructor_wireguard_cidr]))

  security_group_id = aws_security_group.team_2_lab.id
  description       = "HTTPS from authorized team-two tunnel identity"
  ip_protocol       = "tcp"
  from_port         = 8443
  to_port           = 8443
  cidr_ipv4         = each.value
}

resource "aws_vpc_security_group_ingress_rule" "team_1_instructor_ssh" {
  security_group_id = aws_security_group.team_1_lab.id
  description       = "Private SSH from instructor tunnel only"
  ip_protocol       = "tcp"
  from_port         = 22
  to_port           = 22
  cidr_ipv4         = var.instructor_wireguard_cidr
}

resource "aws_vpc_security_group_ingress_rule" "team_2_instructor_ssh" {
  security_group_id = aws_security_group.team_2_lab.id
  description       = "Private SSH from instructor tunnel only"
  ip_protocol       = "tcp"
  from_port         = 22
  to_port           = 22
  cidr_ipv4         = var.instructor_wireguard_cidr
}

# Host egress is for apt/Git/image bootstrap. The vulnerable containers have
# internal-only Docker networks and cannot use it. HTTP remains for Ubuntu
# mirrors; remove it after moving to a pre-baked AMI.
resource "aws_vpc_security_group_egress_rule" "team_1_web" {
  for_each = toset(["80", "443"])

  security_group_id = aws_security_group.team_1_lab.id
  description       = "Host package and image bootstrap"
  ip_protocol       = "tcp"
  from_port         = tonumber(each.value)
  to_port           = tonumber(each.value)
  cidr_ipv4         = "0.0.0.0/0"
}

resource "aws_vpc_security_group_egress_rule" "team_2_web" {
  for_each = toset(["80", "443"])

  security_group_id = aws_security_group.team_2_lab.id
  description       = "Host package and image bootstrap"
  ip_protocol       = "tcp"
  from_port         = tonumber(each.value)
  to_port           = tonumber(each.value)
  cidr_ipv4         = "0.0.0.0/0"
}

resource "aws_vpc_security_group_egress_rule" "team_1_dns_udp" {
  security_group_id = aws_security_group.team_1_lab.id
  description       = "VPC DNS"
  ip_protocol       = "udp"
  from_port         = 53
  to_port           = 53
  cidr_ipv4         = var.vpc_cidr
}

resource "aws_vpc_security_group_egress_rule" "team_1_dns_tcp" {
  security_group_id = aws_security_group.team_1_lab.id
  description       = "VPC DNS fallback"
  ip_protocol       = "tcp"
  from_port         = 53
  to_port           = 53
  cidr_ipv4         = var.vpc_cidr
}

resource "aws_vpc_security_group_egress_rule" "team_2_dns_udp" {
  security_group_id = aws_security_group.team_2_lab.id
  description       = "VPC DNS"
  ip_protocol       = "udp"
  from_port         = 53
  to_port           = 53
  cidr_ipv4         = var.vpc_cidr
}

resource "aws_vpc_security_group_egress_rule" "team_2_dns_tcp" {
  security_group_id = aws_security_group.team_2_lab.id
  description       = "VPC DNS fallback"
  ip_protocol       = "tcp"
  from_port         = 53
  to_port           = 53
  cidr_ipv4         = var.vpc_cidr
}

resource "aws_vpc_security_group_egress_rule" "team_1_ntp" {
  security_group_id = aws_security_group.team_1_lab.id
  description       = "Host clock synchronization"
  ip_protocol       = "udp"
  from_port         = 123
  to_port           = 123
  cidr_ipv4         = "0.0.0.0/0"
}

resource "aws_vpc_security_group_egress_rule" "team_2_ntp" {
  security_group_id = aws_security_group.team_2_lab.id
  description       = "Host clock synchronization"
  ip_protocol       = "udp"
  from_port         = 123
  to_port           = 123
  cidr_ipv4         = "0.0.0.0/0"
}

# Keep rule ownership exclusive without mixing the legacy inline ingress/egress
# fields with the standalone VPC security-group rule resources. This removes the
# AWS-created default egress rule and makes any unmanaged console-added rule
# visible as drift on the next plan.
resource "aws_vpc_security_group_rules_exclusive" "wireguard_edge" {
  security_group_id = aws_security_group.wireguard_edge.id
  ingress_rule_ids = toset(concat(
    [for rule in aws_vpc_security_group_ingress_rule.wireguard_public : rule.id],
    [
      aws_vpc_security_group_ingress_rule.edge_from_team_1.id,
      aws_vpc_security_group_ingress_rule.edge_from_team_2.id,
    ],
  ))
  egress_rule_ids = toset([
    aws_vpc_security_group_egress_rule.edge_all.id,
  ])
}

resource "aws_vpc_security_group_rules_exclusive" "team_1_lab" {
  security_group_id = aws_security_group.team_1_lab.id
  ingress_rule_ids = toset(concat(
    [for rule in aws_vpc_security_group_ingress_rule.team_1_https : rule.id],
    [aws_vpc_security_group_ingress_rule.team_1_instructor_ssh.id],
  ))
  egress_rule_ids = toset(concat(
    [for rule in aws_vpc_security_group_egress_rule.team_1_web : rule.id],
    [
      aws_vpc_security_group_egress_rule.team_1_dns_udp.id,
      aws_vpc_security_group_egress_rule.team_1_dns_tcp.id,
      aws_vpc_security_group_egress_rule.team_1_ntp.id,
    ],
  ))
}

resource "aws_vpc_security_group_rules_exclusive" "team_2_lab" {
  security_group_id = aws_security_group.team_2_lab.id
  ingress_rule_ids = toset(concat(
    [for rule in aws_vpc_security_group_ingress_rule.team_2_https : rule.id],
    [aws_vpc_security_group_ingress_rule.team_2_instructor_ssh.id],
  ))
  egress_rule_ids = toset(concat(
    [for rule in aws_vpc_security_group_egress_rule.team_2_web : rule.id],
    [
      aws_vpc_security_group_egress_rule.team_2_dns_udp.id,
      aws_vpc_security_group_egress_rule.team_2_dns_tcp.id,
      aws_vpc_security_group_egress_rule.team_2_ntp.id,
    ],
  ))
}
