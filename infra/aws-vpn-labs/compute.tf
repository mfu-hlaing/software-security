resource "aws_key_pair" "instructor" {
  key_name   = "${var.project_name}-instructor"
  public_key = trimspace(var.instructor_ssh_public_key)

  tags = { Name = "${var.project_name}-instructor-public-only" }
}

resource "aws_instance" "wireguard_edge" {
  ami                         = var.ubuntu_ami_id
  instance_type               = var.edge_instance_type
  subnet_id                   = aws_subnet.edge.id
  private_ip                  = cidrhost(var.edge_subnet_cidr, 10)
  associate_public_ip_address = true
  source_dest_check           = false
  key_name                    = aws_key_pair.instructor.key_name
  vpc_security_group_ids      = [aws_security_group.wireguard_edge.id]

  user_data_replace_on_change = true
  user_data = templatefile("${path.module}/cloud-init/wireguard-edge.yaml.tftpl", {
    wireguard_port        = var.wireguard_port
    wireguard_server_cidr = var.wireguard_server_address
    wireguard_server_ip   = local.wireguard_server_ip
    instructor_public_key = var.instructor_wireguard_public_key
    instructor_cidr       = var.instructor_wireguard_cidr
    instructor_ip         = local.instructor_wireguard_ip
    team_1_peer_cidrs     = indent(6, join("\n", sort(tolist(var.team_1_peer_cidrs))))
    team_2_peer_cidrs     = indent(6, join("\n", sort(tolist(var.team_2_peer_cidrs))))
    team_1_peer_ips_nft   = join(", ", local.team_1_peer_ips)
    team_2_peer_ips_nft   = join(", ", local.team_2_peer_ips)
    team_1_host_ip        = local.team_1_host_ip
    team_2_host_ip        = local.team_2_host_ip
    team_1_subnet_cidr    = var.team_1_subnet_cidr
    team_2_subnet_cidr    = var.team_2_subnet_cidr
    internal_domain       = var.internal_domain
  })

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
    instance_metadata_tags      = "disabled"
  }

  credit_specification {
    cpu_credits = "standard"
  }

  root_block_device {
    encrypted             = true
    kms_key_id            = var.ebs_kms_key_id != "" ? var.ebs_kms_key_id : null
    volume_type           = "gp3"
    volume_size           = var.root_volume_size_gib
    delete_on_termination = true
  }

  tags = {
    Name = "${var.project_name}-wireguard-edge"
    Role = "wireguard-edge"
  }

  depends_on = [aws_route.edge_internet]
}

resource "aws_eip" "wireguard_edge" {
  domain   = "vpc"
  instance = aws_instance.wireguard_edge.id

  tags = { Name = "${var.project_name}-wireguard-edge" }

  depends_on = [aws_internet_gateway.labs]
}

# Cloud-init needs IMDS once to obtain user-data and a narrowly scoped role once
# to turn IMDS off on its own instance. The application stack is started only
# after that API call succeeds. The role has no data-service permissions.
resource "aws_iam_role" "lab_bootstrap" {
  name = "${var.project_name}-disable-own-imds"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "lab_bootstrap" {
  name = "disable-tagged-lab-imds"
  role = aws_iam_role.lab_bootstrap.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid    = "DisableMetadataOnTrainingLabNodes"
      Effect = "Allow"
      Action = ["ec2:ModifyInstanceMetadataOptions"]
      Resource = format(
        "arn:%s:ec2:%s:%s:instance/*",
        data.aws_partition.current.partition,
        var.aws_region,
        data.aws_caller_identity.current.account_id,
      )
      Condition = {
        StringEquals = {
          "aws:ResourceTag/Project" = var.project_name
          "aws:ResourceTag/Role"    = "team-lab"
          # ModifyInstanceMetadataOptions exposes the requested setting as
          # an EC2 attribute. Restrict the role to the fail-closed transition;
          # it cannot re-enable the endpoint or change another IMDS option.
          "ec2:Attribute/HttpEndpoint" = "disabled"
        }
        ArnLike = {
          # This context key exists only for credentials delivered to an EC2
          # instance, so the policy cannot be exercised by another role path.
          "ec2:SourceInstanceARN" = format(
            "arn:%s:ec2:%s:%s:instance/*",
            data.aws_partition.current.partition,
            var.aws_region,
            data.aws_caller_identity.current.account_id,
          )
        }
      }
    }]
  })
}

resource "aws_iam_instance_profile" "lab_bootstrap" {
  name = "${var.project_name}-lab-bootstrap"
  role = aws_iam_role.lab_bootstrap.name
}

resource "aws_instance" "team_lab" {
  for_each = local.teams

  ami                         = var.ubuntu_ami_id
  instance_type               = var.lab_instance_type
  subnet_id                   = each.value.subnet_id
  private_ip                  = each.value.private_ip
  associate_public_ip_address = false
  source_dest_check           = true
  key_name                    = aws_key_pair.instructor.key_name
  vpc_security_group_ids      = [each.value.security_group]
  iam_instance_profile        = aws_iam_instance_profile.lab_bootstrap.name

  user_data_replace_on_change = true
  user_data = templatefile("${path.module}/cloud-init/team-lab.yaml.tftpl", {
    aws_region     = var.aws_region
    vpc_cidr       = var.vpc_cidr
    repository_url = var.repository_url
    repository_ref = var.repository_ref
    team_profile   = each.value.profile
    team_id        = each.value.id
    team_1_id      = var.team_1_id
    team_2_id      = var.team_2_id
    learn_host     = "learn.${each.value.dns_zone}"
    week01_host    = "w1.${each.value.dns_zone}"
    week04_host    = "w4.${each.value.dns_zone}"
    week05_host    = "w5.${each.value.dns_zone}"
    week06_host    = "w6.${each.value.dns_zone}"
    team_1_host    = "project.team1.${var.internal_domain}"
    team_2_host    = "project.team2.${var.internal_domain}"
  })

  # IMDS must be available for cloud-init to receive user-data. It is IMDSv2-only
  # with hop-limit 1 during bootstrap; cloud-init then disables the endpoint via
  # the one-action role above before Docker starts. Ignoring this one field keeps
  # Terraform from trying to undo the deliberate post-bootstrap hardening.
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
    instance_metadata_tags      = "disabled"
  }

  credit_specification {
    cpu_credits = "standard"
  }

  root_block_device {
    encrypted             = true
    kms_key_id            = var.ebs_kms_key_id != "" ? var.ebs_kms_key_id : null
    volume_type           = "gp3"
    volume_size           = var.root_volume_size_gib
    delete_on_termination = true
  }

  tags = {
    Name = "${var.project_name}-${each.key}"
    Role = "team-lab"
    Team = each.key
  }

  lifecycle {
    ignore_changes = [metadata_options]

    precondition {
      condition     = contains([var.team_1_subnet_cidr, var.team_2_subnet_cidr], each.value.subnet_cidr)
      error_message = "Each team host must remain in its dedicated private subnet."
    }
  }

  depends_on = [
    aws_eip.wireguard_edge,
    aws_route.team_1_internet,
    aws_route.team_2_internet,
    aws_route.team_1_vpn_return,
    aws_route.team_2_vpn_return,
  ]
}
