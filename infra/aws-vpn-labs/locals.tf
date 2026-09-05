locals {
  availability_zone = var.availability_zone != "" ? var.availability_zone : data.aws_availability_zones.available.names[0]

  team_1_host_ip = cidrhost(var.team_1_subnet_cidr, 10)
  team_2_host_ip = cidrhost(var.team_2_subnet_cidr, 10)

  instructor_wireguard_ip = split("/", var.instructor_wireguard_cidr)[0]
  wireguard_server_ip     = split("/", var.wireguard_server_address)[0]
  team_1_peer_ips         = [for value in sort(tolist(var.team_1_peer_cidrs)) : split("/", value)[0]]
  team_2_peer_ips         = [for value in sort(tolist(var.team_2_peer_cidrs)) : split("/", value)[0]]

  # Terraform has no built-in CIDR containment predicate. Convert reviewed
  # IPv4 CIDRs to inclusive integer ranges so containment and overlap guards
  # remain correct even when callers choose unequal prefix lengths.
  cidr_inputs = merge(
    {
      vpc        = var.vpc_cidr
      edge       = var.edge_subnet_cidr
      team1      = var.team_1_subnet_cidr
      team2      = var.team_2_subnet_cidr
      wireguard  = var.wireguard_cidr
      docker     = "172.30.0.0/16"
      instructor = var.instructor_wireguard_cidr
      server     = "${local.wireguard_server_ip}/32"
    },
    { for value in var.team_1_peer_cidrs : "team1-peer:${value}" => value },
    { for value in var.team_2_peer_cidrs : "team2-peer:${value}" => value },
  )

  cidr_parts = {
    for name, cidr in local.cidr_inputs : name => {
      address = sum([
        for index in range(4) :
        try(tonumber(split(".", split("/", cidr)[0])[index]), 0) * pow(256, 3 - index)
      ])
      prefix = try(tonumber(split("/", cidr)[1]), 32)
    }
  }

  cidr_ranges = {
    for name, parts in local.cidr_parts : name => {
      start = floor(parts.address / pow(2, 32 - parts.prefix)) * pow(2, 32 - parts.prefix)
      end   = floor(parts.address / pow(2, 32 - parts.prefix)) * pow(2, 32 - parts.prefix) + pow(2, 32 - parts.prefix) - 1
    }
  }

  teams = {
    team1 = {
      id             = var.team_1_id
      profile        = "team1"
      private_ip     = local.team_1_host_ip
      subnet_cidr    = var.team_1_subnet_cidr
      subnet_id      = aws_subnet.team_1.id
      security_group = aws_security_group.team_1_lab.id
      dns_zone       = "team1.${var.internal_domain}"
    }
    team2 = {
      id             = var.team_2_id
      profile        = "team2"
      private_ip     = local.team_2_host_ip
      subnet_cidr    = var.team_2_subnet_cidr
      subnet_id      = aws_subnet.team_2.id
      security_group = aws_security_group.team_2_lab.id
      dns_zone       = "team2.${var.internal_domain}"
    }
  }
}
