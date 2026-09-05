check "peer_slots_are_disjoint" {
  assert {
    condition = (
      length(setintersection(var.team_1_peer_cidrs, var.team_2_peer_cidrs)) == 0 &&
      !contains(var.team_1_peer_cidrs, var.instructor_wireguard_cidr) &&
      !contains(var.team_2_peer_cidrs, var.instructor_wireguard_cidr) &&
      !contains(local.team_1_peer_ips, local.wireguard_server_ip) &&
      !contains(local.team_2_peer_ips, local.wireguard_server_ip) &&
      split("/", var.wireguard_server_address)[0] != local.instructor_wireguard_ip
    )
    error_message = "Instructor, server, team-one, and team-two WireGuard identities must be distinct."
  }
}

check "peer_slots_belong_to_wireguard_network" {
  assert {
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
    error_message = "All WireGuard server, instructor, and team addresses must belong to wireguard_cidr."
  }
}

check "wireguard_interface_prefix_matches_network" {
  assert {
    condition     = split("/", var.wireguard_server_address)[1] == split("/", var.wireguard_cidr)[1]
    error_message = "wireguard_server_address must use the same prefix length as wireguard_cidr."
  }
}

check "subnets_belong_to_vpc" {
  assert {
    condition = alltrue([
      local.cidr_ranges.vpc.start <= local.cidr_ranges.edge.start && local.cidr_ranges.vpc.end >= local.cidr_ranges.edge.end,
      local.cidr_ranges.vpc.start <= local.cidr_ranges.team1.start && local.cidr_ranges.vpc.end >= local.cidr_ranges.team1.end,
      local.cidr_ranges.vpc.start <= local.cidr_ranges.team2.start && local.cidr_ranges.vpc.end >= local.cidr_ranges.team2.end,
    ])
    error_message = "Every subnet must be contained by vpc_cidr."
  }
}

check "dedicated_networks_do_not_overlap" {
  assert {
    condition = (
      (local.cidr_ranges.edge.end < local.cidr_ranges.team1.start || local.cidr_ranges.team1.end < local.cidr_ranges.edge.start) &&
      (local.cidr_ranges.edge.end < local.cidr_ranges.team2.start || local.cidr_ranges.team2.end < local.cidr_ranges.edge.start) &&
      (local.cidr_ranges.team1.end < local.cidr_ranges.team2.start || local.cidr_ranges.team2.end < local.cidr_ranges.team1.start)
    )
    error_message = "The edge, team-one, and team-two subnets must not overlap at any prefix length."
  }
}

check "routing_domains_do_not_overlap" {
  assert {
    condition = (
      (local.cidr_ranges.vpc.end < local.cidr_ranges.wireguard.start || local.cidr_ranges.wireguard.end < local.cidr_ranges.vpc.start) &&
      (local.cidr_ranges.vpc.end < local.cidr_ranges.docker.start || local.cidr_ranges.docker.end < local.cidr_ranges.vpc.start) &&
      (local.cidr_ranges.wireguard.end < local.cidr_ranges.docker.start || local.cidr_ranges.docker.end < local.cidr_ranges.wireguard.start)
    )
    error_message = "VPC, WireGuard, and the fixed 172.30.0.0/16 Docker address space must not overlap."
  }
}

check "team_ids_are_distinct" {
  assert {
    condition     = var.team_1_id != var.team_2_id
    error_message = "team_1_id and team_2_id must be different opaque aliases."
  }
}
