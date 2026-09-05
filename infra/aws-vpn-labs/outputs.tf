output "wireguard_public_endpoint" {
  description = "Public WireGuard endpoint. This is the only intended public listener."
  value       = "${aws_eip.wireguard_edge.public_ip}:${var.wireguard_port}"
}

output "wireguard_dns" {
  description = "WireGuard-only DNS server for generated peer configurations."
  value       = local.wireguard_server_ip
}

output "peer_allowed_ips" {
  description = "Split-tunnel routes for generated peer configurations."
  value       = "${var.vpc_cidr}, ${var.wireguard_cidr}"
}

output "wireguard_server_public_key_command" {
  description = "Run after cloud-init completes to read the non-secret server public key without enabling public SSH."
  value       = "aws ec2 get-console-output --region ${var.aws_region} --instance-id ${aws_instance.wireguard_edge.id} --latest --output text | grep -o 'WIREGUARD_SERVER_PUBLIC_KEY=[A-Za-z0-9+/=]*' | tail -1"
}

output "instructor_client_template" {
  description = "Non-secret fields for the instructor client. Generate and insert the private key only on the instructor device."
  value       = <<-EOT
    [Interface]
    PrivateKey = <GENERATE-ONLY-ON-INSTRUCTOR-DEVICE>
    Address = ${var.instructor_wireguard_cidr}
    DNS = ${local.wireguard_server_ip}

    [Peer]
    PublicKey = <READ-WITH-wireguard_server_public_key_command>
    Endpoint = ${aws_eip.wireguard_edge.public_ip}:${var.wireguard_port}
    AllowedIPs = ${var.vpc_cidr}, ${var.wireguard_cidr}
    PersistentKeepalive = 25
  EOT
}

output "team_lab_instances" {
  description = "Private lab host identities for instructor operations over WireGuard."
  value = {
    for name, instance in aws_instance.team_lab : name => {
      instance_id = instance.id
      private_ip  = instance.private_ip
      ssh         = "ssh ubuntu@${instance.private_ip}"
    }
  }
}

output "team_urls" {
  description = "Per-team private HTTPS entry points; dnsmasq resolves these only through WireGuard."
  value = {
    for name, team in local.teams : name => {
      learning = "https://learn.${team.dns_zone}:8443"
      week01   = "https://w1.${team.dns_zone}:8443/notes"
      week02   = "https://learn.${team.dns_zone}:8443/sim/fuzz-verdict"
      week03   = "https://learn.${team.dns_zone}:8443/sim/aes-modes"
      week04   = "https://w4.${team.dns_zone}:8443"
      week05   = "https://w5.${team.dns_zone}:8443"
      week06   = "https://w6.${team.dns_zone}:8443"
      project  = "https://project.${team.dns_zone}:8443"
    }
  }
}

output "reserved_peer_slots" {
  description = "Assign exactly one fixed /32 per device; never reuse a slot across people or teams."
  value = {
    team1 = sort(tolist(var.team_1_peer_cidrs))
    team2 = sort(tolist(var.team_2_peer_cidrs))
  }
}

output "lab_bootstrap_status_commands" {
  description = "Use AWS console output or instructor-only private SSH to diagnose bootstrap."
  value = {
    for name, instance in aws_instance.team_lab : name => "aws ec2 get-console-output --region ${var.aws_region} --instance-id ${instance.id} --latest --output text | tail -80"
  }
}
